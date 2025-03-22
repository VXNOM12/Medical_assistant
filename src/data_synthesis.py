#!/usr/bin/env python3
"""
Synthetic Medical Q&A Generator
===============================
Generates synthetic training data from medical guidelines (CDC/NIH/WHO)
"""

import argparse
import json
import logging
from pathlib import Path
from datetime import datetime
from tqdm import tqdm
import sys
import codecs

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

class SyntheticDataGenerator:
    def __init__(self, guidelines_path: Path):
        self.guidelines_path = Path(guidelines_path)
        self.guidelines = self._load_guidelines()
        self.templates = self._initialize_templates()

    def _load_guidelines(self):
        """Load medical guidelines with proper encoding handling."""
        try:
            guidelines_file = self.guidelines_path / "medical_guidelines.json"
            if not guidelines_file.exists():
                raise FileNotFoundError(f"Guidelines file not found: {guidelines_file}")

            # Try different encodings
            encodings = ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']
            
            for encoding in encodings:
                try:
                    with codecs.open(guidelines_file, 'r', encoding=encoding) as f:
                        return json.load(f)
                except UnicodeDecodeError:
                    continue
                    
            raise UnicodeError(f"Could not decode {guidelines_file} with any supported encoding")
            
        except Exception as e:
            raise Exception(f"Error loading guidelines: {str(e)}")

    def _initialize_templates(self):
        """Initialize Q&A templates."""
        return {
            'questions': [
                "What are the symptoms of {condition}?",
                "How is {condition} treated?",
                "What causes {condition}?",
                "How can I prevent {condition}?"
            ],
            'answers': {
                'symptoms': "Common symptoms of {condition} include: {symptoms}",
                'treatment': "Treatment options for {condition} include: {treatments}",
                'causes': "Common causes of {condition} include: {causes}",
                'prevention': "To prevent {condition}, you should: {prevention}"
            }
        }

    def generate_qa_pairs(self, num_pairs: int) -> list:
        """Generate synthetic Q&A pairs."""
        qa_pairs = []
        conditions = self.guidelines.get('conditions', {})
        
        if not conditions:
            raise ValueError("No conditions found in guidelines")

        for _ in range(num_pairs):
            condition = list(conditions.keys())[_ % len(conditions)]
            condition_data = conditions[condition]
            
            # Generate question
            template = self.templates['questions'][_ % len(self.templates['questions'])]
            question = template.format(condition=condition)
            
            # Generate answer
            answer_type = self._get_answer_type(template)
            answer_template = self.templates['answers'][answer_type]
            answer_data = condition_data.get(answer_type + 's', ["Information not available"])
            answer = answer_template.format(
                condition=condition,
                **{answer_type + 's': ', '.join(answer_data)}
            )
            
            qa_pairs.append({
                'question': question,
                'answer': answer,
                'condition': condition,
                'type': answer_type
            })
            
        return qa_pairs

    def _get_answer_type(self, question: str) -> str:
        """Determine answer type from question."""
        if 'symptoms' in question.lower():
            return 'symptom'
        elif 'treated' in question.lower():
            return 'treatment'
        elif 'causes' in question.lower():
            return 'cause'
        elif 'prevent' in question.lower():
            return 'prevention'
        return 'general'

def main():
    # Configure argument parser
    parser = argparse.ArgumentParser(description="Generate synthetic medical Q&A pairs")
    parser.add_argument("--num-pairs", type=int, default=1000,
                      help="Number of Q&A pairs to generate (default: 1000)")
    parser.add_argument("--guidelines-dir", type=str, 
                      default="data/medical_knowledge",
                      help="Path to medical guidelines directory")
    parser.add_argument("--output-dir", type=str,
                      default="data/synthetic_data",
                      help="Output directory for generated data")
    parser.add_argument("--overwrite", action="store_true",
                      help="Overwrite existing files in output directory")
    
    args = parser.parse_args()
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logger = logging.getLogger(__name__)
    
    # Validate paths
    guidelines_path = Path(args.guidelines_dir)
    if not guidelines_path.exists():
        logger.error(f"Guidelines directory not found: {guidelines_path}")
        sys.exit(1)
        
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize generator
    logger.info("Initializing synthetic data generator...")
    try:
        generator = SyntheticDataGenerator(guidelines_path)
    except Exception as e:
        logger.error(f"Failed to initialize generator: {str(e)}")
        sys.exit(1)
    
    # Generate Q&A pairs
    logger.info(f"Generating {args.num_pairs} synthetic Q&A pairs...")
    try:
        synthetic_data = generator.generate_qa_pairs(args.num_pairs)
    except Exception as e:
        logger.error(f"Generation failed: {str(e)}")
        sys.exit(1)
        
    # Create output filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_path / f"synthetic_qa_{timestamp}.jsonl"
    
    # Save generated data with proper encoding
    logger.info(f"Saving output to {output_file}...")
    try:
        with codecs.open(output_file, 'w', encoding='utf-8') as f:
            for item in tqdm(synthetic_data, desc="Saving records"):
                f.write(json.dumps(item, ensure_ascii=False) + "\n")
    except IOError as e:
        logger.error(f"Failed to save output: {str(e)}")
        sys.exit(1)
        
    logger.info(f"Successfully generated {len(synthetic_data)} Q&A pairs")

if __name__ == "__main__":
    main()