import torch
from transformers import BertTokenizer, BertModel
import pandas as pd
import json

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

def predict_score(essay, model, tokenizer, device, max_length=256):
    model.eval()
    encoding = tokenizer(
        essay,
        add_special_tokens=True,
        max_length=max_length,
        padding='max_length',
        truncation=True,
        return_attention_mask=True,
        return_tensors='pt'
    )
    
    input_ids = encoding['input_ids'].to(device)
    attention_mask = encoding['attention_mask'].to(device)
    
    with torch.no_grad():
        score = model(input_ids, attention_mask)
    
    return score.item()

def main():
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    model_path = 'output/best_model.pt'
    params_path = 'output/score_params.json'
    model_name = 'bert-base-uncased'
    
    print("Loading model...")
    model = BertEssayScorer(model_name)
    model.load_state_dict(torch.load(model_path, map_location=device))
    model = model.to(device)
    model.eval()
    
    print("Loading score parameters...")
    with open(params_path, 'r') as f:
        params = json.load(f)
    score_means = params['means']
    score_stds = params['stds']
    
    print("Loading tokenizer...")
    tokenizer = BertTokenizer.from_pretrained(model_name)
    
    print("\n" + "="*50)
    print("Testing on validation data...")
    print("="*50)
    
    df = pd.read_csv('data/training_set_rel3.tsv', sep='\t', encoding='latin-1')
    df = df.dropna(subset=['essay', 'domain1_score', 'essay_set'])
    
    sample_df = df.sample(100, random_state=42)
    
    total_error = 0
    for idx, row in sample_df.iterrows():
        essay = row['essay'][:500]
        essay_set = row['essay_set']
        actual = row['domain1_score']
        
        normalized_pred = predict_score(essay, model, tokenizer, device)
        predicted = normalized_pred * score_stds[str(essay_set)] + score_means[str(essay_set)]
        
        error = abs(actual - predicted)
        total_error += error
        
        print(f"\nEssay ID: {row['essay_id']} (Set {essay_set})")
        print(f"Actual: {actual}, Predicted: {predicted:.2f}, Error: {error:.2f}")
    
    print(f"\n{'='*50}")
    print(f"Average Error: {total_error / len(sample_df):.2f}")
    print(f"{'='*50}")

if __name__ == '__main__':
    main()
