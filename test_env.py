import pandas as pd
import spacy
import torch
from transformers import BertTokenizer

print("环境验证通过！")
print(f"Pandas: {pd.__version__}")
print(f"SpaCy: {spacy.__version__}")
print(f"PyTorch: {torch.__version__}")
print(f"GPU可用: {torch.cuda.is_available()}")