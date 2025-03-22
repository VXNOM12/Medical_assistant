# src/data_retriever.py
"""
Advanced dataset retrieval system for medical chatbot.
Loads datasets from configuration and provides efficient retrieval of relevant information.
"""

import logging
import yaml
import os
import json
from pathlib import Path
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import time
import gc


class MedicalDataRetriever:
    """
    Advanced retrieval system for medical datasets.
    Loads medical QA pairs from configured datasets and provides
    efficient semantic search to find relevant information for user queries.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the data retriever.
        
        Args:
            config_path: Optional custom path to config file
        """
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Set project root
        self.project_root = Path(__file__).parent.parent
        
        # Load configuration
        self.config_path = config_path or str(self.project_root / "config" / "data_config.yaml")
        self.config = self._load_config()
        
        # Initialize storage for datasets
        self.datasets = {}
        self.qa_pairs = []
        self.cache_dir = self.project_root / "data" / "cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
        # Load datasets
        self._load_datasets()
        
        # Initialize vectorizer for retrieval
        self.vectorizer = TfidfVectorizer(
            max_features=10000,
            ngram_range=(1, 2),
            stop_words='english'
        )
        
        # Create vector representations
        self._create_vector_index()
        
        self.logger.info(f"Initialized MedicalDataRetriever with {len(self.qa_pairs)} QA pairs")
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            return config
        except Exception as e:
            self.logger.error(f"Error loading config: {e}")
            # Return minimal default config
            return {"datasets": [], "model_name": "google/flan-t5-large"}
    
    def _load_datasets(self):
        """Load all configured datasets that are marked as auto_loadable."""
        # Check if we have a cached version of processed QA pairs
        cache_file = self.cache_dir / "processed_qa_pairs.json"
        
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.qa_pairs = json.load(f)
                self.logger.info(f"Loaded {len(self.qa_pairs)} QA pairs from cache")
                return
            except Exception as e:
                self.logger.warning(f"Error loading cached QA pairs: {e}")
        
        # If no cache or error loading, process the datasets
        try:
            # Focus on auto-loadable datasets first
            auto_loadable = [d for d in self.config.get('datasets', []) 
                            if d.get('auto_loadable', False)]
            
            if not auto_loadable:
                self.logger.warning("No auto-loadable datasets found in config")
                self._create_fallback_content()
                return
                
            # Load each dataset
            for dataset_config in auto_loadable:
                try:
                    self._load_single_dataset(dataset_config)
                except Exception as e:
                    self.logger.error(f"Error loading dataset {dataset_config['name']}: {e}")
            
            # If no QA pairs were loaded, create fallback content
            if not self.qa_pairs:
                self._create_fallback_content()
            else:
                # Cache the processed QA pairs
                with open(cache_file, 'w') as f:
                    json.dump(self.qa_pairs, f)
                self.logger.info(f"Cached {len(self.qa_pairs)} QA pairs")
                
        except Exception as e:
            self.logger.error(f"Error loading datasets: {e}")
            self._create_fallback_content()
    
    def _load_single_dataset(self, dataset_config: Dict[str, Any]):
        """
        Load a single dataset based on its configuration.
        
        Args:
            dataset_config: Configuration dictionary for the dataset
        """
        try:
            from datasets import load_dataset
            
            name = dataset_config['name']
            config_name = dataset_config.get('config')
            split = dataset_config.get('split', 'train')
            num_samples = min(dataset_config.get('samples', 1000), 10000)  # Limit for efficiency
            
            self.logger.info(f"Loading dataset: {name} (config: {config_name}, samples: {num_samples})")
            
            # Load the dataset
            if config_name:
                dataset = load_dataset(name, config_name, split=split)
            else:
                dataset = load_dataset(name, split=split)
            
            # Sample the dataset
            if len(dataset) > num_samples:
                # Use a consistent seed for reproducibility
                indices = np.random.RandomState(42).choice(
                    len(dataset), num_samples, replace=False
                )
                dataset = dataset.select(indices)
            
            # Process the dataset into QA pairs
            qa_pairs = self._extract_qa_pairs(dataset, dataset_config)
            
            # Add to our collection
            self.qa_pairs.extend(qa_pairs)
            
            self.logger.info(f"Added {len(qa_pairs)} QA pairs from {name}")
            
            # Free memory
            del dataset
            gc.collect()
            
        except Exception as e:
            self.logger.error(f"Error loading dataset {dataset_config['name']}: {e}")
    
    def _extract_qa_pairs(self, dataset, config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract question-answer pairs from a dataset.
        
        Args:
            dataset: The loaded dataset
            config: Dataset configuration
            
        Returns:
            List of QA pairs
        """
        qa_pairs = []
        dataset_name = config['name']
        
        # Helper function to check if a field exists in a sample
        def has_field(sample, fields):
            """Check if sample has any of the specified fields."""
            if isinstance(fields, str):
                return fields in sample
            return any(field in sample for field in fields)
        
        # Process each sample in the dataset
        for i, sample in enumerate(dataset):
            try:
                # Convert sample to dict if it's not already
                if not isinstance(sample, dict):
                    sample = dict(sample)
                
                # Extract question and answer based on dataset structure
                question = None
                answer = None
                
                # Handle different dataset structures
                if dataset_name == "openlifescienceai/medmcqa":
                    # MedMCQA structure
                    if 'question' in sample and 'cop' in sample:
                        question = sample['question']
                        # Get the correct option text
                        options = [
                            sample.get('opa', ''), 
                            sample.get('opb', ''),
                            sample.get('opc', ''),
                            sample.get('opd', '')
                        ]
                        correct_idx = sample['cop'] - 1  # cop is 1-indexed
                        if 0 <= correct_idx < len(options):
                            answer = options[correct_idx]
                            if sample.get('exp'):  # Add explanation if available
                                answer += f" {sample['exp']}"
                
                elif dataset_name == "qiaojin/PubMedQA":
                    # PubMedQA structure
                    if 'question' in sample and 'long_answer' in sample:
                        question = sample['question']
                        answer = sample['long_answer']
                        if not answer and 'final_decision' in sample:
                            # Use decision if long answer not available
                            answer = sample['final_decision']
                            
                # Generic fallbacks for other datasets
                elif has_field(sample, ['question', 'query', 'prompt']):
                    # Find question field
                    for field in ['question', 'query', 'prompt']:
                        if field in sample:
                            question = sample[field]
                            break
                    
                    # Find answer field
                    for field in ['answer', 'response', 'output', 'target']:
                        if field in sample and sample[field]:
                            answer = sample[field]
                            break
                
                # Add valid QA pair
                if question and answer:
                    # Clean the texts
                    question = str(question).strip()
                    answer = str(answer).strip()
                    
                    # Skip very short or very long texts
                    if len(question) < 5 or len(answer) < 5:
                        continue
                    if len(question) > 1000 or len(answer) > 5000:
                        continue
                    
                    qa_pairs.append({
                        "question": question,
                        "answer": answer,
                        "source": dataset_name,
                        "metadata": {
                            "category": config.get('category', 'Uncategorized'),
                            "priority": config.get('priority', 0.5)
                        }
                    })
            
            except Exception as e:
                self.logger.warning(f"Error processing sample {i} from {dataset_name}: {e}")
                continue
        
        return qa_pairs
    
    def _create_fallback_content(self):
        """Create fallback QA pairs when datasets can't be loaded."""
        self.logger.info("Creating fallback content")
        
        # Common medical topics with basic QA pairs
        fallback_qa = [
            {
                "question": "What are common symptoms of seasonal allergies?",
                "answer": "Common symptoms of seasonal allergies include sneezing, runny or stuffy nose, watery and itchy eyes, itchy sinuses, throat, or ear canals, ear congestion, and postnasal drainage. These symptoms occur when your immune system overreacts to allergens like pollen, grass, or mold.",
                "source": "fallback_content",
                "metadata": {"category": "Common Conditions", "priority": 0.8}
            },
            {
                "question": "How can I reduce cholesterol naturally?",
                "answer": "To reduce cholesterol naturally: 1) Eat heart-healthy foods like oats, barley, fatty fish, nuts, and olive oil. 2) Reduce saturated fats and eliminate trans fats. 3) Exercise regularly (aim for 30 minutes daily). 4) Lose excess weight. 5) Quit smoking. 6) Limit alcohol consumption. 7) Add foods with plant sterols or stanols. Always consult a healthcare provider before making significant lifestyle changes.",
                "source": "fallback_content",
                "metadata": {"category": "Heart Health", "priority": 0.8}
            },
            {
                "question": "What is the recommended daily water intake?",
                "answer": "The National Academies of Sciences, Engineering, and Medicine recommends about 3.7 liters (125 ounces) of fluids daily for men and 2.7 liters (91 ounces) for women. This includes all beverages and water-rich foods. However, needs vary based on factors like activity level, climate, overall health, and pregnancy/breastfeeding status. A good general guideline is to drink enough so you're rarely thirsty and your urine is colorless or light yellow.",
                "source": "fallback_content",
                "metadata": {"category": "Nutrition", "priority": 0.7}
            },
            {
                "question": "What causes frequent headaches?",
                "answer": "Frequent headaches can be caused by various factors: 1) Tension and stress, 2) Dehydration, 3) Poor sleep habits, 4) Skipping meals, 5) Certain foods and beverages (like alcohol or caffeine), 6) Hormonal changes, 7) Medications and medication overuse, 8) Environmental factors (bright lights, noise, strong smells), 9) Underlying health conditions (sinusitis, hypertension, etc.), 10) Eye strain. If headaches are severe, persistent, or disruptive to daily life, consult a healthcare provider for proper evaluation.",
                "source": "fallback_content",
                "metadata": {"category": "Common Conditions", "priority": 0.7}
            },
            {
                "question": "What are normal blood pressure ranges?",
                "answer": "Normal blood pressure is typically less than 120/80 mm Hg (systolic/diastolic). Elevated blood pressure is 120-129 systolic and less than 80 diastolic. Hypertension Stage 1 is 130-139 systolic or 80-89 diastolic. Hypertension Stage 2 is 140+ systolic or 90+ diastolic. Hypertensive crisis (requiring immediate medical attention) is higher than 180 systolic and/or higher than 120 diastolic. Blood pressure readings should be interpreted by healthcare professionals considering individual health factors.",
                "source": "fallback_content",
                "metadata": {"category": "Cardiovascular Health", "priority": 0.9}
            },
            {
                "question": "What are the side effects of ibuprofen?",
                "answer": "Common side effects of ibuprofen include: stomach pain, heartburn, nausea, vomiting, gas, diarrhea, constipation, dizziness, headache, nervousness, and rash. Serious side effects (requiring immediate medical attention) include: difficulty breathing/swallowing, swelling (face, throat, arms, hands, feet), unusual weight gain, unexplained tiredness, nausea/vomiting that doesn't stop, stomach pain that doesn't go away, flu-like symptoms, yellowing of skin/eyes, changes in urination, vision/hearing changes, and serious skin reactions.",
                "source": "fallback_content",
                "metadata": {"category": "Medications", "priority": 0.8}
            },
            {
                "question": "What could be the cause of a persistent cough?",
                "answer": "A persistent cough (lasting more than 8 weeks) can be caused by: 1) Chronic postnasal drip from allergies or sinus infections, 2) Asthma, especially cough-variant asthma, 3) Gastroesophageal reflux disease (GERD), 4) Chronic bronchitis or smoking, 5) ACE inhibitor medications, 6) Lung infections like pneumonia or tuberculosis, 7) Chronic obstructive pulmonary disease (COPD), 8) Lung cancer (especially in smokers), 9) Heart failure with fluid accumulation in lungs, 10) Environmental irritants. Persistent coughs should be evaluated by a healthcare provider.",
                "source": "fallback_content",
                "metadata": {"category": "Respiratory Health", "priority": 0.8}
            },
            {
                "question": "How should I take antibiotics correctly?",
                "answer": "To take antibiotics correctly: 1) Follow your prescription exactly as written, 2) Complete the full course, even if you feel better before it's finished, 3) Take at regular intervals to maintain constant blood levels, 4) Some antibiotics should be taken with food, others on an empty stomach (follow directions), 5) Don't share antibiotics or save them for later use, 6) Inform your doctor of all other medications you're taking to prevent interactions, 7) Report severe side effects promptly, 8) Consider taking probiotics (separate from antibiotic doses) to maintain gut health, 9) Avoid alcohol with certain antibiotics.",
                "source": "fallback_content",
                "metadata": {"category": "Medications", "priority": 0.9}
            }
        ]
        
        self.qa_pairs = fallback_qa
        self.logger.info(f"Created {len(fallback_qa)} fallback QA pairs")
    
    def _create_vector_index(self):
        """Create vector representations for efficient retrieval."""
        if not self.qa_pairs:
            self.logger.warning("No QA pairs available for vectorization")
            self.question_vectors = None
            return
            
        try:
            # Extract questions for vectorization
            questions = [item["question"] for item in self.qa_pairs]
            
            # Fit vectorizer and transform questions to vectors
            self.question_vectors = self.vectorizer.fit_transform(questions)
            
            self.logger.info(f"Created vector index with {len(questions)} questions")
            
        except Exception as e:
            self.logger.error(f"Error creating vector index: {e}")
            self.question_vectors = None
    
    def get_relevant_info(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant QA pairs for a given query.
        
        Args:
            query: User's query string
            top_k: Number of results to return
            
        Returns:
            List of relevant QA pairs
        """
        if not self.qa_pairs or self.question_vectors is None:
            self.logger.warning("No indexed data available for retrieval")
            return []
            
        try:
            # Vectorize the query
            query_vector = self.vectorizer.transform([query])
            
            # Calculate similarity with all questions
            similarities = cosine_similarity(query_vector, self.question_vectors).flatten()
            
            # Get top_k indices
            top_indices = similarities.argsort()[-top_k:][::-1]
            
            # Filter by minimum similarity threshold
            relevant_pairs = []
            for idx in top_indices:
                if similarities[idx] > 0.25:  # Minimum relevance threshold
                    qa_pair = self.qa_pairs[idx].copy()
                    qa_pair['relevance_score'] = float(similarities[idx])
                    relevant_pairs.append(qa_pair)
            
            return relevant_pairs
            
        except Exception as e:
            self.logger.error(f"Error retrieving relevant info: {e}")
            return []
    
    def format_for_context(self, qa_pairs: List[Dict[str, Any]]) -> str:
        """
        Format QA pairs as context for the language model.
        
        Args:
            qa_pairs: List of relevant QA pairs
            
        Returns:
            Formatted context string
        """
        if not qa_pairs:
            return ""
            
        context = "Relevant medical information:\n\n"
        
        for i, pair in enumerate(qa_pairs):
            context += f"Information {i+1}:\n"
            context += f"Question: {pair['question']}\n"
            context += f"Answer: {pair['answer']}\n"
            if 'source' in pair:
                context += f"Source: {pair['source']}\n"
            context += "\n"
            
        return context.strip()
    
    def get_enhanced_query(self, query: str) -> str:
        """
        Create enhanced query with relevant context.
        
        Args:
            query: Original user query
            
        Returns:
            Enhanced query with context information
        """
        # Get relevant information
        relevant_info = self.get_relevant_info(query)
        
        if not relevant_info:
            return query
            
        # Format context
        context = self.format_for_context(relevant_info)
        
        # Combine context with original query
        enhanced_query = f"{context}\n\nBased on the information above and your medical knowledge, please answer this question:\n{query}"
        
        return enhanced_query

# For testing the module directly
if __name__ == "__main__":
    # Initialize the retriever
    retriever = MedicalDataRetriever()
    
    # Test queries
    test_queries = [
        "What are common symptoms of seasonal allergies?",
        "How can I reduce cholesterol naturally?",
        "What causes a persistent cough?",
        "How should I take antibiotics correctly?"
    ]
    
    # Test retrieval
    for query in test_queries:
        print(f"\nQuery: {query}")
        
        # Get relevant information
        relevant_info = retriever.get_relevant_info(query)
        
        print(f"Found {len(relevant_info)} relevant QA pairs:")
        for i, info in enumerate(relevant_info):
            print(f"\n{i+1}. Question: {info['question']}")
            print(f"   Relevance: {info['relevance_score']:.2f}")
            print(f"   Answer: {info['answer'][:100]}...")
            print(f"   Source: {info['source']}")
        
        # Get enhanced query
        enhanced_query = retriever.get_enhanced_query(query)
        print(f"\nEnhanced Query Preview (first 200 chars):\n{enhanced_query[:200]}...")