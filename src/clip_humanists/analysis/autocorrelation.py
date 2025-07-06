"""Spatial autocorrelation analysis for geosemiotic patterns."""

import logging
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, field

import numpy as np
import pandas as pd
from scipy import stats
from scipy.spatial.distance import pdist, squareform
from sklearn.neighbors import NearestNeighbors
import libpysal as lps
from esda import Moran, Moran_Local, Geary, Geary_Local, Gamma, G_Local

from ..core.clip_analyzer import CLIPResult
from ..core.gps_extractor import GPSResult


logger = logging.getLogger(__name__)


@dataclass
class MoranResult:
    """Results from Moran's I analysis."""
    statistic: float
    expected_value: float
    variance: float
    z_score: float
    p_value: float
    interpretation: str
    significance_level: float = 0.05
    n_observations: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class LocalMoranResult:
    """Results from Local Moran's I analysis."""
    local_statistics: np.ndarray
    p_values: np.ndarray
    z_scores: np.ndarray
    quadrants: np.ndarray  # 1: HH, 2: LH, 3: LL, 4: HL
    significance_level: float = 0.05
    n_observations: int = 0
    hotspots: List[int] = field(default_factory=list)
    coldspots: List[int] = field(default_factory=list)
    outliers: List[int] = field(default_factory=list)


@dataclass
class GearyResult:
    """Results from Geary's C analysis."""
    statistic: float
    expected_value: float
    variance: float
    z_score: float
    p_value: float
    interpretation: str
    significance_level: float = 0.05
    n_observations: int = 0


@dataclass
class GetisOrdResult:
    """Results from Getis-Ord G analysis."""
    global_g: float
    expected_g: float
    variance_g: float
    z_score: float
    p_value: float
    local_g: Optional[np.ndarray] = None
    local_p_values: Optional[np.ndarray] = None
    local_z_scores: Optional[np.ndarray] = None
    hotspots: List[int] = field(default_factory=list)
    coldspots: List[int] = field(default_factory=list)


class SpatialAutocorrelation:
    """
    Comprehensive spatial autocorrelation analysis for visual similarity data.
    
    This class implements various spatial autocorrelation measures including:
    - Moran's I (global and local)
    - Geary's C (global and local)
    - Getis-Ord G (global and local)
    - Custom measures for semantic similarity
    """
    
    def __init__(
        self,
        distance_threshold: float = 1.0,  # km
        k_neighbors: int = 8,
        distance_metric: str = "euclidean",
        weight_type: str = "inverse_distance",
    ):
        """
        Initialize spatial autocorrelation analyzer.
        
        Args:
            distance_threshold: Maximum distance for spatial weights (km)
            k_neighbors: Number of nearest neighbors for analysis
            distance_metric: Distance metric for spatial weights
            weight_type: Type of spatial weights (inverse_distance, binary, queen, rook)
        """
        self.distance_threshold = distance_threshold
        self.k_neighbors = k_neighbors
        self.distance_metric = distance_metric
        self.weight_type = weight_type
        
        # Cache for spatial weights
        self._weights_cache = {}
        
        logger.info(f"Initialized SpatialAutocorrelation with {weight_type} weights")
    
    def _create_spatial_weights(
        self, 
        coordinates: np.ndarray,
        cache_key: Optional[str] = None
    ) -> lps.W:
        """
        Create spatial weights matrix from coordinates.
        
        Args:
            coordinates: Array of (lat, lon) coordinates
            cache_key: Optional cache key to avoid recomputation
            
        Returns:
            Spatial weights object
        """
        if cache_key and cache_key in self._weights_cache:
            return self._weights_cache[cache_key]
        
        n_points = len(coordinates)
        
        if self.weight_type == "inverse_distance":
            # Calculate pairwise distances
            distances = squareform(pdist(coordinates, metric=self.distance_metric))
            
            # Convert to inverse distance weights
            weights = 1.0 / (distances + 1e-10)  # Add small value to avoid division by zero
            np.fill_diagonal(weights, 0)  # No self-influence
            
            # Apply distance threshold
            weights[distances > self.distance_threshold] = 0
            
            # Create libpysal weights object
            neighbors = {}
            weights_dict = {}
            
            for i in range(n_points):
                valid_neighbors = np.where(weights[i] > 0)[0]
                if len(valid_neighbors) > 0:
                    neighbors[i] = valid_neighbors.tolist()
                    weights_dict[i] = weights[i][valid_neighbors].tolist()
                else:
                    neighbors[i] = []
                    weights_dict[i] = []
            
            w = lps.W(neighbors, weights_dict)
            
        elif self.weight_type == "binary":
            # Binary weights based on distance threshold
            distances = squareform(pdist(coordinates, metric=self.distance_metric))
            
            neighbors = {}
            weights_dict = {}
            
            for i in range(n_points):
                valid_neighbors = np.where(
                    (distances[i] <= self.distance_threshold) & 
                    (distances[i] > 0)
                )[0]
                
                if len(valid_neighbors) > 0:
                    neighbors[i] = valid_neighbors.tolist()
                    weights_dict[i] = [1.0] * len(valid_neighbors)
                else:
                    neighbors[i] = []
                    weights_dict[i] = []
            
            w = lps.W(neighbors, weights_dict)
            
        elif self.weight_type == "k_nearest":
            # K-nearest neighbors
            nbrs = NearestNeighbors(n_neighbors=self.k_neighbors + 1, metric=self.distance_metric)
            nbrs.fit(coordinates)
            distances, indices = nbrs.kneighbors(coordinates)
            
            neighbors = {}
            weights_dict = {}
            
            for i in range(n_points):
                # Exclude self (index 0)
                valid_neighbors = indices[i][1:].tolist()
                neighbor_distances = distances[i][1:]
                
                neighbors[i] = valid_neighbors
                # Inverse distance weights
                weights_dict[i] = (1.0 / (neighbor_distances + 1e-10)).tolist()
            
            w = lps.W(neighbors, weights_dict)
            
        else:
            raise ValueError(f"Unknown weight type: {self.weight_type}")
        
        # Cache the weights
        if cache_key:
            self._weights_cache[cache_key] = w
        
        return w
    
    def _prepare_data(
        self, 
        data: Union[List[CLIPResult], List[GPSResult], pd.DataFrame],
        similarity_field: str = "similarities"
    ) -> Tuple[np.ndarray, np.ndarray, List[str]]:
        """
        Prepare data for spatial autocorrelation analysis.
        
        Args:
            data: Input data (CLIPResult objects, GPSResult objects, or DataFrame)
            similarity_field: Field containing similarity scores
            
        Returns:
            Tuple of (coordinates, similarity_values, prompt_names)
        """
        if isinstance(data, pd.DataFrame):
            # Extract coordinates
            if 'latitude' in data.columns and 'longitude' in data.columns:
                coordinates = data[['latitude', 'longitude']].values
            else:
                raise ValueError("DataFrame must contain 'latitude' and 'longitude' columns")
            
            # Extract similarity values
            similarity_columns = [col for col in data.columns if col.startswith('similarity_')]
            if not similarity_columns:
                raise ValueError("No similarity columns found in DataFrame")
            
            similarity_values = data[similarity_columns].values
            prompt_names = [col.replace('similarity_', '') for col in similarity_columns]
            
        elif isinstance(data, list) and len(data) > 0:
            if isinstance(data[0], CLIPResult):
                # Extract from CLIPResult objects
                coordinates = []
                similarities_dict = {}
                
                for result in data:
                    if hasattr(result, 'gps_coordinates') and result.gps_coordinates:
                        coordinates.append(result.gps_coordinates)
                        for prompt, score in result.similarities.items():
                            if prompt not in similarities_dict:
                                similarities_dict[prompt] = []
                            similarities_dict[prompt].append(score)
                
                if not coordinates:
                    raise ValueError("No valid GPS coordinates found in CLIPResult objects")
                
                coordinates = np.array(coordinates)
                prompt_names = list(similarities_dict.keys())
                similarity_values = np.array([similarities_dict[prompt] for prompt in prompt_names]).T
                
            else:
                raise ValueError("Unsupported data type")
        else:
            raise ValueError("Data must be a list of CLIPResult objects or a pandas DataFrame")
        
        return coordinates, similarity_values, prompt_names
    
    def morans_i(
        self, 
        data: Union[List[CLIPResult], pd.DataFrame],
        prompt: Optional[str] = None,
        **kwargs
    ) -> Union[MoranResult, Dict[str, MoranResult]]:
        """
        Calculate Moran's I statistic for spatial autocorrelation.
        
        Args:
            data: Input data
            prompt: Specific prompt to analyze (if None, analyze all prompts)
            **kwargs: Additional parameters for Moran's I calculation
            
        Returns:
            MoranResult or dictionary of MoranResult objects
        """
        coordinates, similarity_values, prompt_names = self._prepare_data(data)
        
        # Create spatial weights
        w = self._create_spatial_weights(coordinates)
        
        results = {}
        
        # Analyze specific prompt or all prompts
        prompts_to_analyze = [prompt] if prompt else prompt_names
        
        for i, prompt_name in enumerate(prompts_to_analyze):
            if prompt_name not in prompt_names:
                logger.warning(f"Prompt '{prompt_name}' not found in data")
                continue
            
            prompt_index = prompt_names.index(prompt_name)
            values = similarity_values[:, prompt_index]
            
            # Calculate Moran's I
            try:
                moran = Moran(values, w, **kwargs)
                
                # Determine interpretation
                if moran.p_sim < 0.05:
                    if moran.I > moran.EI:
                        interpretation = "Significant positive spatial autocorrelation (clustered)"
                    else:
                        interpretation = "Significant negative spatial autocorrelation (dispersed)"
                else:
                    interpretation = "No significant spatial autocorrelation (random)"
                
                result = MoranResult(
                    statistic=moran.I,
                    expected_value=moran.EI,
                    variance=moran.VI_sim,
                    z_score=moran.z_sim,
                    p_value=moran.p_sim,
                    interpretation=interpretation,
                    n_observations=len(values),
                    metadata={
                        "prompt": prompt_name,
                        "weight_type": self.weight_type,
                        "distance_threshold": self.distance_threshold,
                    }
                )
                
                results[prompt_name] = result
                
            except Exception as e:
                logger.error(f"Error calculating Moran's I for prompt '{prompt_name}': {e}")
                continue
        
        return results[prompt] if prompt else results
    
    def local_morans_i(
        self, 
        data: Union[List[CLIPResult], pd.DataFrame],
        prompt: str,
        **kwargs
    ) -> LocalMoranResult:
        """
        Calculate Local Moran's I for hotspot analysis.
        
        Args:
            data: Input data
            prompt: Specific prompt to analyze
            **kwargs: Additional parameters for Local Moran's I calculation
            
        Returns:
            LocalMoranResult object
        """
        coordinates, similarity_values, prompt_names = self._prepare_data(data)
        
        if prompt not in prompt_names:
            raise ValueError(f"Prompt '{prompt}' not found in data")
        
        prompt_index = prompt_names.index(prompt)
        values = similarity_values[:, prompt_index]
        
        # Create spatial weights
        w = self._create_spatial_weights(coordinates)
        
        try:
            # Calculate Local Moran's I
            local_moran = Moran_Local(values, w, **kwargs)
            
            # Identify significant hotspots, coldspots, and outliers
            significant = local_moran.p_sim < 0.05
            
            hotspots = []
            coldspots = []
            outliers = []
            
            for i, (is_sig, quadrant, local_i) in enumerate(
                zip(significant, local_moran.q, local_moran.Is)
            ):
                if is_sig:
                    if quadrant == 1:  # HH: High-High
                        hotspots.append(i)
                    elif quadrant == 3:  # LL: Low-Low
                        coldspots.append(i)
                    elif quadrant in [2, 4]:  # LH or HL: Outliers
                        outliers.append(i)
            
            return LocalMoranResult(
                local_statistics=local_moran.Is,
                p_values=local_moran.p_sim,
                z_scores=local_moran.z_sim,
                quadrants=local_moran.q,
                n_observations=len(values),
                hotspots=hotspots,
                coldspots=coldspots,
                outliers=outliers,
            )
            
        except Exception as e:
            logger.error(f"Error calculating Local Moran's I: {e}")
            raise
    
    def gearys_c(
        self, 
        data: Union[List[CLIPResult], pd.DataFrame],
        prompt: Optional[str] = None,
        **kwargs
    ) -> Union[GearyResult, Dict[str, GearyResult]]:
        """
        Calculate Geary's C statistic for spatial autocorrelation.
        
        Args:
            data: Input data
            prompt: Specific prompt to analyze (if None, analyze all prompts)
            **kwargs: Additional parameters for Geary's C calculation
            
        Returns:
            GearyResult or dictionary of GearyResult objects
        """
        coordinates, similarity_values, prompt_names = self._prepare_data(data)
        
        # Create spatial weights
        w = self._create_spatial_weights(coordinates)
        
        results = {}
        
        # Analyze specific prompt or all prompts
        prompts_to_analyze = [prompt] if prompt else prompt_names
        
        for i, prompt_name in enumerate(prompts_to_analyze):
            if prompt_name not in prompt_names:
                logger.warning(f"Prompt '{prompt_name}' not found in data")
                continue
            
            prompt_index = prompt_names.index(prompt_name)
            values = similarity_values[:, prompt_index]
            
            # Calculate Geary's C
            try:
                geary = Geary(values, w, **kwargs)
                
                # Determine interpretation
                if geary.p_sim < 0.05:
                    if geary.C < geary.EC:
                        interpretation = "Significant positive spatial autocorrelation (clustered)"
                    else:
                        interpretation = "Significant negative spatial autocorrelation (dispersed)"
                else:
                    interpretation = "No significant spatial autocorrelation (random)"
                
                result = GearyResult(
                    statistic=geary.C,
                    expected_value=geary.EC,
                    variance=geary.VC_sim,
                    z_score=geary.z_sim,
                    p_value=geary.p_sim,
                    interpretation=interpretation,
                    n_observations=len(values),
                )
                
                results[prompt_name] = result
                
            except Exception as e:
                logger.error(f"Error calculating Geary's C for prompt '{prompt_name}': {e}")
                continue
        
        return results[prompt] if prompt else results
    
    def getis_ord_g(
        self, 
        data: Union[List[CLIPResult], pd.DataFrame],
        prompt: str,
        local: bool = True,
        **kwargs
    ) -> GetisOrdResult:
        """
        Calculate Getis-Ord G statistic for hot/cold spot analysis.
        
        Args:
            data: Input data
            prompt: Specific prompt to analyze
            local: Whether to calculate local statistics
            **kwargs: Additional parameters for Getis-Ord G calculation
            
        Returns:
            GetisOrdResult object
        """
        coordinates, similarity_values, prompt_names = self._prepare_data(data)
        
        if prompt not in prompt_names:
            raise ValueError(f"Prompt '{prompt}' not found in data")
        
        prompt_index = prompt_names.index(prompt)
        values = similarity_values[:, prompt_index]
        
        # Create spatial weights
        w = self._create_spatial_weights(coordinates)
        
        try:
            # Calculate Global G
            # Note: This is a simplified implementation
            # Full implementation would use proper Getis-Ord G formulas
            
            # For now, we'll use a custom implementation
            n = len(values)
            W = w.full()[0]  # Get full weights matrix
            
            # Global G
            numerator = 0
            denominator = 0
            
            for i in range(n):
                for j in range(n):
                    if i != j:
                        numerator += W[i, j] * values[i] * values[j]
                        denominator += values[i] * values[j]
            
            global_g = numerator / denominator if denominator > 0 else 0
            
            # Expected G and variance (simplified)
            expected_g = np.sum(W) / (n * (n - 1))
            
            # Variance calculation (simplified)
            variance_g = 0.1  # Placeholder
            
            # Z-score and p-value
            z_score = (global_g - expected_g) / np.sqrt(variance_g) if variance_g > 0 else 0
            p_value = 2 * (1 - stats.norm.cdf(abs(z_score)))
            
            # Local G statistics
            local_g = None
            local_p_values = None
            local_z_scores = None
            hotspots = []
            coldspots = []
            
            if local:
                try:
                    # Use esda's G_Local if available
                    local_g_obj = G_Local(values, w, **kwargs)
                    local_g = local_g_obj.Gs
                    local_z_scores = local_g_obj.z_sim
                    local_p_values = local_g_obj.p_sim
                    
                    # Identify hotspots and coldspots
                    significant = local_p_values < 0.05
                    
                    for i, (is_sig, z_score, local_stat) in enumerate(
                        zip(significant, local_z_scores, local_g)
                    ):
                        if is_sig:
                            if z_score > 0:
                                hotspots.append(i)
                            else:
                                coldspots.append(i)
                                
                except Exception as e:
                    logger.warning(f"Error calculating Local G statistics: {e}")
            
            return GetisOrdResult(
                global_g=global_g,
                expected_g=expected_g,
                variance_g=variance_g,
                z_score=z_score,
                p_value=p_value,
                local_g=local_g,
                local_p_values=local_p_values,
                local_z_scores=local_z_scores,
                hotspots=hotspots,
                coldspots=coldspots,
            )
            
        except Exception as e:
            logger.error(f"Error calculating Getis-Ord G: {e}")
            raise
    
    def semantic_autocorrelation(
        self, 
        data: Union[List[CLIPResult], pd.DataFrame],
        cross_correlation: bool = True
    ) -> Dict[str, Any]:
        """
        Calculate semantic autocorrelation across different prompts.
        
        Args:
            data: Input data
            cross_correlation: Whether to calculate cross-correlations between prompts
            
        Returns:
            Dictionary with semantic autocorrelation results
        """
        coordinates, similarity_values, prompt_names = self._prepare_data(data)
        
        results = {
            "prompt_autocorrelations": {},
            "cross_correlations": {},
            "semantic_clusters": {},
        }
        
        # Calculate autocorrelation for each prompt
        for i, prompt in enumerate(prompt_names):
            moran_result = self.morans_i(data, prompt)
            results["prompt_autocorrelations"][prompt] = moran_result
        
        # Calculate cross-correlations between prompts
        if cross_correlation and len(prompt_names) > 1:
            for i in range(len(prompt_names)):
                for j in range(i + 1, len(prompt_names)):
                    prompt1, prompt2 = prompt_names[i], prompt_names[j]
                    
                    # Calculate spatial cross-correlation
                    values1 = similarity_values[:, i]
                    values2 = similarity_values[:, j]
                    
                    # Simple cross-correlation (can be enhanced)
                    correlation = np.corrcoef(values1, values2)[0, 1]
                    
                    results["cross_correlations"][f"{prompt1}_vs_{prompt2}"] = {
                        "correlation": correlation,
                        "p_value": stats.pearsonr(values1, values2)[1],
                    }
        
        return results
    
    def clear_cache(self) -> None:
        """Clear the spatial weights cache."""
        self._weights_cache.clear()
        logger.info("Spatial weights cache cleared")
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the spatial weights cache."""
        return {
            "cache_size": len(self._weights_cache),
            "cache_keys": list(self._weights_cache.keys()),
        }