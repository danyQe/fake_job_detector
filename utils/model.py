import torch
import torch.nn as nn
import numpy as np
from transformers import (
    BertTokenizer, BertModel, 
    RobertaTokenizer, RobertaModel,
    AdamW, get_linear_schedule_with_warmup
)
from sklearn.base import BaseEstimator, ClassifierMixin
from tqdm import tqdm

class JobFraudDetector(nn.Module):
    """
    Neural network model for job fraud detection using BERT/RoBERTa embeddings
    Architecture:
    1. Pre-trained BERT/RoBERTa for contextual embeddings
    2. Span representation layer
    3. Classifier with specific dimensions:
       - Input layer (768)
       - Dropout layer
       - Dense layer (128)
       - Dense layer (32)
       - Sigmoid activation
       - Output layer (0,1)
    """
    def __init__(self, model_type='bert', dropout_rate=0.3):
        """
        Initialize the model
        
        Args:
            model_type (str): Type of transformer model to use ('bert' or 'roberta')
            dropout_rate (float): Dropout rate for regularization
        """
        super(JobFraudDetector, self).__init__()
        
        self.model_type = model_type.lower()
        
        # Load pre-trained transformer model
        if self.model_type == 'bert':
            self.transformer = BertModel.from_pretrained('bert-base-uncased')
            self.hidden_size = 768  # BERT base hidden size
        elif self.model_type == 'roberta':
            self.transformer = RobertaModel.from_pretrained('roberta-base')
            self.hidden_size = 768  # RoBERTa base hidden size
        else:
            raise ValueError(f"Unsupported model type: {model_type}. Use 'bert' or 'roberta'.")
        
        # Classifier layers exactly matching the architecture
        self.classifier = nn.Sequential(
            # Input layer (1 x 768) - Using [CLS] token representation
            nn.Linear(self.hidden_size, 768),
            
            # Dropout layer
            nn.Dropout(dropout_rate),
            
            # Dense layer (1 x 128)
            nn.Linear(768, 128),
            nn.ReLU(),
            
            # Dense layer (1 x 32)
            nn.Linear(128, 32),
            nn.ReLU(),
            
            # Output layer with sigmoid activation
            nn.Linear(32, 1),
            nn.Sigmoid()
        )
        
    def forward(self, input_ids, attention_mask):
        """
        Forward pass through the network
        
        Args:
            input_ids (torch.Tensor): Input token IDs
            attention_mask (torch.Tensor): Attention mask
            
        Returns:
            torch.Tensor: Binary classification output (0,1)
        """
        # Get transformer outputs (contextual vectors E0 to En)
        outputs = self.transformer(
            input_ids=input_ids,
            attention_mask=attention_mask,
            output_hidden_states=True  # Get all hidden states for span representation
        )
        
        # Get the [CLS] token representation (first token)
        cls_output = outputs.pooler_output  # Shape: (batch_size, 768)
        
        # Pass through classifier layers
        output = self.classifier(cls_output)
        
        return output

class TransformerClassifier(BaseEstimator, ClassifierMixin):
    """
    Scikit-learn compatible wrapper for the JobFraudDetector model
    """
    def __init__(self, model_type='bert', max_length=512, batch_size=32, 
                 learning_rate=2e-5, epochs=4, device=None):
        """
        Initialize the classifier
        
        Args:
            model_type (str): Type of transformer model to use ('bert' or 'roberta')
            max_length (int): Maximum sequence length
            batch_size (int): Batch size for training
            learning_rate (float): Learning rate
            epochs (int): Number of training epochs
            device (str): Device to use ('cuda' or 'cpu')
        """
        self.model_type = model_type.lower()
        self.max_length = max_length
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.epochs = epochs
        
        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # Initialize tokenizer
        if self.model_type == 'bert':
            self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        elif self.model_type == 'roberta':
            self.tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
        else:
            raise ValueError(f"Unsupported model type: {model_type}. Use 'bert' or 'roberta'.")
        
        # Initialize model
        self.model = JobFraudDetector(model_type=self.model_type)
        self.model.to(self.device)
        
    def _tokenize_text(self, texts):
        """
        Tokenize text data
        
        Args:
            texts (list): List of text strings
            
        Returns:
            dict: Dictionary containing input_ids and attention_mask
        """
        return self.tokenizer(
            texts,
            padding='max_length',
            truncation=True,
            max_length=self.max_length,
            return_tensors='pt'
        )
    
    def _create_data_loader(self, texts, labels=None, shuffle=True):
        """
        Create a PyTorch DataLoader
        
        Args:
            texts (list): List of text strings
            labels (list): List of labels (optional)
            shuffle (bool): Whether to shuffle the data
            
        Returns:
            torch.utils.data.DataLoader: DataLoader for the dataset
        """
        # Tokenize texts
        encodings = self._tokenize_text(texts)
        
        # Create dataset
        dataset = torch.utils.data.TensorDataset(
            encodings['input_ids'],
            encodings['attention_mask'],
            torch.tensor(labels) if labels is not None else torch.zeros(len(texts))
        )
        
        # Create data loader
        return torch.utils.data.DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=shuffle
        )
    
    def fit(self, X, y):
        """
        Train the model
        
        Args:
            X (list): List of text strings
            y (list): List of labels
            
        Returns:
            self: The trained model
        """
        # Create data loader
        train_loader = self._create_data_loader(X, y)
        
        # Set up optimizer and scheduler
        optimizer = AdamW(self.model.parameters(), lr=self.learning_rate)
        total_steps = len(train_loader) * self.epochs
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=0,
            num_training_steps=total_steps
        )
        
        # Loss function
        criterion = nn.BCELoss()
        
        # Training loop
        self.model.train()
        for epoch in range(self.epochs):
            print(f"Epoch {epoch+1}/{self.epochs}")
            
            running_loss = 0.0
            correct_preds = 0
            total_preds = 0
            
            progress_bar = tqdm(train_loader, desc=f"Epoch {epoch+1}")
            for batch in progress_bar:
                # Get batch data
                input_ids, attention_mask, labels = [b.to(self.device) for b in batch]
                labels = labels.float().view(-1, 1)
                
                # Zero gradients
                optimizer.zero_grad()
                
                # Forward pass
                outputs = self.model(input_ids, attention_mask)
                
                # Calculate loss
                loss = criterion(outputs, labels)
                
                # Backward pass
                loss.backward()
                
                # Update parameters
                optimizer.step()
                scheduler.step()
                
                # Update statistics
                running_loss += loss.item()
                
                # Calculate accuracy
                predictions = (outputs >= 0.5).float()
                correct_preds += (predictions == labels).sum().item()
                total_preds += labels.size(0)
                
                # Update progress bar
                progress_bar.set_postfix({
                    'loss': running_loss / (progress_bar.n + 1),
                    'accuracy': correct_preds / total_preds
                })
        
        return self
    
    def predict(self, X):
        """
        Make predictions
        
        Args:
            X (list): List of text strings
            
        Returns:
            numpy.ndarray: Predicted labels
        """
        # Create data loader
        data_loader = self._create_data_loader(X, shuffle=False)
        
        # Make predictions
        self.model.eval()
        predictions = []
        
        with torch.no_grad():
            for batch in data_loader:
                # Get batch data
                input_ids, attention_mask, _ = [b.to(self.device) for b in batch]
                
                # Forward pass
                outputs = self.model(input_ids, attention_mask)
                
                # Convert to binary predictions
                batch_preds = (outputs >= 0.5).float().cpu().numpy()
                predictions.extend(batch_preds)
        
        return np.array(predictions).flatten().astype(int)
    
    def predict_proba(self, X):
        """
        Predict class probabilities
        
        Args:
            X (list): List of text strings
            
        Returns:
            numpy.ndarray: Predicted probabilities
        """
        # Create data loader
        data_loader = self._create_data_loader(X, shuffle=False)
        
        # Make predictions
        self.model.eval()
        probabilities = []
        
        with torch.no_grad():
            for batch in data_loader:
                # Get batch data
                input_ids, attention_mask, _ = [b.to(self.device) for b in batch]
                
                # Forward pass
                outputs = self.model(input_ids, attention_mask)
                
                # Get probabilities
                batch_probs = outputs.cpu().numpy()
                probabilities.extend(batch_probs)
        
        # Convert to 2D array with probabilities for both classes
        probs_array = np.array(probabilities).flatten()
        return np.vstack((1 - probs_array, probs_array)).T
    
    def save(self, path):
        """
        Save the model
        
        Args:
            path (str): Path to save the model
        """
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'model_type': self.model_type,
            'max_length': self.max_length,
            'batch_size': self.batch_size,
            'learning_rate': self.learning_rate,
            'epochs': self.epochs
        }, path)
    
    @classmethod
    def load(cls, path, device=None):
        """
        Load a saved model
        
        Args:
            path (str): Path to the saved model
            device (str): Device to use ('cuda' or 'cpu')
            
        Returns:
            TransformerClassifier: Loaded model
        """
        # Load checkpoint
        checkpoint = torch.load(path, map_location=torch.device('cpu'))
        
        # Create model
        model = cls(
            model_type=checkpoint['model_type'],
            max_length=checkpoint['max_length'],
            batch_size=checkpoint['batch_size'],
            learning_rate=checkpoint['learning_rate'],
            epochs=checkpoint['epochs'],
            device=device
        )
        
        # Load state dict
        model.model.load_state_dict(checkpoint['model_state_dict'])
        
        return model 