"""Configuration management for CLIP for Humanists."""

import os
import yaml
from typing import Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ModelConfig:
    """Configuration for CLIP models."""
    name: str = "openai/clip-vit-base-patch32"
    batch_size: int = 16
    cache_embeddings: bool = True
    device: str = "auto"  # auto, cpu, cuda
    precision: str = "float32"  # float32, float16


@dataclass
class ProcessingConfig:
    """Configuration for image processing."""
    max_image_size: int = 512
    supported_formats: list = field(default_factory=lambda: [".jpg", ".jpeg", ".png"])
    normalize_coordinates: bool = True
    include_confidence: bool = True


@dataclass
class VisualizationConfig:
    """Configuration for visualization."""
    default_figsize: tuple = (12, 8)
    dpi: int = 300
    colormap: str = "viridis"
    map_style: str = "OpenStreetMap"
    thumbnail_size: int = 150


@dataclass
class Config:
    """Main configuration class."""
    model: ModelConfig = field(default_factory=ModelConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    visualization: VisualizationConfig = field(default_factory=VisualizationConfig)
    
    @classmethod
    def from_yaml(cls, config_path: str) -> "Config":
        """Load configuration from YAML file."""
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
        
        # Convert dictionaries to dataclass objects
        model_config = ModelConfig(**config_data.get("model", {}))
        processing_config = ProcessingConfig(**config_data.get("processing", {}))
        visualization_config = VisualizationConfig(**config_data.get("visualization", {}))
        
        return cls(
            model=model_config,
            processing=processing_config,
            visualization=visualization_config
        )
    
    @classmethod
    def default(cls) -> "Config":
        """Create default configuration."""
        return cls()
    
    def to_yaml(self, output_path: str) -> None:
        """Save configuration to YAML file."""
        config_dict = {
            "model": {
                "name": self.model.name,
                "batch_size": self.model.batch_size,
                "cache_embeddings": self.model.cache_embeddings,
                "device": self.model.device,
                "precision": self.model.precision,
            },
            "processing": {
                "max_image_size": self.processing.max_image_size,
                "supported_formats": self.processing.supported_formats,
                "normalize_coordinates": self.processing.normalize_coordinates,
                "include_confidence": self.processing.include_confidence,
            },
            "visualization": {
                "default_figsize": list(self.visualization.default_figsize),
                "dpi": self.visualization.dpi,
                "colormap": self.visualization.colormap,
                "map_style": self.visualization.map_style,
                "thumbnail_size": self.visualization.thumbnail_size,
            }
        }
        
        output_dir = os.path.dirname(output_path)
        if output_dir:  # Only create directory if path has a directory component
            os.makedirs(output_dir, exist_ok=True)
        with open(output_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False)


# Global configuration instance
_config: Optional[Config] = None


def get_config() -> Config:
    """Get the global configuration instance."""
    global _config
    if _config is None:
        _config = Config.default()
    return _config


def set_config(config: Config) -> None:
    """Set the global configuration instance."""
    global _config
    _config = config


def load_config(config_path: str) -> Config:
    """Load configuration from file and set as global."""
    config = Config.from_yaml(config_path)
    set_config(config)
    return config