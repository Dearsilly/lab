import sys
print("Python路径:", sys.executable)
print("Python版本:", sys.version)

try:
    import torch
    print("PyTorch版本:", torch.__version__)
    print("CUDA可用:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU型号:", torch.cuda.get_device_name(0))
except ImportError as e:
    print("导入PyTorch失败:", e)
except Exception as e:
    print("未知错误:", e)