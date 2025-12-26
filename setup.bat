@echo off
echo 🚀 Configurando ambiente Tech Challenge 3...

REM Criar .env se não existir
if not exist .env (
    echo 📝 Criando arquivo .env a partir de env.example...
    copy env.example .env
    echo ✅ Arquivo .env criado. Por favor, edite-o com suas configurações.
) else (
    echo ✅ Arquivo .env já existe.
)

REM Criar diretórios necessários
echo 📁 Criando diretórios...
if not exist logs mkdir logs
if not exist lora_model_qwen3_medquad mkdir lora_model_qwen3_medquad
if not exist postgres_data mkdir postgres_data

REM Criar ambiente virtual se não existir
if not exist .venv (
    echo 🐍 Criando ambiente virtual Python...
    python -m venv .venv
    echo ✅ Ambiente virtual criado.
) else (
    echo ✅ Ambiente virtual já existe.
)

echo.
echo ✅ Setup inicial concluído!
echo.
echo Próximos passos:
echo 1. Edite o arquivo .env com suas configurações
echo 2. Ative o ambiente virtual: .venv\Scripts\activate
echo 3. Instale PyTorch com CUDA: pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
echo 4. Instale Unsloth: pip install "unsloth[windows] @ git+https://github.com/unslothai/unsloth.git"
echo 5. Instale outras dependências: pip install -r requirements.txt
echo 6. Execute verificação: python check_environment.py
echo 7. Inicie o banco: docker-compose up -d


