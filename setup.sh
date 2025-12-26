#!/bin/bash
# Script de setup inicial para Linux/macOS/WSL

set -e

echo "🚀 Configurando ambiente Tech Challenge 3..."

# Criar .env se não existir
if [ ! -f .env ]; then
    echo "📝 Criando arquivo .env a partir de env.example..."
    cp env.example .env
    echo "✅ Arquivo .env criado. Por favor, edite-o com suas configurações."
else
    echo "✅ Arquivo .env já existe."
fi

# Criar diretórios necessários
echo "📁 Criando diretórios..."
mkdir -p logs
mkdir -p lora_model_qwen3_medquad
mkdir -p postgres_data

# Criar ambiente virtual se não existir
if [ ! -d .venv ]; then
    echo "🐍 Criando ambiente virtual Python..."
    python3.10 -m venv .venv || python3 -m venv .venv
    echo "✅ Ambiente virtual criado."
else
    echo "✅ Ambiente virtual já existe."
fi

echo ""
echo "✅ Setup inicial concluído!"
echo ""
echo "Próximos passos:"
echo "1. Edite o arquivo .env com suas configurações"
echo "2. Ative o ambiente virtual: source .venv/bin/activate"
echo "3. Instale PyTorch com CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126"
echo "4. Instale Unsloth: pip install \"unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git\""
echo "5. Instale outras dependências: pip install -r requirements.txt"
echo "6. Execute verificação: python check_environment.py"
echo "7. Inicie o banco: docker-compose up -d"


