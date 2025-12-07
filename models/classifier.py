import joblib
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.linear_model import SGDClassifier
import logging
from typing import Dict, Any

# Configure logging 
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class JobClassifier:
    def __init__(self, model_path: str = "models/sgd_classifier.joblib", 
                 vectorizer_path: str = "models/count_vectorizer.joblib"):
        """Initialize the classifier with pre-trained model and vectorizer"""
        try:
            self.model = joblib.load(model_path)
            self.vectorizer = joblib.load(vectorizer_path)
            logger.info("Model and vectorizer loaded successfully")
        except Exception as e:
            logger.error(f"Error loading model or vectorizer: {e}")
            raise

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict if a job posting is fraudulent
        
        Args:
            text (str): Job posting text
            
        Returns:
            dict: Prediction results including prediction and confidence
        """
        try:
            # Transform text using the vectorizer
            X = self.vectorizer.transform([text])
            
            # Get prediction and probability
            prediction = bool(self.model.predict(X)[0])
            probabilities = self.model.predict_proba(X)[0]
            confidence = float(probabilities[1] if prediction else probabilities[0])
            
            # Get feature importance for explanation
            feature_names = self.vectorizer.get_feature_names_out()
            coef = self.model.coef_[0]
            
            # Get top contributing words
            if prediction:
                # For fraudulent prediction, look at positive coefficients
                top_indices = np.argsort(coef)[-5:]
            else:
                # For legitimate prediction, look at negative coefficients
                top_indices = np.argsort(coef)[:5]
            
            important_words = [feature_names[i] for i in top_indices]
            
            return {
                "prediction": prediction,
                "confidence": round(confidence * 100, 2),
                "is_fake": prediction,
                "important_words": important_words,
                "reasoning": self._generate_reasoning(prediction, important_words)
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            return {
                "prediction": None,
                "confidence": 0,
                "is_fake": None,
                "important_words": [],
                "reasoning": "Error making prediction"
            }

    def _generate_reasoning(self, prediction: bool, important_words: list) -> str:
        """Generate reasoning based on prediction and important words"""
        if prediction:
            return f"This job posting appears to be fraudulent based on suspicious terms like: {', '.join(important_words)}"
        else:
            return f"This appears to be a legitimate job posting based on professional terms like: {', '.join(important_words)}" 