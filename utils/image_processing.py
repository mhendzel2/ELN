"""
Image processing utilities for the ELN system
Provides functions for image analysis, enhancement, and measurements
"""

import numpy as np
from PIL import Image
from skimage import filters, measure, morphology, color
from skimage.feature import peak_local_max
import io

def load_image(file_path):
    """Load an image from file path"""
    return np.array(Image.open(file_path))

def load_image_from_bytes(image_bytes):
    """Load an image from bytes"""
    return np.array(Image.open(io.BytesIO(image_bytes)))

def convert_to_grayscale(image):
    """Convert image to grayscale"""
    if len(image.shape) == 3:
        return color.rgb2gray(image)
    return image

def enhance_contrast(image, method='adaptive'):
    """Enhance image contrast"""
    if method == 'adaptive':
        # Adaptive histogram equalization
        from skimage import exposure
        return exposure.equalize_adapthist(image)
    elif method == 'histogram':
        from skimage import exposure
        return exposure.equalize_hist(image)
    return image

def detect_edges(image, method='canny', sigma=1.0):
    """Detect edges in image"""
    gray = convert_to_grayscale(image)
    
    if method == 'canny':
        return filters.canny(gray, sigma=sigma)
    elif method == 'sobel':
        return filters.sobel(gray)
    elif method == 'prewitt':
        return filters.prewitt(gray)
    return gray

def threshold_image(image, method='otsu'):
    """Apply thresholding to segment image"""
    gray = convert_to_grayscale(image)
    
    if method == 'otsu':
        threshold = filters.threshold_otsu(gray)
    elif method == 'li':
        threshold = filters.threshold_li(gray)
    elif method == 'yen':
        threshold = filters.threshold_yen(gray)
    else:
        threshold = 0.5
    
    return gray > threshold

def count_objects(binary_image, min_size=50):
    """Count objects in binary image"""
    # Remove small objects
    cleaned = morphology.remove_small_objects(binary_image, min_size=min_size)
    
    # Label connected components
    labeled = measure.label(cleaned)
    
    # Get region properties
    regions = measure.regionprops(labeled)
    
    return len(regions), regions

def measure_objects(image, min_size=50):
    """
    Measure objects in image
    Returns list of measurements including area, perimeter, intensity, etc.
    """
    gray = convert_to_grayscale(image)
    binary = threshold_image(image)
    
    count, regions = count_objects(binary, min_size=min_size)
    
    measurements = []
    for region in regions:
        measurements.append({
            'area': region.area,
            'perimeter': region.perimeter,
            'centroid': region.centroid,
            'eccentricity': region.eccentricity,
            'mean_intensity': region.mean_intensity,
            'bbox': region.bbox,
            'equivalent_diameter': region.equivalent_diameter
        })
    
    return measurements

def detect_cells(image, min_size=100, max_size=10000):
    """
    Detect cells in microscopy images
    Returns count and cell properties
    """
    measurements = measure_objects(image, min_size=min_size)
    
    # Filter by size
    cells = [m for m in measurements if min_size <= m['area'] <= max_size]
    
    return len(cells), cells

def calculate_intensity_profile(image, start_point, end_point):
    """Calculate intensity profile along a line"""
    from skimage import measure
    gray = convert_to_grayscale(image)
    
    # Get line profile
    profile = measure.profile_line(gray, start_point, end_point)
    
    return profile

def add_scale_bar(image, scale_bar_length_um, pixels_per_um, 
                   position='bottom-right', color=(255, 255, 255)):
    """
    Add scale bar to image
    
    Args:
        image: Input image array
        scale_bar_length_um: Length of scale bar in micrometers
        pixels_per_um: Pixels per micrometer
        position: Position of scale bar ('bottom-right', 'bottom-left', etc.)
        color: RGB color tuple for scale bar
    """
    img_copy = image.copy()
    height, width = img_copy.shape[:2]
    
    # Calculate scale bar length in pixels
    bar_length_px = int(scale_bar_length_um * pixels_per_um)
    bar_height = max(5, height // 100)
    margin = 20
    
    # Determine position
    if 'bottom' in position:
        y_start = height - margin - bar_height
    else:
        y_start = margin
    
    if 'right' in position:
        x_start = width - margin - bar_length_px
    else:
        x_start = margin
    
    # Draw scale bar
    img_copy[y_start:y_start+bar_height, x_start:x_start+bar_length_px] = color
    
    return img_copy

def analyze_fluorescence(image, channel=None):
    """
    Analyze fluorescence intensity in image
    
    Args:
        image: Input image (can be multi-channel)
        channel: Channel to analyze (0, 1, 2 for RGB or None for all)
    
    Returns:
        Dictionary with statistics
    """
    if channel is not None and len(image.shape) == 3:
        img = image[:, :, channel]
    else:
        img = convert_to_grayscale(image)
    
    stats = {
        'mean': float(np.mean(img)),
        'std': float(np.std(img)),
        'min': float(np.min(img)),
        'max': float(np.max(img)),
        'median': float(np.median(img)),
        'total_intensity': float(np.sum(img))
    }
    
    return stats
