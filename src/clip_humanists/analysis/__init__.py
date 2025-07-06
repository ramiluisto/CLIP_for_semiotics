"""Analysis components for spatial autocorrelation and multimodal content analysis."""

# Try to import full version, fall back to simplified
try:
    from .autocorrelation import SpatialAutocorrelation
    FULL_SPATIAL_AVAILABLE = True
except ImportError:
    from .autocorrelation_simple import SimpleSpatialAutocorrelation as SpatialAutocorrelation
    FULL_SPATIAL_AVAILABLE = False

# Import multimodal content analysis
try:
    from .multimodal_content import MultimodalContentAnalyzer
    MULTIMODAL_AVAILABLE = True
except ImportError:
    MultimodalContentAnalyzer = None
    MULTIMODAL_AVAILABLE = False

__all__ = ["SpatialAutocorrelation", "FULL_SPATIAL_AVAILABLE"]

if MultimodalContentAnalyzer:
    __all__.extend(["MultimodalContentAnalyzer", "MULTIMODAL_AVAILABLE"])