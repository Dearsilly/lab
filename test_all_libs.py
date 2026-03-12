# 测试所有核心库是否能正常导入
try:
    import pandas as pd
    print("✅ pandas导入成功")
except ImportError as e:
    print("❌ pandas导入失败:", e)

try:
    import spacy
    nlp = spacy.load("en_core_web_sm")
    print("✅ spacy导入成功")
except ImportError as e:
    print("❌ spacy导入失败:", e)

try:
    import torch
    print(f"✅ torch导入成功（版本：{torch.__version__}）")
    print(f"✅ CUDA可用：{torch.cuda.is_available()}")
except ImportError as e:
    print("❌ torch导入失败:", e)

try:
    from transformers import BertTokenizer
    tokenizer = BertTokenizer.from_pretrained("bert-base-uncased")
    print("✅ transformers导入成功")
except ImportError as e:
    print("❌ transformers导入失败:", e)

print("\n所有库测试完成！")