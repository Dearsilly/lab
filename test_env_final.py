import torch
import spacy
from transformers import BertTokenizer, BertForSequenceClassification

print("✅ PyTorch版本:", torch.__version__)
print("✅ CUDA可用:", torch.cuda.is_available())
print("✅ spacy版本:", spacy.__version__)
print("✅ transformers导入成功")

# 测试加载关键库
try:
    nlp = spacy.load("en_core_web_sm")
    print("✅ spacy模型加载成功")
except Exception as e:
    print("❌ spacy模型加载失败:", e)

try:
    model = BertForSequenceClassification.from_pretrained("bert-base-uncased", num_labels=2)
    print("✅ BERT模型加载成功")
except Exception as e:
    print("❌ BERT模型加载失败:", e)