"""
Data analysis utilities for quantification and statistics
"""

import numpy as np
import pandas as pd
from scipy import stats
import json

def calculate_basic_stats(values):
    """Calculate basic statistical measures"""
    values = np.array(values)
    
    return {
        'n': len(values),
        'mean': float(np.mean(values)),
        'std': float(np.std(values, ddof=1)),
        'sem': float(stats.sem(values)),
        'median': float(np.median(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'q25': float(np.percentile(values, 25)),
        'q75': float(np.percentile(values, 75)),
        'cv': float(np.std(values, ddof=1) / np.mean(values) * 100) if np.mean(values) != 0 else 0
    }

def ttest(group1, group2, paired=False):
    """Perform t-test between two groups"""
    if paired:
        statistic, pvalue = stats.ttest_rel(group1, group2)
    else:
        statistic, pvalue = stats.ttest_ind(group1, group2)
    
    return {
        'statistic': float(statistic),
        'pvalue': float(pvalue),
        'significant': pvalue < 0.05,
        'test_type': 'paired_ttest' if paired else 'independent_ttest'
    }

def anova(*groups):
    """Perform one-way ANOVA"""
    statistic, pvalue = stats.f_oneway(*groups)
    
    return {
        'f_statistic': float(statistic),
        'pvalue': float(pvalue),
        'significant': pvalue < 0.05,
        'num_groups': len(groups)
    }

def correlation(x, y, method='pearson'):
    """Calculate correlation between two variables"""
    if method == 'pearson':
        coef, pvalue = stats.pearsonr(x, y)
    elif method == 'spearman':
        coef, pvalue = stats.spearmanr(x, y)
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return {
        'coefficient': float(coef),
        'pvalue': float(pvalue),
        'significant': pvalue < 0.05,
        'method': method
    }

def linear_regression(x, y):
    """Perform linear regression"""
    slope, intercept, r_value, p_value, std_err = stats.linregress(x, y)
    
    # Calculate predicted values and residuals
    y_pred = slope * np.array(x) + intercept
    residuals = np.array(y) - y_pred
    
    return {
        'slope': float(slope),
        'intercept': float(intercept),
        'r_squared': float(r_value ** 2),
        'pvalue': float(p_value),
        'std_err': float(std_err),
        'residuals': residuals.tolist()
    }

def normalize_data(values, method='minmax'):
    """
    Normalize data
    
    Args:
        values: Array of values
        method: 'minmax', 'zscore', or 'robust'
    """
    values = np.array(values)
    
    if method == 'minmax':
        min_val = np.min(values)
        max_val = np.max(values)
        normalized = (values - min_val) / (max_val - min_val) if max_val != min_val else values
    elif method == 'zscore':
        normalized = (values - np.mean(values)) / np.std(values)
    elif method == 'robust':
        median = np.median(values)
        mad = np.median(np.abs(values - median))
        normalized = (values - median) / mad if mad != 0 else values
    else:
        raise ValueError(f"Unknown normalization method: {method}")
    
    return normalized.tolist()

def detect_outliers(values, method='iqr', threshold=1.5):
    """
    Detect outliers in data
    
    Args:
        values: Array of values
        method: 'iqr' (Interquartile Range) or 'zscore'
        threshold: Threshold for outlier detection
    """
    values = np.array(values)
    
    if method == 'iqr':
        q1 = np.percentile(values, 25)
        q3 = np.percentile(values, 75)
        iqr = q3 - q1
        lower_bound = q1 - threshold * iqr
        upper_bound = q3 + threshold * iqr
        outliers = (values < lower_bound) | (values > upper_bound)
    elif method == 'zscore':
        z_scores = np.abs((values - np.mean(values)) / np.std(values))
        outliers = z_scores > threshold
    else:
        raise ValueError(f"Unknown method: {method}")
    
    return {
        'outlier_indices': np.where(outliers)[0].tolist(),
        'outlier_values': values[outliers].tolist(),
        'num_outliers': int(np.sum(outliers))
    }

def fold_change_analysis(control, treatment):
    """
    Calculate fold change between control and treatment
    
    Args:
        control: Control values
        treatment: Treatment values
    """
    control = np.array(control)
    treatment = np.array(treatment)
    
    mean_control = np.mean(control)
    mean_treatment = np.mean(treatment)
    
    if mean_control == 0:
        return {'error': 'Control mean is zero'}
    
    fold_change = mean_treatment / mean_control
    log2_fc = np.log2(fold_change)
    
    # Perform t-test
    ttest_result = ttest(control, treatment)
    
    return {
        'control_mean': float(mean_control),
        'treatment_mean': float(mean_treatment),
        'fold_change': float(fold_change),
        'log2_fold_change': float(log2_fc),
        'upregulated': fold_change > 1,
        'pvalue': ttest_result['pvalue'],
        'significant': ttest_result['significant']
    }

def calculate_ic50(concentrations, responses, method='log'):
    """
    Calculate IC50 from dose-response data
    
    Args:
        concentrations: Array of concentrations
        responses: Array of responses (0-100%)
        method: 'log' or 'linear'
    """
    from scipy.optimize import curve_fit
    
    concentrations = np.array(concentrations)
    responses = np.array(responses)
    
    if method == 'log':
        # Log-transform concentrations
        log_conc = np.log10(concentrations)
        
        # Sigmoid function
        def sigmoid(x, bottom, top, ic50, hill):
            return bottom + (top - bottom) / (1 + 10**((ic50 - x) * hill))
        
        try:
            # Fit curve
            popt, pcov = curve_fit(sigmoid, log_conc, responses, 
                                  p0=[0, 100, np.median(log_conc), 1],
                                  maxfev=10000)
            
            bottom, top, log_ic50, hill = popt
            ic50 = 10 ** log_ic50
            
            # Calculate R-squared
            residuals = responses - sigmoid(log_conc, *popt)
            ss_res = np.sum(residuals**2)
            ss_tot = np.sum((responses - np.mean(responses))**2)
            r_squared = 1 - (ss_res / ss_tot)
            
            return {
                'ic50': float(ic50),
                'log_ic50': float(log_ic50),
                'hill_slope': float(hill),
                'bottom': float(bottom),
                'top': float(top),
                'r_squared': float(r_squared)
            }
        except Exception as e:
            return {'error': f'Curve fitting failed: {str(e)}'}
    
    return {'error': 'Method not implemented'}

def batch_analysis(data, group_column, value_column):
    """
    Perform batch analysis on grouped data
    
    Args:
        data: Dictionary or DataFrame with data
        group_column: Column name for grouping
        value_column: Column name for values to analyze
    """
    if isinstance(data, dict):
        df = pd.DataFrame(data)
    else:
        df = data
    
    results = {}
    
    for group in df[group_column].unique():
        group_data = df[df[group_column] == group][value_column].values
        results[str(group)] = calculate_basic_stats(group_data)
    
    return results

def calculate_percent_change(baseline, treatment):
    """Calculate percent change from baseline"""
    baseline = np.array(baseline)
    treatment = np.array(treatment)
    
    percent_change = ((treatment - baseline) / baseline) * 100
    
    return {
        'mean_percent_change': float(np.mean(percent_change)),
        'std_percent_change': float(np.std(percent_change)),
        'individual_changes': percent_change.tolist()
    }
