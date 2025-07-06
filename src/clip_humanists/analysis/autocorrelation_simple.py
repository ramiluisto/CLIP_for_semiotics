"""Simplified spatial autocorrelation analysis without heavy dependencies."""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.neighbors import NearestNeighbors

logger = logging.getLogger(__name__)


@dataclass
class SimpleMoranResult:
    """Simplified results from Moran's I analysis."""
    statistic: float
    expected_value: float
    variance: float
    z_score: float
    p_value: float
    interpretation: str
    significance_level: float = 0.05
    n_observations: int = 0


class SimpleSpatialAutocorrelation:
    """
    Simplified spatial autocorrelation analysis using basic implementations.
    This version doesn't require libpysal/esda but provides core functionality.
    """
    
    def __init__(
        self,
        distance_threshold: float = 1.0,  # km
        k_neighbors: int = 8,
    ):
        """Initialize simplified spatial autocorrelation analyzer."""
        self.distance_threshold = distance_threshold
        self.k_neighbors = k_neighbors
        
        logger.info("Initialized SimpleSpatialAutocorrelation")
    
    def _create_weights_matrix(self, coordinates: np.ndarray) -> np.ndarray:
        """Create simple distance-based weights matrix."""
        n = len(coordinates)
        distances = squareform(pdist(coordinates))
        
        # Create inverse distance weights
        weights = 1.0 / (distances + 1e-10)
        np.fill_diagonal(weights, 0)  # No self-influence
        
        # Apply distance threshold
        weights[distances > self.distance_threshold] = 0
        
        # Row normalize
        row_sums = weights.sum(axis=1)
        row_sums[row_sums == 0] = 1  # Avoid division by zero
        weights = weights / row_sums[:, np.newaxis]
        
        return weights
    
    def _prepare_data_simple(self, data: List[Any]) -> Tuple[np.ndarray, Dict[str, np.ndarray]]:
        """Prepare data for analysis (simplified version)."""
        coordinates = []
        similarities = {}
        
        for item in data:
            if hasattr(item, 'gps_coordinates') and item.gps_coordinates:
                coordinates.append(item.gps_coordinates)
                
                if hasattr(item, 'similarities'):
                    for prompt, score in item.similarities.items():
                        if prompt not in similarities:
                            similarities[prompt] = []
                        similarities[prompt].append(score)
        
        if not coordinates:
            raise ValueError("No valid GPS coordinates found")
        
        coordinates = np.array(coordinates)
        similarities = {k: np.array(v) for k, v in similarities.items()}
        
        return coordinates, similarities
    
    def simple_morans_i(self, data: List[Any], prompt: str) -> SimpleMoranResult:
        """
        Calculate a simplified version of Moran's I.
        
        Args:
            data: List of data objects with gps_coordinates and similarities
            prompt: Prompt to analyze
            
        Returns:
            SimpleMoranResult object
        """
        coordinates, similarities = self._prepare_data_simple(data)
        
        if prompt not in similarities:
            raise ValueError(f"Prompt '{prompt}' not found in data")
        
        values = similarities[prompt]
        n = len(values)
        
        if n < 3:
            raise ValueError("Need at least 3 observations for Moran's I")
        
        # Create weights matrix
        W = self._create_weights_matrix(coordinates)
        
        # Calculate Moran's I
        mean_y = np.mean(values)
        y_centered = values - mean_y
        
        # Numerator: sum of weighted cross-products
        numerator = 0
        for i in range(n):
            for j in range(n):
                numerator += W[i, j] * y_centered[i] * y_centered[j]
        
        # Denominator: sum of squared deviations
        denominator = np.sum(y_centered ** 2)
        
        # Sum of weights
        S0 = np.sum(W)
        
        # Moran's I statistic
        if denominator == 0 or S0 == 0:
            I = 0
        else:
            I = (n / S0) * (numerator / denominator)
        
        # Expected value under null hypothesis
        EI = -1 / (n - 1)
        
        # Simplified variance calculation
        S1 = 0.5 * np.sum((W + W.T) ** 2)
        S2 = np.sum(np.sum(W, axis=1) ** 2)
        
        b2 = n * np.sum(y_centered ** 4) / (np.sum(y_centered ** 2) ** 2)
        
        # Variance under normality assumption
        VI = ((n * ((n**2 - 3*n + 3) * S1 - n * S2 + 3 * S0**2) - 
               b2 * ((n**2 - n) * S1 - 2*n * S2 + 6 * S0**2)) / 
              ((n - 1) * (n - 2) * (n - 3) * S0**2))
        
        # Z-score and p-value
        if VI > 0:
            z_score = (I - EI) / np.sqrt(VI)
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
        else:
            z_score = 0
            p_value = 1
        
        # Interpretation
        if p_value < 0.05:
            if I > EI:
                interpretation = "Significant positive spatial autocorrelation (clustered)"
            else:
                interpretation = "Significant negative spatial autocorrelation (dispersed)"
        else:
            interpretation = "No significant spatial autocorrelation (random)"
        
        return SimpleMoranResult(
            statistic=I,
            expected_value=EI,
            variance=VI,
            z_score=z_score,
            p_value=p_value,
            interpretation=interpretation,
            n_observations=n,
        )
    
    def analyze_all_prompts(self, data: List[Any]) -> Dict[str, SimpleMoranResult]:
        """Analyze all prompts in the data."""
        _, similarities = self._prepare_data_simple(data)
        
        results = {}
        for prompt in similarities.keys():
            try:
                result = self.simple_morans_i(data, prompt)
                results[prompt] = result
            except Exception as e:
                logger.warning(f"Failed to analyze prompt '{prompt}': {e}")
        
        return results


# Conditional import for full functionality
try:
    from .autocorrelation import SpatialAutocorrelation as FullSpatialAutocorrelation
    # If successful, use the full version
    SpatialAutocorrelation = FullSpatialAutocorrelation
    logger.info("Full spatial autocorrelation module available")
except ImportError:
    logger.info("Using simplified spatial autocorrelation (missing libpysal/esda)")
    SpatialAutocorrelation = SimpleSpatialAutocorrelation