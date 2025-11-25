"""
Gel analysis utilities for electrophoresis gel quantification
Provides functions for lane detection, band identification, and intensity quantification
"""

import numpy as np
from scipy import signal, ndimage
from skimage import filters, measure
import cv2

def load_gel_image(file_path):
    """Load gel image and convert to appropriate format"""
    img = cv2.imread(file_path, cv2.IMREAD_GRAYSCALE)
    return img

def invert_gel(image):
    """Invert gel image (bands should be bright on dark background)"""
    return 255 - image

def detect_lanes(image, num_lanes=None, method='projection'):
    """
    Detect lanes in gel image
    
    Args:
        image: Gel image (grayscale)
        num_lanes: Expected number of lanes (optional)
        method: Detection method ('projection' or 'vertical_lines')
    
    Returns:
        List of lane boundaries [(x_start, x_end), ...]
    """
    height, width = image.shape
    
    if method == 'projection':
        # Sum intensity along vertical axis
        vertical_profile = np.sum(image, axis=0)
        
        # Smooth the profile
        smoothed = signal.savgol_filter(vertical_profile, 51, 3)
        
        # Find valleys (lane separators)
        peaks, _ = signal.find_peaks(-smoothed, distance=width//(num_lanes+1) if num_lanes else 50)
        
        # Create lane boundaries
        lanes = []
        if len(peaks) > 0:
            # Add boundaries at start and end
            boundaries = [0] + list(peaks) + [width]
            for i in range(len(boundaries) - 1):
                lanes.append((boundaries[i], boundaries[i+1]))
        else:
            # If no lanes detected, divide equally
            if num_lanes:
                lane_width = width // num_lanes
                lanes = [(i*lane_width, (i+1)*lane_width) for i in range(num_lanes)]
            else:
                lanes = [(0, width)]
    
    return lanes

def extract_lane(image, lane_bounds):
    """Extract a single lane from gel image"""
    x_start, x_end = lane_bounds
    return image[:, x_start:x_end]

def detect_bands(lane_image, threshold_method='otsu', min_distance=20):
    """
    Detect bands in a lane
    
    Args:
        lane_image: Image of single lane
        threshold_method: Thresholding method
        min_distance: Minimum distance between bands in pixels
    
    Returns:
        List of band positions and properties
    """
    # Get horizontal intensity profile
    horizontal_profile = np.mean(lane_image, axis=1)
    
    # Smooth profile
    smoothed = signal.savgol_filter(horizontal_profile, 11, 2)
    
    # Find peaks (bands)
    peaks, properties = signal.find_peaks(
        smoothed, 
        distance=min_distance,
        prominence=np.std(smoothed) * 0.5
    )
    
    bands = []
    for i, peak in enumerate(peaks):
        # Calculate band properties
        band = {
            'position': int(peak),
            'intensity': float(smoothed[peak]),
            'prominence': float(properties['prominences'][i]) if 'prominences' in properties else 0,
            'width': properties['widths'][i] if 'widths' in properties else 0
        }
        bands.append(band)
    
    return bands

def quantify_band(lane_image, band_position, band_width=None):
    """
    Quantify band intensity
    
    Args:
        lane_image: Image of lane
        band_position: Y-coordinate of band center
        band_width: Width of band (auto-detect if None)
    
    Returns:
        Dictionary with quantification metrics
    """
    height, width = lane_image.shape
    
    if band_width is None:
        # Auto-detect band width
        profile = np.mean(lane_image, axis=1)
        band_width = 20  # Default width
    
    # Define band region
    y_start = max(0, int(band_position - band_width/2))
    y_end = min(height, int(band_position + band_width/2))
    
    band_region = lane_image[y_start:y_end, :]
    
    # Calculate metrics
    metrics = {
        'position': band_position,
        'mean_intensity': float(np.mean(band_region)),
        'max_intensity': float(np.max(band_region)),
        'total_intensity': float(np.sum(band_region)),
        'area': band_region.size,
        'volume': float(np.sum(band_region)),  # Sum of all pixel intensities
        'width': band_width
    }
    
    return metrics

def analyze_gel(image, num_lanes=None, lane_bounds=None):
    """
    Complete gel analysis pipeline
    
    Args:
        image: Gel image
        num_lanes: Number of lanes (optional)
        lane_bounds: Pre-defined lane boundaries (optional)
    
    Returns:
        Dictionary with analysis results for all lanes
    """
    # Detect lanes if not provided
    if lane_bounds is None:
        lane_bounds = detect_lanes(image, num_lanes=num_lanes)
    
    results = {
        'num_lanes': len(lane_bounds),
        'lanes': []
    }
    
    # Analyze each lane
    for i, bounds in enumerate(lane_bounds):
        lane_img = extract_lane(image, bounds)
        bands = detect_bands(lane_img)
        
        # Quantify each band
        quantified_bands = []
        for band in bands:
            metrics = quantify_band(lane_img, band['position'])
            band.update(metrics)
            quantified_bands.append(band)
        
        results['lanes'].append({
            'lane_number': i + 1,
            'bounds': bounds,
            'num_bands': len(quantified_bands),
            'bands': quantified_bands
        })
    
    return results

def calculate_molecular_weight(band_position, marker_positions, marker_weights):
    """
    Calculate molecular weight based on marker ladder
    
    Args:
        band_position: Y-coordinate of band
        marker_positions: List of marker band positions
        marker_weights: List of corresponding molecular weights (kDa)
    
    Returns:
        Estimated molecular weight in kDa
    """
    # Fit log-linear relationship between position and molecular weight
    log_weights = np.log10(marker_weights)
    
    # Linear interpolation/extrapolation
    estimated_log_weight = np.interp(band_position, marker_positions, log_weights)
    estimated_weight = 10 ** estimated_log_weight
    
    return estimated_weight

def normalize_lanes(gel_results, reference_lane=None, method='total_intensity'):
    """
    Normalize band intensities across lanes
    
    Args:
        gel_results: Results from analyze_gel
        reference_lane: Lane to use as reference (None for global normalization)
        method: Normalization method ('total_intensity', 'loading_control')
    
    Returns:
        Normalized gel results
    """
    if method == 'total_intensity':
        # Calculate total intensity per lane
        lane_totals = []
        for lane in gel_results['lanes']:
            total = sum(band['total_intensity'] for band in lane['bands'])
            lane_totals.append(total)
        
        # Determine normalization factor
        if reference_lane is not None:
            norm_factor = lane_totals[reference_lane]
        else:
            norm_factor = np.mean(lane_totals)
        
        # Normalize each lane
        for i, lane in enumerate(gel_results['lanes']):
            factor = norm_factor / lane_totals[i] if lane_totals[i] > 0 else 1
            for band in lane['bands']:
                band['normalized_intensity'] = band['total_intensity'] * factor
    
    return gel_results

def compare_bands(gel_results, lane1, lane2, band_index):
    """
    Compare band intensity between two lanes
    
    Args:
        gel_results: Results from analyze_gel
        lane1, lane2: Lane indices to compare
        band_index: Band index within lanes
    
    Returns:
        Comparison metrics
    """
    try:
        band1 = gel_results['lanes'][lane1]['bands'][band_index]
        band2 = gel_results['lanes'][lane2]['bands'][band_index]
        
        ratio = band1['total_intensity'] / band2['total_intensity']
        fold_change = ratio if ratio >= 1 else -1/ratio
        
        return {
            'lane1_intensity': band1['total_intensity'],
            'lane2_intensity': band2['total_intensity'],
            'ratio': ratio,
            'fold_change': fold_change,
            'percent_difference': ((band1['total_intensity'] - band2['total_intensity']) / 
                                  band2['total_intensity'] * 100)
        }
    except (IndexError, ZeroDivisionError) as e:
        return {'error': str(e)}
