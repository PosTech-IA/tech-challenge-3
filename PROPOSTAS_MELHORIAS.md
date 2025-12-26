# Propostas de Melhorias para Facilitar a Instalação

Este documento contém propostas de mudanças no código para tornar a instalação e configuração do projeto mais fácil e portável.

## 📋 Resumo das Propostas

1. **config.py**: Usar variáveis de ambiente com valores padrão
2. **docker-compose.yaml**: Usar variáveis de ambiente para configurações
3. **llm_model.py**: Tornar configurações do modelo mais flexíveis
4. **lora/03-treinamento-lora.py**: Usar variáveis de ambiente
5. **main.py**: Melhorar tratamento de variáveis de ambiente
6. **tools.py**: Usar configurações do .env

---

## 1. Melhorias no `config.py`

### Problema Atual
- Caminhos hardcoded (especialmente Windows: `C:\Users\robso\...`)
- Configurações do banco hardcoded
- Não usa variáveis de ambiente

### Proposta de Mudança

```python
# config.py
# Importações de Sistema e DB
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente do arquivo .env
load_dotenv()

# ==============================================================================
# CONFIGURAÇÕES DO MODELO LoRA
# ==============================================================================

# Caminho do adaptador LoRA (com fallback para caminho relativo)
LORA_ADAPTER_PATH = os.getenv(
    'LORA_ADAPTER_PATH',
    str(Path(__file__).parent / 'lora_model_qwen3_medquad')
)

# Garantir que o caminho seja absoluto
LORA_ADAPTER_PATH = os.path.abspath(os.path.expanduser(LORA_ADAPTER_PATH))

# Modelo base (com fallback)
MODEL_BASE = os.getenv('MODEL_BASE', 'unsloth/Qwen3-1.7B')

# ==============================================================================
# CONFIGURAÇÕES DO BANCO DE DADOS
# ==============================================================================

DB_CONFIG = {
    'dbname': os.getenv('DB_NAME', 'atividade3-fiap'),
    'user': os.getenv('DB_USER', 'user'),
    'password': os.getenv('DB_PASSWORD', 'password'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432')
}

DB_NAME = DB_CONFIG['dbname']

# ==============================================================================
# CONFIGURAÇÕES DO MODELO (Avançado)
# ==============================================================================

MAX_SEQ_LENGTH = int(os.getenv('MAX_SEQ_LENGTH', '2048'))
LOAD_IN_4BIT = os.getenv('LOAD_IN_4BIT', 'true').lower() == 'true'
DEVICE_MAP = os.getenv('DEVICE_MAP', 'auto')

# ==============================================================================
# CONFIGURAÇÕES DE LOGGING
# ==============================================================================

LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_DIR = os.getenv('LOG_DIR', 'logs')

# Criar diretório de logs se não existir
os.makedirs(LOG_DIR, exist_ok=True)

# ==============================================================================
# SCHEMA DO BANCO (mantido como está)
# ==============================================================================

DATABASE_SCHEMA_INFO = f"""
SCHEMA DO BANCO {DB_NAME}:
...
"""

SYSTEM_PROMPT = """
...
"""
```

### Benefícios
- ✅ Funciona em qualquer sistema operacional
- ✅ Fácil configuração via arquivo `.env`
- ✅ Valores padrão sensatos para desenvolvimento
- ✅ Caminhos relativos funcionam automaticamente

---

## 2. Melhorias no `docker-compose.yaml`

### Problema Atual
- Valores hardcoded (nome do banco, usuário, senha)
- Não permite fácil customização

### Proposta de Mudança

```yaml
# docker-compose.yml
version: '3.8'

services:
  db:
    image: ${POSTGRES_IMAGE:-postgres:16-alpine}
    container_name: ${POSTGRES_CONTAINER_NAME:-postgres-atividade3-fiap}
    restart: always
    
    environment:
      POSTGRES_DB: ${DB_NAME:-atividade3-fiap}
      POSTGRES_USER: ${DB_USER:-user}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
    
    ports:
      - "${DB_PORT:-5432}:5432"
      
    volumes:
      - ./postgres_data:/var/lib/postgresql/data/
      - ./init_files/init.sql:/docker-entrypoint-initdb.d/init.sql

volumes:
  postgres_data:
```

### Benefícios
- ✅ Usa variáveis de ambiente com valores padrão
- ✅ Fácil de customizar sem editar o arquivo
- ✅ Compatível com diferentes ambientes (dev, staging, prod)

---

## 3. Melhorias no `llm_model.py`

### Problema Atual
- Configurações hardcoded (max_seq_length, load_in_4bit)
- Não usa variáveis de ambiente

### Proposta de Mudança

```python
# llm_model.py
# ... imports existentes ...

from config import (
    LORA_ADAPTER_PATH, 
    MODEL_BASE,
    MAX_SEQ_LENGTH,
    LOAD_IN_4BIT,
    DEVICE_MAP
)

# ... código existente ...

try:
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=LORA_ADAPTER_PATH,
        max_seq_length=MAX_SEQ_LENGTH,
        dtype=None,
        load_in_4bit=LOAD_IN_4BIT,
        device_map=DEVICE_MAP,
    )
    llm_logger.info(f"Modelo carregado com sucesso de: {LORA_ADAPTER_PATH}")
    llm_logger.info(f"Configuração: max_seq_length={MAX_SEQ_LENGTH}, load_in_4bit={LOAD_IN_4BIT}, device_map={DEVICE_MAP}")
    
    # ... resto do código ...
```

### Benefícios
- ✅ Configurações centralizadas em `config.py`
- ✅ Fácil ajuste via variáveis de ambiente
- ✅ Melhor logging das configurações usadas

---

## 4. Melhorias no `lora/03-treinamento-lora.py`

### Problema Atual
- Caminhos hardcoded (Windows específico)
- Configurações hardcoded no código

### Proposta de Mudança

```python
# lora/03-treinamento-lora.py
# ... imports existentes ...
import os
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# --- CONFIGURAÇÃO DE CAMINHOS E MODELO ---
# Usar variáveis de ambiente com fallbacks
LORA_ADAPTER_PATH = os.getenv(
    'LORA_ADAPTER_PATH',
    str(Path(__file__).parent.parent / 'lora_model_qwen3_medquad')
)
LORA_ADAPTER_PATH = os.path.abspath(os.path.expanduser(LORA_ADAPTER_PATH))

MODEL_BASE = os.getenv('MODEL_BASE', 'unsloth/Qwen3-1.7B')

# Dataset path
DATASET_PATH = os.getenv(
    'DATASET_PATH',
    str(Path(__file__).parent.parent / 'dataset_medquad_fine_tuning.jsonl')
)
DATASET_PATH = os.path.abspath(os.path.expanduser(DATASET_PATH))

# Configurações de treinamento (com fallbacks)
LORA_R = int(os.getenv('LORA_R', '16'))
LORA_ALPHA = int(os.getenv('LORA_ALPHA', '16'))
LORA_DROPOUT = float(os.getenv('LORA_DROPOUT', '0'))
LEARNING_RATE = float(os.getenv('LEARNING_RATE', '2e-4'))
BATCH_SIZE = int(os.getenv('BATCH_SIZE', '1'))
GRADIENT_ACCUMULATION_STEPS = int(os.getenv('GRADIENT_ACCUMULATION_STEPS', '4'))
MAX_STEPS = int(os.getenv('MAX_STEPS', '60')) if os.getenv('MAX_STEPS') else None

# ... resto do código usando essas variáveis ...
```

### Benefícios
- ✅ Funciona em qualquer sistema operacional
- ✅ Configurações via `.env`
- ✅ Fácil ajuste de hiperparâmetros sem editar código

---

## 5. Melhorias no `main.py`

### Problema Atual
- Usa `os.getenv` mas poderia ter melhor tratamento de erros

### Proposta de Mudança

```python
# main.py
# ... imports existentes ...
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# ... código existente ...

def main():
    """Função principal de execução"""
    
    # Verificar se o arquivo .env existe (opcional, apenas aviso)
    if not os.path.exists('.env'):
        print("⚠️  AVISO: Arquivo .env não encontrado. Usando valores padrão.")
        print("   Para personalizar, copie env.example para .env e ajuste os valores.")
    
    # ... resto do código existente ...
```

### Benefícios
- ✅ Avisa usuário se `.env` não existe
- ✅ Carrega variáveis de ambiente automaticamente

---

## 6. Melhorias no `tools.py`

### Problema Atual
- Usa `DB_CONFIG` de `config.py` (já está bom, mas pode melhorar)

### Proposta de Mudança

```python
# tools.py
# ... imports existentes ...

from config import DB_CONFIG, DB_NAME

# O código já está usando DB_CONFIG, que agora vem do .env
# Nenhuma mudança necessária, mas podemos adicionar validação:

def validate_db_config():
    """Valida se as configurações do banco estão corretas"""
    required_keys = ['dbname', 'user', 'password', 'host', 'port']
    missing = [key for key in required_keys if not DB_CONFIG.get(key)]
    if missing:
        raise ValueError(f"Configurações do banco incompletas. Faltam: {missing}")
    return True

# Chamar no início do módulo (opcional)
# validate_db_config()
```

### Benefícios
- ✅ Validação de configurações
- ✅ Mensagens de erro mais claras

---

## 7. Criar Script de Verificação de Ambiente

### Proposta: Criar `check_environment.py`

```python
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
    ]
    
    results = []
    for name, check_func in checks:
        print(f"[{name}]", end=" ")
        results.append(check_func())
        print()
    
    print("=" * 60)
    passed = sum(results)
    total = len(results)
    print(f"Resultado: {passed}/{total} verificações passaram")
    
    if passed == total:
        print("✅ Ambiente configurado corretamente!")
        return 0
    else:
        print("⚠️  Algumas verificações falharam. Revise as configurações.")
        return 1

if __name__ == '__main__':
    sys.exit(main())
```

### Benefícios
- ✅ Verifica ambiente antes de executar
- ✅ Identifica problemas rapidamente
- ✅ Guia o usuário na configuração

---

## 8. Adicionar Script de Setup Inicial

### Proposta: Criar `setup.sh` e `setup.bat`

**setup.sh** (Linux/macOS):
```bash
#!/bin/bash
# Script de setup inicial para Linux/macOS

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
    python3.10 -m venv .venv
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
echo "3. Instale as dependências: pip install -r requirements.txt"
echo "4. Execute: python check_environment.py"
```

**setup.bat** (Windows):
```batch
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
echo 3. Instale as dependências: pip install -r requirements.txt
echo 4. Execute: python check_environment.py
```

### Benefícios
- ✅ Automatiza configuração inicial
- ✅ Cria estrutura de diretórios
- ✅ Guia o usuário nos próximos passos

---

## Resumo das Mudanças Necessárias

### Arquivos a Modificar:
1. ✅ `config.py` - Usar variáveis de ambiente
2. ✅ `docker-compose.yaml` - Usar variáveis de ambiente
3. ✅ `llm_model.py` - Usar configurações de `config.py`
4. ✅ `lora/03-treinamento-lora.py` - Usar variáveis de ambiente
5. ✅ `main.py` - Adicionar `load_dotenv()`

### Arquivos a Criar:
1. ✅ `env.example` - Template de configuração (já criado)
2. ✅ `check_environment.py` - Script de verificação
3. ✅ `setup.sh` / `setup.bat` - Scripts de setup inicial

### Dependências Adicionais:
- ✅ `python-dotenv` - Já adicionado ao `requirements.txt`

---

## Ordem de Implementação Recomendada

1. **Fase 1 - Configuração Básica:**
   - Modificar `config.py` para usar variáveis de ambiente
   - Adicionar `python-dotenv` ao `requirements.txt`
   - Criar `env.example`

2. **Fase 2 - Integração:**
   - Modificar `llm_model.py` para usar configurações de `config.py`
   - Modificar `docker-compose.yaml` para usar variáveis de ambiente
   - Modificar `main.py` para carregar `.env`

3. **Fase 3 - Scripts de Treinamento:**
   - Modificar `lora/03-treinamento-lora.py` para usar variáveis de ambiente

4. **Fase 4 - Ferramentas de Apoio:**
   - Criar `check_environment.py`
   - Criar `setup.sh` e `setup.bat`

---

## Notas Importantes

- ⚠️ **Backward Compatibility**: As mudanças propostas mantêm valores padrão, então o código continuará funcionando mesmo sem o arquivo `.env`
- ⚠️ **Testes**: Após implementar as mudanças, teste em diferentes sistemas operacionais
- ⚠️ **Documentação**: Atualize o `INSTALL.md` após implementar as mudanças

---

**Última atualização**: Dezembro 2024


