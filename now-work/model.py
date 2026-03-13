import torch
from transformers import BertTokenizer, BertModel
import numpy as np
import pandas as pd

class EssayScorer:
    def __init__(self, model_dir='output'):
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        print(f"Using device: {self.device}")
        
        self.tokenizer = BertTokenizer.from_pretrained('bert-base-uncased')
        
        self.score_ranges = {
            1: (2, 12),
            2: (1, 6),
            3: (0, 3),
            4: (0, 3),
            5: (0, 4),
            6: (0, 4),
            7: (2, 24),
            8: (10, 60)
        }
        
        # Load single model trained on all sets
        model_path = f'{model_dir}/best_model.pt'
        self.model = self._load_model(model_path)
        
        # Load normalization params
        import json
        with open(f'{model_dir}/score_params.json', 'r') as f:
            params = json.load(f)
        self.score_means = {int(k): v for k, v in params['means'].items()}
        self.score_stds = {int(k): v for k, v in params['stds'].items()}
        
    def _load_model(self, model_path):
        model = BertEssayScorer()
        model.load_state_dict(torch.load(model_path, map_location=self.device))
        model = model.to(self.device)
        model.eval()
        return model
    
    def predict(self, essay, essay_set=None, max_length=256):
        """Predict essay score for a given essay."""
        if essay_set is None:
            essay_set = self._detect_essay_set(essay)
        
        # Normalize using set-specific params
        norm_score = self._normalize_score(essay_set)
        
        # Tokenize
        encoding = self.tokenizer(
            essay,
            add_special_tokens=True,
            max_length=max_length,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        input_ids = encoding['input_ids'].to(self.device)
        attention_mask = encoding['attention_mask'].to(self.device)
        
        # Predict
        with torch.no_grad():
            pred_normalized = self.model(input_ids, attention_mask).item()
        
        # Denormalize
        score_min, score_max = self.score_ranges[essay_set]
        pred_score = pred_normalized * (score_max - score_min) + score_min
        pred_score = max(score_min, min(score_max, pred_score))
        
        return {
            "predicted_score": float(pred_score),
            "essay_set": int(essay_set),
            "score_range": list(self.score_ranges[essay_set])
        }
    
    def _normalize_score(self, essay_set):
        """Get normalization parameters for a given set."""
        mean = self.score_means.get(essay_set, 0)
        std = self.score_stds.get(essay_set, 1)
        return (mean, std)
    
    def _detect_essay_set(self, essay):
        """Detect essay set based on length (fallback when not provided)."""
        length = len(essay)
        if length < 150:
            return 3
        elif length < 300:
            return 4
        elif length < 500:
            return 2
        elif length < 800:
            return 5
        else:
            return 1

class BertEssayScorer(torch.nn.Module):
    def __init__(self, model_name='bert-base-uncased', dropout=0.1):
        super(BertEssayScorer, self).__init__()
        self.bert = BertModel.from_pretrained(model_name)
        self.dropout = torch.nn.Dropout(dropout)
        self.regressor = torch.nn.Linear(768, 1)
    
    def forward(self, input_ids, attention_mask):
        outputs = self.bert(input_ids=input_ids, attention_mask=attention_mask)
        pooled_output = outputs.pooler_output
        x = self.dropout(pooled_output)
        return self.regressor(x).squeeze(-1)
