from transformers import BertForSequenceRegression, BertTokenizer

print("✅ BertForSequenceRegression 导入成功")
# 测试模型加载
try:
    model = BertForSequenceRegression.from_pretrained("bert-base-uncased", num_labels=1)
    print("✅ 回归模型加载成功")
except Exception as e:
    print("❌ 模型加载失败:", e)