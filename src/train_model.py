import torch
import logging
import yaml
import json
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime
from transformers import (
    AutoModelForSeq2SeqGeneration,
    AutoTokenizer,
    Trainer,
    TrainingArguments,
    DataCollatorForSeq2Seq,
    EarlyStoppingCallback
)
from datasets import Dataset, DatasetDict
import numpy as np
from sklearn.metrics import accuracy_score, precision_recall_fscore_support
import wandb
import os
from tqdm import tqdm

class MedicalModelTrainer:
    """
    Handles training and fine-tuning of medical language models.
    Includes data preparation, training, evaluation, and model saving.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the model trainer.
        
        Args:
            config_path: Optional path to config file
        """
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Set project root and load config
        self.project_root = Path(__file__).parent.parent
        self.config = self._load_config(config_path)
        
        # Setup device
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.logger.info(f"Using device: {self.device}")
        
        # Initialize model and tokenizer
        self._initialize_model()
        
        # Setup wandb for experiment tracking
        if self.config['use_wandb']:
            self._setup_wandb()

    def _load_config(self, config_path: Optional[str]) -> Dict:
        """Load training configuration."""
        try:
            if config_path is None:
                config_path = self.project_root / "config" / "data_config.yaml"
                
            with open(config_path) as f:
                config = yaml.safe_load(f)
                
            self.logger.info("Successfully loaded training configuration")
            return config
            
        except Exception as e:
            self.logger.error(f"Error loading config: {str(e)}")
            raise

    def _initialize_model(self):
        """Initialize model and tokenizer."""
        try:
            model_name = self.config['model_name']
            self.logger.info(f"Initializing model: {model_name}")
            
            # Initialize tokenizer
            self.tokenizer = AutoTokenizer.from_pretrained(
                model_name,
                model_max_length=self.config['max_length']
            )
            
            # Initialize model
            self.model = AutoModelForSeq2SeqGeneration.from_pretrained(
                model_name
            ).to(self.device)
            
            self.logger.info("Successfully initialized model and tokenizer")
            
        except Exception as e:
            self.logger.error(f"Error initializing model: {str(e)}")
            raise

    def _setup_wandb(self):
        """Setup Weights & Biases for experiment tracking."""
        try:
            wandb.init(
                project="medical-chatbot",
                config=self.config,
                name=f"training-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
            )
        except Exception as e:
            self.logger.warning(f"Error setting up wandb: {str(e)}")
            self.config['use_wandb'] = False

    def prepare_dataset(self, dataset_dict: DatasetDict) -> DatasetDict:
        """
        Prepare dataset for training.
        
        Args:
            dataset_dict: Input dataset dictionary
            
        Returns:
            Processed dataset dictionary
        """
        def tokenize_function(examples):
            """Tokenize examples."""
            model_inputs = self.tokenizer(
                examples['input'],
                max_length=self.config['max_length'],
                padding='max_length',
                truncation=True
            )
            
            # Tokenize targets
            with self.tokenizer.as_target_tokenizer():
                labels = self.tokenizer(
                    examples['output'],
                    max_length=self.config['max_length'],
                    padding='max_length',
                    truncation=True
                )
                
            model_inputs['labels'] = labels['input_ids']
            return model_inputs

        # Process datasets
        tokenized_datasets = {}
        for split, dataset in dataset_dict.items():
            self.logger.info(f"Processing {split} split")
            tokenized_datasets[split] = dataset.map(
                tokenize_function,
                batched=True,
                remove_columns=dataset.column_names
            )
            
        return DatasetDict(tokenized_datasets)

    def compute_metrics(self, eval_pred) -> Dict[str, float]:
        """
        Compute evaluation metrics.
        
        Args:
            eval_pred: Evaluation predictions
            
        Returns:
            Dictionary of metric scores
        """
        predictions, labels = eval_pred
        
        # Decode predictions
        decoded_preds = self.tokenizer.batch_decode(
            predictions, skip_special_tokens=True
        )
        
        # Decode labels
        labels = np.where(labels != -100, labels, self.tokenizer.pad_token_id)
        decoded_labels = self.tokenizer.batch_decode(
            labels, skip_special_tokens=True
        )
        
        # Compute ROUGE scores
        rouge_scores = self.compute_rouge_scores(decoded_preds, decoded_labels)
        
        # Compute accuracy
        accuracy = accuracy_score(
            [l.split() for l in decoded_labels],
            [p.split() for p in decoded_preds],
            normalize=True
        )
        
        # Compute precision, recall, f1
        precision, recall, f1, _ = precision_recall_fscore_support(
            [l.split() for l in decoded_labels],
            [p.split() for p in decoded_preds],
            average='weighted'
        )
        
        metrics = {
            'accuracy': accuracy,
            'precision': precision,
            'recall': recall,
            'f1': f1,
            **rouge_scores
        }
        
        return metrics

    def compute_rouge_scores(self, predictions: list, references: list) -> Dict[str, float]:
        """
        Compute ROUGE scores for predictions.
        
        Args:
            predictions: List of predicted texts
            references: List of reference texts
            
        Returns:
            Dictionary of ROUGE scores
        """
        try:
            from rouge_score import rouge_scorer
            
            scorer = rouge_scorer.RougeScorer(['rouge1', 'rouge2', 'rougeL'])
            scores = {
                'rouge1': 0.0,
                'rouge2': 0.0,
                'rougeL': 0.0
            }
            
            for pred, ref in zip(predictions, references):
                score = scorer.score(ref, pred)
                scores['rouge1'] += score['rouge1'].fmeasure
                scores['rouge2'] += score['rouge2'].fmeasure
                scores['rougeL'] += score['rougeL'].fmeasure
                
            # Average scores
            n_samples = len(predictions)
            for key in scores:
                scores[key] /= n_samples
                
            return scores
            
        except ImportError:
            self.logger.warning("rouge_score not installed. Skipping ROUGE computation.")
            return {}

    def train(self, dataset_dict: DatasetDict) -> Tuple[Dict[str, float], str]:
        """
        Train the model.
        
        Args:
            dataset_dict: Dataset dictionary with train/validation splits
            
        Returns:
            Tuple of (evaluation metrics, model save path)
        """
        try:
            # Prepare datasets
            processed_datasets = self.prepare_dataset(dataset_dict)
            
            # Setup training arguments
            training_args = TrainingArguments(
                output_dir="medical_chatbot_model",
                num_train_epochs=self.config['training_params']['num_epochs'],
                per_device_train_batch_size=self.config['training_params']['batch_size'],
                per_device_eval_batch_size=self.config['training_params']['batch_size'],
                warmup_steps=self.config['training_params']['warmup_steps'],
                weight_decay=self.config['training_params']['weight_decay'],
                logging_dir="logs",
                logging_steps=100,
                eval_steps=500,
                save_steps=1000,
                evaluation_strategy="steps",
                load_best_model_at_end=True,
                metric_for_best_model="f1",
                greater_is_better=True
            )
            
            # Setup data collator
            data_collator = DataCollatorForSeq2Seq(
                self.tokenizer,
                model=self.model,
                padding=True
            )
            
            # Initialize trainer
            trainer = Trainer(
                model=self.model,
                args=training_args,
                train_dataset=processed_datasets['train'],
                eval_dataset=processed_datasets['test'],
                data_collator=data_collator,
                tokenizer=self.tokenizer,
                compute_metrics=self.compute_metrics,
                callbacks=[EarlyStoppingCallback(early_stopping_patience=3)]
            )
            
            # Train model
            self.logger.info("Starting training...")
            trainer.train()
            
            # Evaluate model
            metrics = trainer.evaluate()
            
            # Save model
            save_path = self._save_model(trainer)
            
            # Log to wandb if enabled
            if self.config['use_wandb']:
                wandb.log(metrics)
                
            return metrics, save_path
            
        except Exception as e:
            self.logger.error(f"Error during training: {str(e)}")
            raise

    def _save_model(self, trainer) -> str:
        """
        Save trained model and tokenizer.
        
        Args:
            trainer: Trained Trainer instance
            
        Returns:
            Path where model was saved
        """
        try:
            # Create save directory
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            save_dir = self.project_root / "models" / f"medical_model_{timestamp}"
            save_dir.mkdir(parents=True, exist_ok=True)
            
            # Save model
            trainer.save_model(save_dir)
            
            # Save tokenizer
            self.tokenizer.save_pretrained(save_dir)
            
            # Save config
            with open(save_dir / "config.json", 'w') as f:
                json.dump(self.config, f, indent=2)
                
            self.logger.info(f"Saved model to {save_dir}")
            return str(save_dir)
            
        except Exception as e:
            self.logger.error(f"Error saving model: {str(e)}")
            raise

    def evaluate_model(self, test_dataset: Dataset) -> Dict[str, float]:
        """
        Evaluate model on test dataset.
        
        Args:
            test_dataset: Test dataset
            
        Returns:
            Dictionary of evaluation metrics
        """
        try:
            # Prepare test dataset
            processed_dataset = self.prepare_dataset({'test': test_dataset})['test']
            
            # Setup data collator
            data_collator = DataCollatorForSeq2Seq(
                self.tokenizer,
                model=self.model,
                padding=True
            )
            
            # Setup trainer for evaluation
            trainer = Trainer(
                model=self.model,
                tokenizer=self.tokenizer,
                data_collator=data_collator,
                compute_metrics=self.compute_metrics
            )
            
            # Run evaluation
            metrics = trainer.evaluate(processed_dataset)
            
            # Log to wandb if enabled
            if self.config['use_wandb']:
                wandb.log({'test_metrics': metrics})
                
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error during evaluation: {str(e)}")
            raise

def main():
    """Main function to run training pipeline."""
    try:
        # Initialize trainer
        trainer = MedicalModelTrainer()
        
        # Load dataset
        from datasets import load_dataset
        dataset = load_dataset("bigbio/mediqa")
        
        # Train model
        metrics, save_path = trainer.train(dataset)
        
        print(f"Training completed. Model saved to: {save_path}")
        print("Metrics:", metrics)
        
    except Exception as e:
        logging.error(f"Training failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()