#!/usr/bin/env python3
"""
Script para verificar se o ambiente está configurado corretamente.
Execute antes de rodar o projeto principal.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

def check_python_version():
    """Verifica versão do Python"""
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 10):
        print("❌ Python 3.10+ é necessário")
        return False
    print(f"✅ Python {version.major}.{version.minor}.{version.micro}")
    return True

def check_cuda():
    """Verifica se CUDA está disponível"""
    try:
        import torch
        if torch.cuda.is_available():
            print(f"✅ CUDA disponível: {torch.cuda.get_device_name(0)}")
            print(f"   Versão CUDA: {torch.version.cuda}")
            print(f"   VRAM Total: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
            return True
        else:
            print("⚠️  CUDA não disponível (modo CPU)")
            return False
    except ImportError:
        print("❌ PyTorch não instalado")
        return False

def check_env_file():
    """Verifica se arquivo .env existe"""
    if Path('.env').exists():
        print("✅ Arquivo .env encontrado")
        load_dotenv()
        return True
    else:
        print("⚠️  Arquivo .env não encontrado (usando valores padrão)")
        print("   Para personalizar, copie env.example para .env")
        return False

def check_docker():
    """Verifica se Docker está rodando"""
    import subprocess
    try:
        result = subprocess.run(['docker', 'ps'], capture_output=True, timeout=5)
        if result.returncode == 0:
            print("✅ Docker está rodando")
            return True
        else:
            print("⚠️  Docker não está rodando ou não está instalado")
            return False
    except (FileNotFoundError, subprocess.TimeoutExpired):
        print("⚠️  Docker não encontrado ou não está rodando")
        return False

def check_lora_model():
    """Verifica se modelo LoRA existe"""
    load_dotenv()
    lora_path = os.getenv('LORA_ADAPTER_PATH', './lora_model_qwen3_medquad')
    lora_path = Path(lora_path).expanduser().resolve()
    
    if lora_path.exists() and (lora_path / 'adapter_config.json').exists():
        print(f"✅ Modelo LoRA encontrado em: {lora_path}")
        return True
    else:
        print(f"⚠️  Modelo LoRA não encontrado em: {lora_path}")
        print("   Você precisará treinar o modelo primeiro")
        return False

def check_database_connection():
    """Verifica se consegue conectar ao banco de dados"""
    try:
        import psycopg2
        from config import DB_CONFIG
        
        conn = psycopg2.connect(**DB_CONFIG)
        conn.close()
        print("✅ Conexão com banco de dados OK")
        return True
    except ImportError:
        print("⚠️  psycopg2 não instalado")
        return False
    except Exception as e:
        print(f"⚠️  Não foi possível conectar ao banco: {e}")
        print("   Verifique se o Docker está rodando: docker-compose up -d")
        return False

def main():
    print("=" * 60)
    print("VERIFICAÇÃO DE AMBIENTE - Tech Challenge 3")
    print("=" * 60)
    print()
    
    checks = [
        ("Python", check_python_version),
        ("CUDA", check_cuda),
        (".env", check_env_file),
        ("Docker", check_docker),
        ("LoRA Model", check_lora_model),
        ("Database", check_database_connection),
    ]
    
    results = []
    for name, check_func in checks:
        print(f"[{name}]", end=" ")
        results.append(check_func())
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(checks)
    print(f"Resultado: {passed}/{total} verificações passaram")
    
    if passed == total:
        print("✅ Ambiente configurado corretamente!")
        return 0
    else:
        print("⚠️  Algumas verificações falharam. Revise as configurações.")
        print("\nDicas:")
        if not results[0]:  # Python
            print("  - Instale Python 3.10 ou superior")
        if not results[1]:  # CUDA
            print("  - Instale PyTorch com CUDA: pip install torch --index-url https://download.pytorch.org/whl/cu126")
        if not results[2]:  # .env
            print("  - Copie env.example para .env: cp env.example .env")
        if not results[3]:  # Docker
            print("  - Inicie o Docker Desktop ou instale Docker")
        if not results[4]:  # LoRA Model
            print("  - Treine o modelo: python lora/03-treinamento-lora.py")
        if not results[5]:  # Database
            print("  - Inicie o banco: docker-compose up -d")
        return 1

if __name__ == '__main__':
    sys.exit(main())


