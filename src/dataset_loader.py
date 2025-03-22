from datasets import load_dataset
import logging
from typing import Dict, List, Any, Optional
import yaml
from pathlib import Path

class DatasetLoader:
    """
    Handles loading and processing of medical datasets with robust error handling 
    and advanced dataset management capabilities.
    """
    
    def __init__(self, config_path: Optional[str] = None, logger: Optional[logging.Logger] = None):
        """
        Initialize the dataset loader with comprehensive configuration.
        
        Args:
            config_path: Optional path to dataset configuration file
            logger: Optional custom logger
        """
        # Setup logging
        self.logger = logger or logging.getLogger(__name__)
        
        # Set project root and configuration path
        self.project_root = Path(__file__).parent.parent
        self.config_path = config_path or self.project_root / "config" / "data_config.yaml"
        
        # Initialize tracking variables
        self.loaded_datasets = []
        self.successful_datasets = 0
        self.failed_datasets = 0
        
        # Load configuration
        self.config = self._load_config()
    
    def _load_config(self) -> Dict:
        """
        Load dataset configuration with enhanced error handling.
        
        Returns:
            Dictionary of dataset configurations
        """
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)
            
            # Validate configuration
            if not config or 'datasets' not in config:
                self.logger.warning("Empty or invalid dataset configuration")
                return {"datasets": []}
            
            return config
        
        except FileNotFoundError:
            self.logger.error(f"Configuration file not found: {self.config_path}")
            return {"datasets": []}
        
        except yaml.YAMLError as e:
            self.logger.error(f"YAML parsing error: {e}")
            return {"datasets": []}
        
        except Exception as e:
            self.logger.error(f"Unexpected error loading config: {e}")
            return {"datasets": []}
    
    def load_datasets(self) -> List[Dict[str, Any]]:
        """
        Load all configured datasets with comprehensive error handling.
        
        Returns:
            List of loaded dataset information
        """
        # Reset dataset tracking
        self.loaded_datasets = []
        self.successful_datasets = 0
        self.failed_datasets = 0
        
        # Load datasets from configuration
        for dataset_config in self.config.get("datasets", []):
            try:
                # Extract dataset configuration
                name = dataset_config.get("name")
                config = dataset_config.get("config")
                split = dataset_config.get("split", "train")
                max_samples = dataset_config.get("samples", -1)
                
                self.logger.info(f"Attempting to load dataset: {name}")
                
                # Load dataset
                dataset = load_dataset(
                    name, 
                    config, 
                    split=split
                )
                
                # Sample dataset if required
                if max_samples > 0:
                    dataset = dataset.select(range(min(len(dataset), max_samples)))
                
                # Prepare dataset metadata
                dataset_info = {
                    "name": name,
                    "category": dataset_config.get("category", "General"),
                    "dataset": dataset,
                    "size": len(dataset),
                    "split": split
                }
                
                self.loaded_datasets.append(dataset_info)
                self.successful_datasets += 1
                
                self.logger.info(
                    f"Successfully loaded {name} with {len(dataset)} examples "
                    f"from {split} split"
                )
                
            except Exception as e:
                self.failed_datasets += 1
                self.logger.error(f"Failed to load dataset {name}: {e}")
        
        return self.loaded_datasets
    
    def get_dataset_status(self) -> Dict[str, Any]:
        """
        Provide comprehensive status of dataset loading.
        
        Returns:
            Dictionary with dataset loading statistics
        """
        return {
            "total_datasets_attempted": self.successful_datasets + self.failed_datasets,
            "successful_datasets": self.successful_datasets,
            "failed_datasets": self.failed_datasets,
            "total_examples": sum(dataset["size"] for dataset in self.loaded_datasets),
            "datasets": [
                {
                    "name": dataset["name"],
                    "category": dataset["category"],
                    "size": dataset["size"],
                    "split": dataset.get("split", "unknown")
                }
                for dataset in self.loaded_datasets
            ]
        }
    
    def has_sufficient_data(self, min_examples: int = 1000) -> bool:
        """
        Determine if loaded datasets provide sufficient data for analysis.
        
        Args:
            min_examples: Minimum number of examples required
        
        Returns:
            Boolean indicating if data is sufficient
        """
        total_examples = sum(dataset["size"] for dataset in self.loaded_datasets)
        return (
            self.successful_datasets > 0 and 
            total_examples >= min_examples
        )
    
    def get_datasets_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Retrieve datasets by specific category.
        
        Args:
            category: Category to filter datasets
        
        Returns:
            List of datasets matching the category
        """
        return [
            dataset for dataset in self.loaded_datasets 
            if dataset['category'].lower() == category.lower()
        ]

def main():
    """
    Demonstrate DatasetLoader functionality.
    """
    try:
        # Initialize dataset loader
        loader = DatasetLoader()
        
        # Load datasets
        loader.load_datasets()
        
        # Get dataset status
        status = loader.get_dataset_status()
        print("Dataset Loading Status:")
        print(f"Total Datasets: {status['total_datasets_attempted']}")
        print(f"Successful Datasets: {status['successful_datasets']}")
        print(f"Failed Datasets: {status['failed_datasets']}")
        print(f"Total Examples: {status['total_examples']}")
        
        # Check if data is sufficient
        if loader.has_sufficient_data():
            print("\nDataset loading successful. Data is sufficient for analysis.")
        else:
            print("\nWarning: Insufficient data loaded.")
        
    except Exception as e:
        print(f"Error in dataset loading: {e}")

if __name__ == "__main__":
    main()