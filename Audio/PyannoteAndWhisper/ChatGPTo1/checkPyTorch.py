import torch

print(f"PyTorch version: {torch.__version__}")
if torch.cuda.is_available():
    print("CUDA is available!")
    print(f"CUDA Version: {torch.version.cuda}")
    print(f"Number of CUDA devices: {torch.cuda.device_count()}")
    print(f"CUDA Device Name: {torch.cuda.get_device_name(0)}")
else:
    print("CUDA is not available.")
