"""
CLIP for Humanists: Advanced Visual Semiotic Analysis Tool

A comprehensive toolkit for analyzing images using CLIP models with spatial 
autocorrelation analysis for digital humanities research.
"""

__version__ = "2.0.0"
__author__ = "CLIP for Humanists Project"

from .core.clip_analyzer import EnhancedCLIPAnalyzer
from .core.gps_extractor import GPSExtractor

# Import spatial autocorrelation with fallback
try:
    from .analysis.autocorrelation import SpatialAutocorrelation
except ImportError:
    from .analysis.autocorrelation_simple import SimpleSpatialAutocorrelation as SpatialAutocorrelation

# Optional imports (may not be available yet)
try:
    from .analysis.statistics import StatisticalAnalysis
except ImportError:
    StatisticalAnalysis = None

try:
    from .visualization.plots import AdvancedPlots
except ImportError:
    AdvancedPlots = None

try:
    from .visualization.maps import InteractiveMaps
except ImportError:
    InteractiveMaps = None

__all__ = [
    "EnhancedCLIPAnalyzer",
    "GPSExtractor", 
    "SpatialAutocorrelation",
]

# Add optional components if available
if StatisticalAnalysis:
    __all__.append("StatisticalAnalysis")
if AdvancedPlots:
    __all__.append("AdvancedPlots")
if InteractiveMaps:
    __all__.append("InteractiveMaps")