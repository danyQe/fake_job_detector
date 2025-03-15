import torch
import torch.nn as nn
import numpy as np
from transformers import PreTrainedTokenizerFast
from tokenizers import Tokenizer, models, normalizers, pre_tokenizers, trainers
from sklearn.model_selection import train_test_split
from .evaluation import calculate_metrics
from tqdm import tqdm

class BPETokenizer:
    """
    Byte-Pair Encoding (BPE) tokenizer implementation
    """
    def __init__(self, vocab_size=30000):
        self.vocab_size = vocab_size
        self.tokenizer = None
        
    def train(self, texts):
        """
        Train BPE tokenizer on input texts
        
        Args:
            texts (list): List of input texts
        """
        # Initialize a BPE tokenizer
        tokenizer = Tokenizer(models.BPE())
        
        # Add normalizer
        tokenizer.normalizer = normalizers.Sequence([
            normalizers.NFD(),
            normalizers.Lowercase(),
            normalizers.StripAccents()
        ])
        
        # Add pre-tokenizer
        tokenizer.pre_tokenizer = pre_tokenizers.Sequence([
            pre_tokenizers.WhitespaceSplit(),
            pre_tokenizers.Punctuation(),
            pre_tokenizers.Digits(individual_digits=True)
        ])
        
        # Initialize trainer
        trainer = trainers.BpeTrainer(
            vocab_size=self.vocab_size,
            special_tokens=["[PAD]", "[UNK]", "[CLS]", "[SEP]", "[MASK]"]
        )
        
        # Train the tokenizer
        tokenizer.train_from_iterator(texts, trainer=trainer)
        
        # Convert to PreTrainedTokenizerFast for compatibility with transformers
        self.tokenizer = PreTrainedTokenizerFast(
            tokenizer_object=tokenizer,
            pad_token="[PAD]",
            cls_token="[CLS]",
            sep_token="[SEP]",
            mask_token="[MASK]"
        )
    
    def tokenize(self, texts):
        """
        Tokenize input texts
        
        Args:
            texts (list): List of input texts
            
        Returns:
            dict: Dictionary containing input_ids and attention_mask
        """
        if self.tokenizer is None:
            raise ValueError("Tokenizer not trained. Call train() first.")
        
        return self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )

class FakeJobDetectionAlgorithm:
    """
    Implementation of the fake job detection algorithm
    """
    def __init__(self, model_type='bert', embedding_dim=768, num_layers=12,
                 vocab_size=30000, batch_size=32, learning_rate=2e-5,
                 num_epochs=4, device=None):
        self.model_type = model_type
        self.embedding_dim = embedding_dim
        self.num_layers = num_layers
        self.vocab_size = vocab_size
        self.batch_size = batch_size
        self.learning_rate = learning_rate
        self.num_epochs = num_epochs
        
        # Set device
        if device is None:
            self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        else:
            self.device = torch.device(device)
        
        # Initialize BPE tokenizer
        self.tokenizer = BPETokenizer(vocab_size=vocab_size)
        
        # Initialize model components
        self.initialize_model()
        
    def initialize_model(self):
        """Initialize model components based on the algorithm"""
        from .model import JobFraudDetector
        self.model = JobFraudDetector(
            model_type=self.model_type,
            dropout_rate=0.3
        ).to(self.device)
        
        self.criterion = nn.BCELoss()
        self.optimizer = torch.optim.AdamW(
            self.model.parameters(),
            lr=self.learning_rate
        )
    
    def preprocess_data(self, X, y=None):
        """
        Preprocess input data according to the algorithm
        
        Args:
            X (list): List of input texts
            y (array-like): Labels (optional)
            
        Returns:
            tuple: Preprocessed features and labels
        """
        # Train tokenizer if not trained
        if self.tokenizer.tokenizer is None:
            self.tokenizer.train(X)
        
        # Tokenize input texts
        features = self.tokenizer.tokenize(X)
        
        if y is not None:
            labels = torch.tensor(y, dtype=torch.float32)
            return features, labels
        return features
    
    def create_data_loader(self, features, labels=None, shuffle=True):
        """Create PyTorch DataLoader"""
        if labels is None:
            labels = torch.zeros(len(features['input_ids']))
        
        dataset = torch.utils.data.TensorDataset(
            features['input_ids'],
            features['attention_mask'],
            labels
        )
        
        return torch.utils.data.DataLoader(
            dataset,
            batch_size=self.batch_size,
            shuffle=shuffle
        )
    
    def train(self, X, y):
        """
        Train the model following the algorithm
        
        Args:
            X (list): List of input texts
            y (array-like): Labels
            
        Returns:
            dict: Training metrics
        """
        # Preprocess data
        features, labels = self.preprocess_data(X, y)
        
        # Create data loader
        train_loader = self.create_data_loader(features, labels)
        
        # Training loop
        self.model.train()
        metrics_history = []
        
        for epoch in range(self.num_epochs):
            print(f"Epoch {epoch + 1}/{self.num_epochs}")
            running_loss = 0.0
            all_preds = []
            all_labels = []
            
            progress_bar = tqdm(train_loader, desc=f"Training")
            for batch in progress_bar:
                # Get batch data
                input_ids, attention_mask, batch_labels = [
                    b.to(self.device) for b in batch
                ]
                batch_labels = batch_labels.view(-1, 1)
                
                # Zero gradients
                self.optimizer.zero_grad()
                
                # Forward pass
                outputs = self.model(input_ids, attention_mask)
                
                # Compute loss
                loss = self.criterion(outputs, batch_labels)
                
                # Backward pass and optimization
                loss.backward()
                self.optimizer.step()
                
                # Update statistics
                running_loss += loss.item()
                all_preds.extend((outputs >= 0.5).float().cpu().numpy())
                all_labels.extend(batch_labels.cpu().numpy())
                
                # Update progress bar
                progress_bar.set_postfix({'loss': running_loss / (progress_bar.n + 1)})
            
            # Calculate epoch metrics
            epoch_metrics = calculate_metrics(
                np.array(all_labels).flatten(),
                np.array(all_preds).flatten()
            )
            metrics_history.append(epoch_metrics)
            
            print(f"Epoch {epoch + 1} metrics:")
            for metric, value in epoch_metrics.items():
                if isinstance(value, dict):
                    continue
                print(f"{metric}: {value:.4f}")
            print()
        
        return metrics_history[-1]  # Return final epoch metrics
    
    def predict(self, X):
        """
        Make predictions following the algorithm
        
        Args:
            X (list): List of input texts
            
        Returns:
            numpy.ndarray: Predicted labels
        """
        # Preprocess data
        features = self.preprocess_data(X)
        
        # Create data loader
        data_loader = self.create_data_loader(features, shuffle=False)
        
        # Make predictions
        self.model.eval()
        predictions = []
        
        with torch.no_grad():
            for batch in data_loader:
                input_ids, attention_mask, _ = [b.to(self.device) for b in batch]
                outputs = self.model(input_ids, attention_mask)
                predictions.extend((outputs >= 0.5).float().cpu().numpy())
        
        return np.array(predictions).flatten().astype(int)
    
    def evaluate(self, X, y):
        """
        Evaluate the model following the algorithm
        
        Args:
            X (list): List of input texts
            y (array-like): True labels
            
        Returns:
            dict: Evaluation metrics
        """
        predictions = self.predict(X)
        return calculate_metrics(y, predictions)
    
    def save(self, path):
        """Save the model and tokenizer"""
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'tokenizer': self.tokenizer.tokenizer,
            'model_type': self.model_type,
            'embedding_dim': self.embedding_dim,
            'num_layers': self.num_layers,
            'vocab_size': self.vocab_size
        }, path)
    
    def load(self, path):
        """Load a saved model and tokenizer"""
        checkpoint = torch.load(path, map_location=self.device)
        
        # Load model parameters
        self.model_type = checkpoint['model_type']
        self.embedding_dim = checkpoint['embedding_dim']
        self.num_layers = checkpoint['num_layers']
        self.vocab_size = checkpoint['vocab_size']
        
        # Reinitialize model and load state
        self.initialize_model()
        self.model.load_state_dict(checkpoint['model_state_dict'])
        
        # Load tokenizer
        self.tokenizer.tokenizer = checkpoint['tokenizer'] 