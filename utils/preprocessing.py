import re
import pandas as pd
import neattext as nt
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
import nltk

# Download necessary NLTK resources
try:
    nltk.data.find('tokenizers/punkt')
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('punkt')
    nltk.download('stopwords')

def clean_text(text):
    """
    Clean job posting text by removing HTML tags, URLs, emails, special characters, etc.
    
    Args:
        text (str): Raw job posting text
        
    Returns:
        str: Cleaned text
    """
    if not isinstance(text, str):
        return ""
    
    # Convert to lowercase
    text = text.lower()
    
    # Remove HTML tags
    text = re.sub(r'<.*?>', '', text)
    
    # Remove URLs
    text = re.sub(r'http\S+|www\S+|https\S+', '', text)
    
    # Remove email addresses
    text = re.sub(r'\S+@\S+', '', text)
    
    # Remove special characters and numbers
    text = re.sub(r'[^\w\s]', '', text)
    text = re.sub(r'\d+', '', text)
    
    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()
    
    return text

def remove_stopwords(text):
    """
    Remove stopwords from text
    
    Args:
        text (str): Input text
        
    Returns:
        str: Text with stopwords removed
    """
    stop_words = set(stopwords.words('english'))
    word_tokens = word_tokenize(text)
    filtered_text = [word for word in word_tokens if word not in stop_words]
    return ' '.join(filtered_text)

def preprocess_job_content(df, text_column):
    """
    Preprocess job content by cleaning text and removing stopwords
    
    Args:
        df (pandas.DataFrame): DataFrame containing job postings
        text_column (str): Name of the column containing job text
        
    Returns:
        pandas.DataFrame: DataFrame with preprocessed text
    """
    # Create a copy to avoid modifying the original DataFrame
    df_processed = df.copy()
    
    # Clean text
    df_processed['cleaned_text'] = df_processed[text_column].apply(clean_text)
    
    # Remove stopwords
    df_processed['processed_text'] = df_processed['cleaned_text'].apply(remove_stopwords)
    
    return df_processed

def combine_text_features(df, text_columns):
    """
    Combine multiple text columns into a single 'job_content' column
    
    Args:
        df (pandas.DataFrame): DataFrame containing job postings
        text_columns (list): List of column names to combine
        
    Returns:
        pandas.DataFrame: DataFrame with combined text column
    """
    # Create a copy to avoid modifying the original DataFrame
    df_combined = df.copy()
    
    # Combine text columns
    df_combined['job_content'] = df_combined[text_columns].apply(
        lambda row: ' '.join([str(val) for val in row if isinstance(val, str)]), axis=1
    )
    
    return df_combined

def prepare_dataset(fake_jobs_path, us_jobs_path, pakistan_jobs_path):
    """
    Prepare the combined dataset from three sources
    
    Args:
        fake_jobs_path (str): Path to the Fake Job Postings dataset
        us_jobs_path (str): Path to the US Job Postings dataset
        pakistan_jobs_path (str): Path to the Pakistan Job Postings dataset
        
    Returns:
        pandas.DataFrame: Combined and preprocessed dataset
    """
    # Load datasets
    fake_jobs_df = pd.read_csv(fake_jobs_path)
    us_jobs_df = pd.read_csv(us_jobs_path)
    pakistan_jobs_df = pd.read_csv(pakistan_jobs_path)
    
    # Extract relevant columns from each dataset
    fake_jobs_text_cols = ['title', 'company_profile', 'description', 'requirements', 'benefits']
    us_jobs_text_cols = ["Job Title","Job Requirements", "Company Name"]
    pakistan_jobs_text_cols = ["Job Name","JD","Company Name"]
    
    # Combine text columns for each dataset
    fake_jobs_df = combine_text_features(fake_jobs_df, fake_jobs_text_cols)
    us_jobs_df = combine_text_features(us_jobs_df, us_jobs_text_cols)
    pakistan_jobs_df = combine_text_features(pakistan_jobs_df, pakistan_jobs_text_cols)
    
    # Add fraudulent label
    fake_jobs_df['fraudulent'] = fake_jobs_df['fraudulent'].astype(int)  # Already has this column
    us_jobs_df['fraudulent'] = 0  # Assuming all US jobs are legitimate
    pakistan_jobs_df['fraudulent'] = 0  # Assuming all Pakistan jobs are legitimate
    
    # Keep only necessary columns
    fake_jobs_df = fake_jobs_df[['description', 'fraudulent']]
    us_jobs_df = us_jobs_df[['Job Description', 'fraudulent']]
    pakistan_jobs_df = pakistan_jobs_df[['JD', 'fraudulent']]
    
    # Combine all datasets
    combined_df = pd.concat([fake_jobs_df, us_jobs_df, pakistan_jobs_df], ignore_index=True)
    
    # Preprocess the combined dataset
    combined_df = preprocess_job_content(combined_df, 'job_content')
    
    # Remove duplicates
    combined_df.drop_duplicates(subset=['processed_text'], inplace=True)
    
    # Remove rows with empty text
    combined_df = combined_df[combined_df['processed_text'].str.strip().astype(bool)]
    
    return combined_df 