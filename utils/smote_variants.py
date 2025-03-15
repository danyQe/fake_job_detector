import numpy as np
from sklearn.neighbors import NearestNeighbors
from imblearn.over_sampling import SMOTE, BorderlineSMOTE, SVMSMOTE, ADASYN
from imblearn.combine import SMOTETomek
import random

class SMOBDSmote:
    """
    Implementation of SMOBD SMOTE (Synthetic Minority Over-sampling Technique with Borderline Density)
    
    This variant considers density and distribution of data points that are close to the actual 
    distribution of the data for the synthesis of new data points.
    """
    def __init__(self, k_neighbors=5, random_state=42):
        self.k_neighbors = k_neighbors
        self.random_state = random_state
        
    def fit_resample(self, X, y):
        # Identify minority and majority classes
        unique_classes, class_counts = np.unique(y, return_counts=True)
        minority_class = unique_classes[np.argmin(class_counts)]
        majority_class = unique_classes[np.argmax(class_counts)]
        
        # Get indices of minority and majority samples
        minority_indices = np.where(y == minority_class)[0]
        majority_indices = np.where(y == majority_class)[0]
        
        X_minority = X[minority_indices]
        X_majority = X[majority_indices]
        
        # Find borderline samples
        nn = NearestNeighbors(n_neighbors=self.k_neighbors+1)
        nn.fit(X)
        
        # For each minority sample, find its k nearest neighbors
        distances, indices = nn.kneighbors(X_minority)
        
        # Identify borderline samples (minority samples with at least 50% majority neighbors)
        borderline_indices = []
        for i, idx_array in enumerate(indices):
            # Skip the first index as it's the sample itself
            neighbor_classes = [y[idx] for idx in idx_array[1:]]
            majority_count = sum(1 for c in neighbor_classes if c == majority_class)
            
            # If more than half of neighbors are from majority class, it's a borderline sample
            if majority_count > self.k_neighbors / 2:
                borderline_indices.append(i)
        
        # If no borderline samples found, use regular SMOTE
        if not borderline_indices:
            smote = SMOTE(random_state=self.random_state)
            return smote.fit_resample(X, y)
        
        # Get borderline minority samples
        X_borderline = X_minority[borderline_indices]
        
        # Calculate density around each borderline sample
        densities = []
        for i in range(len(X_borderline)):
            # Calculate average distance to k nearest neighbors
            avg_distance = np.mean(distances[borderline_indices[i]][1:])
            densities.append(1.0 / (avg_distance + 1e-10))  # Avoid division by zero
        
        # Normalize densities
        total_density = sum(densities)
        if total_density > 0:
            densities = [d / total_density for d in densities]
        else:
            densities = [1.0 / len(densities)] * len(densities)
        
        # Determine number of synthetic samples to generate
        n_samples = len(X_majority) - len(X_minority)
        
        # Generate synthetic samples
        synthetic_samples = []
        synthetic_labels = []
        
        for _ in range(n_samples):
            # Select a borderline sample based on density
            idx = np.random.choice(len(X_borderline), p=densities)
            sample = X_borderline[idx]
            
            # Find k nearest neighbors of the selected sample
            nn_idx = indices[borderline_indices[idx]][1:]
            nn_minority_idx = [i for i in nn_idx if y[i] == minority_class]
            
            if not nn_minority_idx:
                continue
            
            # Select a random neighbor from minority class
            neighbor_idx = np.random.choice(nn_minority_idx)
            neighbor = X[neighbor_idx]
            
            # Generate synthetic sample
            alpha = np.random.random()
            synthetic_sample = sample + alpha * (neighbor - sample)
            
            synthetic_samples.append(synthetic_sample)
            synthetic_labels.append(minority_class)
        
        # Combine original and synthetic samples
        if synthetic_samples:
            X_resampled = np.vstack([X, np.array(synthetic_samples)])
            y_resampled = np.hstack([y, np.array(synthetic_labels)])
        else:
            X_resampled = X
            y_resampled = y
        
        return X_resampled, y_resampled

class GSmote:
    """
    Implementation of G-SMOTE (Geometric SMOTE)
    
    This variant defines a safe area to ensure that no noisy data instance is synthesized.
    Its objective is to generate diverse minority class instances to prevent intra-cluster skewness.
    """
    def __init__(self, k_neighbors=5, selection_strategy='combined', truncation_factor=1.0, random_state=42):
        self.k_neighbors = k_neighbors
        self.selection_strategy = selection_strategy
        self.truncation_factor = truncation_factor
        self.random_state = random_state
        
    def fit_resample(self, X, y):
        # Identify minority and majority classes
        unique_classes, class_counts = np.unique(y, return_counts=True)
        minority_class = unique_classes[np.argmin(class_counts)]
        
        # Get indices of minority samples
        minority_indices = np.where(y == minority_class)[0]
        X_minority = X[minority_indices]
        
        # Determine number of synthetic samples to generate
        n_minority = len(X_minority)
        n_majority = len(y) - n_minority
        n_samples = n_majority - n_minority
        
        if n_samples <= 0:
            return X, y
        
        # Find k nearest neighbors for each minority sample
        nn = NearestNeighbors(n_neighbors=self.k_neighbors+1)
        nn.fit(X)
        distances, indices = nn.kneighbors(X_minority)
        
        # Generate synthetic samples
        synthetic_samples = []
        synthetic_labels = []
        
        for _ in range(n_samples):
            # Select a random minority sample
            idx = np.random.randint(0, n_minority)
            sample = X_minority[idx]
            
            # Select a neighbor based on the selection strategy
            if self.selection_strategy == 'minority':
                valid_neighbors = [i for i, idx in enumerate(indices[idx][1:]) 
                                  if y[idx] == minority_class]
            elif self.selection_strategy == 'majority':
                valid_neighbors = [i for i, idx in enumerate(indices[idx][1:]) 
                                  if y[idx] != minority_class]
            else:  # 'combined'
                valid_neighbors = list(range(len(indices[idx][1:])))
            
            if not valid_neighbors:
                continue
            
            neighbor_idx = np.random.choice(valid_neighbors)
            neighbor = X[indices[idx][1:][neighbor_idx]]
            
            # Generate synthetic sample using geometric approach
            alpha = np.random.random() * 2 - 1  # Between -1 and 1
            
            # Apply truncation factor
            if alpha < 0:
                alpha = max(alpha, -self.truncation_factor)
            else:
                alpha = min(alpha, self.truncation_factor)
            
            # Generate synthetic sample
            synthetic_sample = sample + alpha * (neighbor - sample)
            
            synthetic_samples.append(synthetic_sample)
            synthetic_labels.append(minority_class)
        
        # Combine original and synthetic samples
        if synthetic_samples:
            X_resampled = np.vstack([X, np.array(synthetic_samples)])
            y_resampled = np.hstack([y, np.array(synthetic_labels)])
        else:
            X_resampled = X
            y_resampled = y
        
        return X_resampled, y_resampled

def get_smote_variant(variant_name, random_state=42):
    """
    Get the specified SMOTE variant
    
    Args:
        variant_name (str): Name of the SMOTE variant
        random_state (int): Random seed for reproducibility
        
    Returns:
        object: SMOTE variant object
    """
    variants = {
        'smote': SMOTE(random_state=random_state),
        'borderline_smote': BorderlineSMOTE(random_state=random_state),
        'svm_smote': SVMSMOTE(random_state=random_state),
        'adasyn': ADASYN(random_state=random_state),
        'smote_tomek': SMOTETomek(random_state=random_state),
        'smobd_smote': SMOBDSmote(random_state=random_state),
        'g_smote': GSmote(random_state=random_state)
    }
    
    if variant_name.lower() not in variants:
        raise ValueError(f"Unknown SMOTE variant: {variant_name}. Available variants: {list(variants.keys())}")
    
    return variants[variant_name.lower()] 