import importlib
import sys

print("=" * 50)
print("Python Environment Check")
print("=" * 50)

print("Python version:", sys.version)
print()

# 需要检查的库
packages = [
    "numpy",
    "pandas",
    "sklearn",
    "scipy",
    "tqdm",
    "requests",
    "matplotlib",
    "transformers",
    "datasets",
    "evaluate",
    "accelerate",
    "sentencepiece",
    "huggingface_hub",
    "spacy",
]

failed = []

for pkg in packages:
    try:
        importlib.import_module(pkg)
        print(f"{pkg:<20} ✓ installed")
    except ImportError:
        print(f"{pkg:<20} ✗ NOT installed")
        failed.append(pkg)

print()
print("=" * 50)

if failed:
    print("Missing packages:")
    for p in failed:
        print(" -", p)
    print()
    print("Run:")
    print("pip install -r env/requirements_new.txt")
else:
    print("All dependencies installed successfully ✅")

print("=" * 50)