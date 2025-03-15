import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    confusion_matrix, classification_report, roc_curve, auc,
    balanced_accuracy_score
)

def calculate_metrics(y_true, y_pred):
    """
    Calculate various evaluation metrics
    
    Args:
        y_true (array-like): True labels
        y_pred (array-like): Predicted labels
        
    Returns:
        dict: Dictionary containing evaluation metrics
    """
    # Calculate basic metrics
    accuracy = accuracy_score(y_true, y_pred)
    balanced_acc = balanced_accuracy_score(y_true, y_pred)
    precision = precision_score(y_true, y_pred)
    recall = recall_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred)
    
    # Calculate confusion matrix
    tn, fp, fn, tp = confusion_matrix(y_true, y_pred).ravel()
    
    # Calculate specificity (true negative rate)
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0
    
    # Calculate sensitivity (true positive rate, same as recall)
    sensitivity = recall
    
    # Calculate G-mean (geometric mean of sensitivity and specificity)
    g_mean = np.sqrt(sensitivity * specificity)
    
    # Calculate Type I and Type II error rates
    type_i_error = fp / (tn + fp) if (tn + fp) > 0 else 0  # False positive rate
    type_ii_error = fn / (tp + fn) if (tp + fn) > 0 else 0  # False negative rate
    
    return {
        'accuracy': accuracy,
        'balanced_accuracy': balanced_acc,
        'precision': precision,
        'recall': recall,
        'f1_score': f1,
        'specificity': specificity,
        'sensitivity': sensitivity,
        'g_mean': g_mean,
        'type_i_error': type_i_error,
        'type_ii_error': type_ii_error,
        'confusion_matrix': {
            'tn': tn,
            'fp': fp,
            'fn': fn,
            'tp': tp
        }
    }

def plot_confusion_matrix(y_true, y_pred, title='Confusion Matrix'):
    """
    Plot confusion matrix
    
    Args:
        y_true (array-like): True labels
        y_pred (array-like): Predicted labels
        title (str): Title for the plot
    """
    cm = confusion_matrix(y_true, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', 
                xticklabels=['Non-Fraudulent', 'Fraudulent'],
                yticklabels=['Non-Fraudulent', 'Fraudulent'])
    plt.xlabel('Predicted')
    plt.ylabel('True')
    plt.title(title)
    plt.tight_layout()
    
    return plt.gcf()

def plot_roc_curve(y_true, y_prob, title='ROC Curve'):
    """
    Plot ROC curve
    
    Args:
        y_true (array-like): True labels
        y_prob (array-like): Predicted probabilities for the positive class
        title (str): Title for the plot
    """
    fpr, tpr, _ = roc_curve(y_true, y_prob)
    roc_auc = auc(fpr, tpr)
    
    plt.figure(figsize=(8, 6))
    plt.plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC curve (area = {roc_auc:.2f})')
    plt.plot([0, 1], [0, 1], color='navy', lw=2, linestyle='--')
    plt.xlim([0.0, 1.0])
    plt.ylim([0.0, 1.05])
    plt.xlabel('False Positive Rate')
    plt.ylabel('True Positive Rate')
    plt.title(title)
    plt.legend(loc='lower right')
    plt.tight_layout()
    
    return plt.gcf()

def print_classification_report(y_true, y_pred):
    """
    Print classification report
    
    Args:
        y_true (array-like): True labels
        y_pred (array-like): Predicted labels
    """
    report = classification_report(y_true, y_pred, target_names=['Non-Fraudulent', 'Fraudulent'])
    print(report)
    
    return report

def compare_models(models_results, metric='balanced_accuracy'):
    """
    Compare multiple models based on a specific metric
    
    Args:
        models_results (dict): Dictionary with model names as keys and metrics dictionaries as values
        metric (str): Metric to compare models on
        
    Returns:
        matplotlib.figure.Figure: Bar plot comparing models
    """
    model_names = list(models_results.keys())
    metric_values = [results[metric] for results in models_results.values()]
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(model_names, metric_values, color='skyblue')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                 f'{height:.2f}', ha='center', va='bottom')
    
    plt.xlabel('Models')
    plt.ylabel(metric.replace('_', ' ').title())
    plt.title(f'Comparison of Models based on {metric.replace("_", " ").title()}')
    plt.xticks(rotation=45)
    plt.tight_layout()
    
    return plt.gcf()

def plot_metrics_comparison(metrics_dict, title='Model Performance Metrics'):
    """
    Plot multiple metrics for a single model
    
    Args:
        metrics_dict (dict): Dictionary containing metric names and values
        title (str): Title for the plot
        
    Returns:
        matplotlib.figure.Figure: Bar plot of metrics
    """
    # Select metrics to plot (exclude confusion matrix and error rates)
    plot_metrics = {k: v for k, v in metrics_dict.items() 
                   if k not in ['confusion_matrix', 'type_i_error', 'type_ii_error']}
    
    metric_names = list(plot_metrics.keys())
    metric_values = list(plot_metrics.values())
    
    plt.figure(figsize=(12, 6))
    bars = plt.bar(metric_names, metric_values, color='lightgreen')
    
    # Add value labels on top of bars
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                 f'{height:.2f}', ha='center', va='bottom')
    
    plt.xlabel('Metrics')
    plt.ylabel('Value')
    plt.title(title)
    plt.xticks(rotation=45)
    plt.ylim(0, 1.1)  # Metrics are typically between 0 and 1
    plt.tight_layout()
    
    return plt.gcf() 