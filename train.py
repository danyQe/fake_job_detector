import argparse
import os
import pandas as pd
import torch
from sklearn.model_selection import train_test_split
from utils.preprocessing import prepare_dataset
from utils.model import TransformerClassifier
from utils.smote_variants import get_smote_variant
from utils.evaluation import plot_confusion_matrix, plot_roc_curve, print_classification_report
import matplotlib.pyplot as plt

def main(args):
    print("Loading and preparing datasets...")
    
    # Prepare the combined dataset from all three sources
    combined_df = prepare_dataset(
        fake_jobs_path=args.fake_jobs_path,
        us_jobs_path=args.us_jobs_path,
        pakistan_jobs_path=args.pakistan_jobs_path
    )
    
    # Split features and labels
    X = combined_df['processed_text'].values
    y = combined_df['fraudulent'].values
    
    # Split into train and test sets
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    
    # Handle class imbalance using specified SMOTE variant
    if args.smote_variant:
        print(f"Applying {args.smote_variant} to handle class imbalance...")
        smote = get_smote_variant(args.smote_variant)
        X_train_reshaped = X_train.reshape(-1, 1)
        X_train_resampled, y_train_resampled = smote.fit_resample(X_train_reshaped, y_train)
        X_train = X_train_resampled.flatten()
        y_train = y_train_resampled
    
    # Initialize model
    print(f"Initializing {args.model_type} model...")
    model = TransformerClassifier(
        model_type=args.model_type,
        max_length=args.max_length,
        batch_size=args.batch_size,
        learning_rate=args.learning_rate,
        epochs=args.epochs,
        device=args.device
    )
    
    # Train model
    print("Starting training...")
    model.fit(X_train, y_train)
    
    # Evaluate on test set
    print("\nEvaluating model on test set...")
    y_pred = model.predict(X_test)
    y_prob = model.predict_proba(X_test)[:, 1]
    
    # Print classification report
    print("\nClassification Report:")
    print_classification_report(y_test, y_pred)
    
    # Plot confusion matrix
    cm_plot = plot_confusion_matrix(y_test, y_pred)
    cm_plot.savefig(os.path.join(args.output_dir, 'confusion_matrix.png'))
    plt.close()
    
    # Plot ROC curve
    roc_plot = plot_roc_curve(y_test, y_prob)
    roc_plot.savefig(os.path.join(args.output_dir, 'roc_curve.png'))
    plt.close()
    
    # Save model
    os.makedirs(args.output_dir, exist_ok=True)
    model_path = os.path.join(args.output_dir, f'{args.model_type}_model.pt')
    print(f"\nSaving model to {model_path}")
    model.save(model_path)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train fake job detection model")
    
    # Dataset paths
    parser.add_argument("--fake_jobs_path", type=str, default="data/fake_job_postings.csv",
                        help="Path to Fake Job Postings dataset")
    parser.add_argument("--us_jobs_path", type=str, default="data/us_job_postings.csv",
                        help="Path to US Job Postings dataset")
    parser.add_argument("--pakistan_jobs_path", type=str, default="data/pakistan_job_postings.csv",
                        help="Path to Pakistan Job Postings dataset")
    
    # Model parameters
    parser.add_argument("--model_type", type=str, default="bert", choices=["bert", "roberta"],
                        help="Type of transformer model to use")
    parser.add_argument("--max_length", type=int, default=512,
                        help="Maximum sequence length")
    parser.add_argument("--batch_size", type=int, default=32,
                        help="Training batch size")
    parser.add_argument("--learning_rate", type=float, default=2e-5,
                        help="Learning rate")
    parser.add_argument("--epochs", type=int, default=4,
                        help="Number of training epochs")
    
    # SMOTE parameters
    parser.add_argument("--smote_variant", type=str, default="smobd_smote",
                        choices=["smote", "borderline_smote", "svm_smote", "adasyn",
                                "smote_tomek", "smobd_smote", "g_smote"],
                        help="SMOTE variant to use for handling class imbalance")
    
    # Other parameters
    parser.add_argument("--device", type=str, default=None,
                        help="Device to use (cuda or cpu)")
    parser.add_argument("--output_dir", type=str, default="models",
                        help="Directory to save model and results")
    
    args = parser.parse_args()
    main(args) 