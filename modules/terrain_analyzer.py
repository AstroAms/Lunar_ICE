import numpy as np
from scipy import ndimage

def analyze_terrain(image_data):
    """
    Analyze terrain from OHRC image data.
    Returns slope map, roughness map, hazard map.
    """
    if image_data.ndim == 3:
        gray = image_data[0].astype(np.float32)
    else:
        gray = image_data.astype(np.float32)
    
    # Normalize
    gray = (gray - gray.min()) / (gray.max() - gray.min() + 1e-10)
    
    # Slope estimation using gradient
    gy, gx = np.gradient(gray)
    slope = np.sqrt(gx**2 + gy**2) * 100
    slope = np.clip(slope, 0, 30)
    
    # Roughness using local standard deviation
    from scipy.ndimage import generic_filter
    roughness = generic_filter(gray, np.std, size=7)
    roughness = np.clip(roughness * 50, 0, 10)
    
    # Hazard map (craters + boulders = high roughness + sudden slope change)
    laplacian = ndimage.laplace(gray)
    hazard = np.clip(np.abs(laplacian) * 200 + slope * 0.3, 0, 1)
    
    return slope, roughness, hazard

def generate_demo_terrain():
    """Generate synthetic terrain for demo mode."""
    np.random.seed(123)
    size = 512
    
    # Base terrain
    terrain = np.random.normal(0.5, 0.15, (size, size)).astype(np.float32)
    terrain = ndimage.gaussian_filter(terrain, sigma=15)
    
    # Add craters
    for cx, cy, r, depth in [(150,150,55,0.3),(350,380,40,0.25),(420,120,30,0.2),(250,250,70,0.4)]:
        y, x = np.ogrid[:size, :size]
        dist = np.sqrt((x-cx)**2 + (y-cy)**2)
        rim = np.exp(-((dist-r)/8)**2) * depth * 0.5
        bowl = np.exp(-(dist/(r*0.7))**2) * depth
        terrain += rim - bowl
    
    terrain = np.clip(terrain, 0, 1)
    return terrain[np.newaxis, :]

def select_landing_site(ice_mask, slope, hazard, ice_probability):
    """
    Select the optimal landing site.
    Criteria: Near ice, low slope (<15°), low hazard, high ice probability nearby.
    Returns coordinates and score.
    """
    size = ice_mask.shape[0]
    
    # Score each pixel
    # Proximity to ice
    from scipy.ndimage import distance_transform_edt
    ice_distance = distance_transform_edt(1 - ice_mask)
    ice_proximity = 1 - np.clip(ice_distance / 100, 0, 1)
    
    # Safety (inverse of slope and hazard)
    slope_norm = np.clip(slope / 30, 0, 1)
    safety = 1 - (slope_norm * 0.5 + hazard * 0.5)
    
    # Combined score
    score_map = (
        ice_proximity * 0.35 +
        safety * 0.40 +
        ice_probability * 0.25
    )
    
    # Exclude very hazardous areas
    score_map[hazard > 0.7] = 0
    score_map[slope > 15] = 0
    
    # Find best location
    best_idx = np.unravel_index(np.argmax(score_map), score_map.shape)
    best_score = float(score_map[best_idx])
    
    return {
        'row': int(best_idx[0]),
        'col': int(best_idx[1]),
        'score': best_score,
        'slope_at_site': float(slope[best_idx]),
        'hazard_at_site': float(hazard[best_idx]),
        'score_map': score_map
    }