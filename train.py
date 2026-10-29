import argparse
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import joblib
import logging
from fake_job_detector.models.ml_classifier import MLJobClassifier
from fake_job_detector.utils.preprocessing import clean_text, remove_stopwords
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import SGDClassifier
from sklearn.metrics import accuracy_score, f1_score

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def train_model():
    """Train and save the SGD classifier model using only text features"""
    try:
        # Load data
        logger.info("Loading dataset...")
        data = pd.read_csv('data/fake_job_postings_cleaned.csv')
        
        # Split features and target - only use text
        X = data[['text']]  # Only use text column
        y = data['fraudulent']
        
        # Split into train and test sets
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.33, random_state=53)
        
        # Create and fit the vectorizer
        logger.info("Creating and fitting vectorizer...")
        vectorizer = CountVectorizer(stop_words='english')
        X_train_vec = vectorizer.fit_transform(X_train)
        X_test_vec = vectorizer.transform(X_test)
        
        # Train SGD classifier
        logger.info("Training SGD classifier...")
        clf = SGDClassifier(
            loss='log_loss',
            max_iter=1000,
            tol=1e-3,
            random_state=53,
            class_weight='balanced'  # Handle class imbalance
        )
        clf.fit(X_train_vec, y_train)
        
        # Evaluate the model
        y_pred = clf.predict(X_test_vec)
        accuracy = accuracy_score(y_test, y_pred)
        f1 = f1_score(y_test, y_pred)
        
        logger.info(f"Model Performance:")
        logger.info(f"Accuracy: {accuracy:.4f}")
        logger.info(f"F1 Score: {f1:.4f}")
        
        # Create models directory if it doesn't exist
        os.makedirs('models', exist_ok=True)
        
        # Save the model and vectorizer
        logger.info("Saving model and vectorizer...")
        joblib.dump(clf, 'models/sgd_classifier.joblib')
        joblib.dump(vectorizer, 'models/count_vectorizer.joblib')
        
        logger.info("Training completed successfully!")
        
        return True
        
    except Exception as e:
        logger.error(f"Error during training: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train a machine learning model for job fraud detection")
    
    parser.add_argument('--data_path', type=str, default='data/fake_job_postings_cleaned.csv',
                        help='Path to the training data')
    parser.add_argument('--model_type', type=str, default='sgd',
                        choices=['sgd'],  # Only allow SGD classifier
                        help='Type of model to train')
    parser.add_argument('--test_size', type=float, default=0.33,
                        help='Proportion of data to use for testing')
    parser.add_argument('--random_state', type=int, default=53,
                        help='Random seed for reproducibility')
    parser.add_argument('--output_dir', type=str, default='models',
                        help='Directory to save the trained model')
    
    args = parser.parse_args()

    train_model()