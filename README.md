# Fake Job Posting Detection System

This project implements a machine learning system to detect fraudulent job postings based on the research paper "Online Recruitment Fraud (ORF) Detection Using Deep Learning Approaches".

## Overview

Online recruitment fraud is a significant issue in cybercrime, with scammers creating fraudulent job postings to exploit job seekers. This project aims to detect such fake job postings using transformer-based deep learning models (BERT/RoBERTa) and address the class imbalance problem using SMOTE variants.

## Features

- Data preprocessing and cleaning for job posting text
- Exploratory Data Analysis (EDA) to understand patterns in fraudulent job postings
- Implementation of transformer-based models (BERT/RoBERTa) for classification
- Handling class imbalance using SMOTE variants
- Evaluation using multiple metrics (accuracy, balanced accuracy, recall, F1-score, etc.)
- Web interface for real-time job posting fraud detection

## Project Structure

```
fake_job_detector/
├── data/                  # Dataset storage
├── models/                # Trained models
├── notebooks/             # Jupyter notebooks for analysis
├── utils/                 # Utility functions
├── requirements.txt       # Dependencies
└── README.md              # Project documentation
```

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/fake_job_detector.git
cd fake_job_detector
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Data Collection

The system uses job postings from three sources:
- Fake Job Postings dataset
- US Job Postings dataset
- Pakistan Job Postings dataset

You can download these datasets from Kaggle:
- [Fake Job Postings](https://www.kaggle.com/shivamb/real-or-fake-fakejobposting-prediction)
- [US Job Postings](https://www.kaggle.com/datasets/promptcloud/indeed-job-posting-dataset)
- [Pakistan Job Postings](https://www.kaggle.com/datasets/zusmani/pakistans-job-market)

### Training

To train the model:
```bash
python train.py --model bert --smote smobd
```

### Evaluation

To evaluate the model:
```bash
python evaluate.py --model_path models/bert_smobd.pkl
```

### Web Interface

To run the web interface:
```bash
streamlit run app.py
```

## Results

The BERT model with SMOBD SMOTE variant achieved the highest balanced accuracy and recall of about 90%, significantly outperforming models trained on imbalanced data.

## References

1. Akram, N., Irfan, R., Al-Shamayleh, A. S., Kousar, A., Qaddos, A., Imran, M., & Akhunzada, A. (2024). Online Recruitment Fraud (ORF) Detection Using Deep Learning Approaches. IEEE Access.

## License

This project is licensed under the MIT License - see the LICENSE file for details. 