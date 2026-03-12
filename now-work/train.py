import os
import pandas as pd
import numpy as np
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import BertTokenizer, BertModel, get_linear_schedule_with_warmup
from torch.optim import AdamW
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class EssayDataset(Dataset):
    def __init__(self, essays, scores, tokenizer, max_length=512):
        self.essays = essays
        self.scores = scores
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.essays)
    
    def __getitem__(self, idx):
        essay = str(self.essays[idx])
        score = float(self.scores[idx])
        
        encoding = self.tokenizer(
            essay,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt'
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(score, dtype=torch.float)
        }

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

def train_epoch(model, data_loader, optimizer, scheduler, device):
    model.train()
    total_loss = 0
    scaler = torch.cuda.amp.GradScaler()
    
    for batch in data_loader:
        input_ids = batch['input_ids'].to(device)
        attention_mask = batch['attention_mask'].to(device)
        labels = batch['labels'].to(device)
        
        optimizer.zero_grad()
        
        with torch.cuda.amp.autocast():
            outputs = model(input_ids, attention_mask)
            loss = torch.nn.MSELoss()(outputs, labels)
        
        scaler.scale(loss).backward()
        scaler.unscale_(optimizer)
        torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
        scaler.step(optimizer)
        scaler.update()
        scheduler.step()
        total_loss += loss.item()
    
    return total_loss / len(data_loader)

def evaluate(model, data_loader, device):
    model.eval()
    predictions = []
    actuals = []
    
    with torch.no_grad():
        for batch in data_loader:
            input_ids = batch['input_ids'].to(device)
            attention_mask = batch['attention_mask'].to(device)
            labels = batch['labels']
            
            outputs = model(input_ids, attention_mask)
            predictions.extend(outputs.cpu().numpy())
            actuals.extend(labels.numpy())
    
    mse = mean_squared_error(actuals, predictions)
    rmse = np.sqrt(mse)
    return rmse, predictions

def main():
    DATA_PATH = 'data/training_set_rel3.tsv'
    MODEL_NAME = 'bert-base-uncased'
    MAX_LENGTH = 256
    BATCH_SIZE = 16
    EPOCHS = 10
    LEARNING_RATE = 1e-5  # 更小学习率
    OUTPUT_DIR = 'output'
    MAX_SAMPLES = None  # 全部数据
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    print(f"Using device: {device}")
    
    print("Loading data...")
    df = pd.read_csv(DATA_PATH, sep='\t', encoding='latin-1')
    df = df.dropna(subset=['essay', 'domain1_score', 'essay_set'])
    
    print(f"Essay sets: {df['essay_set'].unique()}")
    print("Normalizing scores per essay set...")
    
    score_means = {}
    score_stds = {}
    for essay_set in df['essay_set'].unique():
        set_df = df[df['essay_set'] == essay_set]
        mean = set_df['domain1_score'].mean()
        std = set_df['domain1_score'].std()
        score_means[int(essay_set)] = mean
        score_stds[int(essay_set)] = std if std > 0 else 1.0
        print(f"  Set {essay_set}: mean={mean:.2f}, std={std:.2f}")
    
    df['normalized_score'] = df.apply(
        lambda x: (x['domain1_score'] - score_means[x['essay_set']]) / score_stds[x['essay_set']], 
        axis=1
    )
    
    essays = df['essay'].values
    scores = df['normalized_score'].values
    
    print(f"Total samples: {len(essays)}")
    print(f"Normalized score range: {scores.min():.2f} - {scores.max():.2f}")
    
    if MAX_SAMPLES and len(essays) > MAX_SAMPLES:
        indices = np.random.choice(len(essays), MAX_SAMPLES, replace=False)
        essays = essays[indices]
        scores = scores[indices]
        print(f"Sampled to: {len(essays)} samples")
    
    train_essays, val_essays, train_scores, val_scores = train_test_split(
        essays, scores, test_size=0.1, random_state=42
    )
    
    print(f"Training samples: {len(train_essays)}")
    print(f"Validation samples: {len(val_essays)}")
    
    print("Loading tokenizer...")
    tokenizer = BertTokenizer.from_pretrained(MODEL_NAME)
    
    print("Creating datasets...")
    train_dataset = EssayDataset(train_essays, train_scores, tokenizer, MAX_LENGTH)
    val_dataset = EssayDataset(val_essays, val_scores, tokenizer, MAX_LENGTH)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    print("Creating model...")
    model = BertEssayScorer(MODEL_NAME)
    model = model.to(device)
    
    optimizer = AdamW(model.parameters(), lr=LEARNING_RATE)
    total_steps = len(train_loader) * EPOCHS
    scheduler = get_linear_schedule_with_warmup(
        optimizer,
        num_warmup_steps=total_steps // 10,
        num_training_steps=total_steps
    )
    
    best_rmse = float('inf')
    
    print("Starting training...")
    for epoch in range(EPOCHS):
        print(f"\nEpoch {epoch + 1}/{EPOCHS}")
        
        train_loss = train_epoch(model, train_loader, optimizer, scheduler, device)
        print(f"Training Loss: {train_loss:.4f}")
        
        val_rmse, predictions = evaluate(model, val_loader, device)
        print(f"Validation RMSE: {val_rmse:.4f}")
        
        if val_rmse < best_rmse:
            best_rmse = val_rmse
            torch.save(model.state_dict(), os.path.join(OUTPUT_DIR, 'best_model.pt'))
            import json
            with open(os.path.join(OUTPUT_DIR, 'score_params.json'), 'w') as f:
                json.dump({'means': score_means, 'stds': score_stds}, f)
            print(f"Model saved with RMSE: {best_rmse:.4f}")
    
    print("\nTraining completed!")
    print(f"Best Validation RMSE: {best_rmse:.4f}")

if __name__ == '__main__':
    main()
