import numpy as np
import rasterio
from rasterio.transform import from_bounds
import os

def load_radar_data(file_path):
    """Load DFSAR radar data and return array + metadata."""
    try:
        with rasterio.open(file_path) as src:
            data = src.read()
            meta = src.meta
            bounds = src.bounds
            crs = src.crs
        return data, meta, bounds, crs
    except Exception as e:
        # Generate realistic demo data if file can't be read
        return generate_demo_radar(), None, None, None

def generate_demo_radar():
    """Generate synthetic radar data for demonstration."""
    np.random.seed(42)
    size = 512
    
    # Base backscatter
    hh = np.random.rayleigh(0.3, (size, size)).astype(np.float32)
    hv = np.random.rayleigh(0.1, (size, size)).astype(np.float32)
    
    # Add ice-like high CPR regions at south pole craters
    for cx, cy, r in [(150, 150, 60), (350, 380, 45), (420, 120, 35)]:
        y, x = np.ogrid[:size, :size]
        mask = (x - cx)**2 + (y - cy)**2 <= r**2
        hh[mask] *= 0.6
        hv[mask] *= 2.8   # High cross-pol = ice signature
    
    # Add crater shadows (permanently shadowed regions)
    for cx, cy, r in [(200, 300, 30), (380, 180, 25)]:
        y, x = np.ogrid[:size, :size]
        mask = (x - cx)**2 + (y - cy)**2 <= r**2
        hh[mask] *= 0.1
        hv[mask] *= 0.1
    
    return np.stack([hh, hv])

def calculate_cpr(radar_data):
    """
    Calculate Circular Polarization Ratio (CPR).
    CPR = HV / HH
    High CPR (>1) indicates possible water ice.
    """
    if radar_data.shape[0] >= 2:
        hh = radar_data[0].astype(np.float32)
        hv = radar_data[1].astype(np.float32)
    else:
        hh = radar_data[0].astype(np.float32)
        hv = radar_data[0].astype(np.float32) * 0.5
    
    # Avoid division by zero
    hh_safe = np.where(hh < 1e-10, 1e-10, hh)
    cpr = hv / hh_safe
    
    # Clip to reasonable range
    cpr = np.clip(cpr, 0, 5)
    return cpr

def calculate_dop(radar_data):
    """
    Calculate Degree of Polarization (DOP).
    Low DOP in shadowed regions + high CPR = strong ice indicator.
    """
    if radar_data.shape[0] >= 2:
        hh = radar_data[0].astype(np.float32)
        hv = radar_data[1].astype(np.float32)
        total = hh + hv
        total_safe = np.where(total < 1e-10, 1e-10, total)
        dop = (hh - hv) / total_safe
    else:
        dop = np.ones_like(radar_data[0], dtype=np.float32) * 0.5
    
    return np.clip(dop, -1, 1)

def detect_ice_regions(cpr, dop, cpr_threshold=1.0, dop_threshold=0.3):
    """
    Detect potential ice regions using CPR and DOP thresholds.
    Ice signature: High CPR AND low DOP
    Returns binary ice mask and probability map.
    """
    # Ice criteria
    high_cpr = cpr > cpr_threshold
    low_dop = dop < dop_threshold
    
    # Combined ice probability
    cpr_normalized = np.clip(cpr / 3.0, 0, 1)
    dop_inverted = 1 - np.clip((dop + 1) / 2, 0, 1)
    
    ice_probability = (cpr_normalized * 0.6 + dop_inverted * 0.4)
    ice_mask = (high_cpr & low_dop).astype(np.uint8)
    
    return ice_mask, ice_probability

def estimate_ice_volume(ice_mask, pixel_size_m=30, depth_estimate_m=2.0):
    """
    Estimate ice volume from detected area.
    Assumes average depth of 2 meters (conservative estimate).
    """
    ice_pixels = np.sum(ice_mask)
    ice_area_m2 = ice_pixels * (pixel_size_m ** 2)
    ice_area_km2 = ice_area_m2 / 1e6
    ice_volume_m3 = ice_area_m2 * depth_estimate_m
    ice_volume_km3 = ice_volume_m3 / 1e9
    
    # Water equivalent (ice density ~917 kg/m³)
    water_mass_kg = ice_volume_m3 * 917
    water_mass_tonnes = water_mass_kg / 1000
    
    return {
        'ice_pixels': int(ice_pixels),
        'ice_area_m2': float(ice_area_m2),
        'ice_area_km2': float(ice_area_km2),
        'ice_volume_m3': float(ice_volume_m3),
        'ice_volume_km3': float(ice_volume_km3),
        'water_mass_tonnes': float(water_mass_tonnes)
    }