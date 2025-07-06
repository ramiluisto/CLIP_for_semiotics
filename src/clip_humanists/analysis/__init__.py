"""Analysis components for spatial autocorrelation and statistical analysis."""

# Try to import full version, fall back to simplified
try:
    from .autocorrelation import SpatialAutocorrelation
    FULL_SPATIAL_AVAILABLE = True
except ImportError:
    from .autocorrelation_simple import SimpleSpatialAutocorrelation as SpatialAutocorrelation
    FULL_SPATIAL_AVAILABLE = False

__all__ = ["SpatialAutocorrelation", "FULL_SPATIAL_AVAILABLE"]