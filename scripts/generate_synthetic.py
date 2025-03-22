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
import chardet

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

# Now import from the data_synthesis module
from src.data_synthesis import SyntheticDataGenerator

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
    
    # Save generated data
    logger.info(f"Saving output to {output_file}...")
    try:
        with open(output_file, "w") as f:
            for item in tqdm(synthetic_data, desc="Saving records"):
                f.write(json.dumps(item) + "\n")
    except IOError as e:
        logger.error(f"Failed to save output: {str(e)}")
        sys.exit(1)
        
    logger.info(f"Successfully generated {len(synthetic_data)} Q&A pairs")

    def detect_encoding(file_path):
        with open(file_path, 'rb') as f:
            result = chardet.detect(f.read())
        return result['encoding']
    
    def _load_guidelines(self, path):
        guidelines = []
        for file in Path(path).glob("*.json"):
            encoding = detect_encoding(file)
            try:
                with open(file, 'r', encoding=encoding) as f:
                    data = json.load(f)
                    guidelines.extend(data["guidelines"])
            except Exception as e:
                print(f"Skipping {file.name}: {str(e)}")
        return guidelines

if __name__ == "__main__":
    main()