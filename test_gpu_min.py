print("开始测试GPU...")
import torch
print("PyTorch导入成功")
print("PyTorch版本:", torch.__version__)
print("CUDA可用:", torch.cuda.is_available())