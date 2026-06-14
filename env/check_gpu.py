import torch

print("=" * 50)
print("GPU Environment Check")
print("=" * 50)

print("PyTorch version:", torch.__version__)
print("CUDA available:", torch.cuda.is_available())

if torch.cuda.is_available():

    print("GPU name:", torch.cuda.get_device_name(0))
    print("CUDA capability:", torch.cuda.get_device_capability(0))
    print("CUDA device count:", torch.cuda.device_count())

    print("\nRunning GPU test...")

    x = torch.randn(1024, 1024, device="cuda")
    y = torch.matmul(x, x)

    print("Tensor device:", y.device)
    print("GPU computation successful ✅")

else:
    print("GPU not available ❌")

print("=" * 50)