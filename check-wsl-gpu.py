import torch
import sys

print("=" * 60)
print("VERIFICAÇÃO DE GPU NO WSL")
print("=" * 60)

print(f"\nPython: {sys.version}")
print(f"PyTorch: {torch.__version__}")

if torch.cuda.is_available():
    print(f"\n✅ CUDA disponível!")
    print(f"   Versão CUDA: {torch.version.cuda}")
    print(f"   GPU: {torch.cuda.get_device_name(0)}")
    print(f"   VRAM Total: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    
    # Teste simples
    x = torch.randn(3, 3).cuda()
    print(f"\n✅ Teste de tensor na GPU: OK")
    print(f"   Tensor device: {x.device}")
else:
    print("\n❌ CUDA não disponível")
    print("   Verifique:")
    print("   1. Drivers NVIDIA instalados no Windows")
    print("   2. nvidia-smi funciona no WSL")
    print("   3. PyTorch foi instalado com suporte CUDA")

print("=" * 60)





