# Guia de Instalação - Tech Challenge 3

Este guia fornece instruções completas para instalar e configurar o projeto Dr. IA, incluindo dependências do sistema, Docker, LoRA e todas as bibliotecas necessárias.

## 📋 Índice

1. [Instalação no WSL2 (Windows Subsystem for Linux)](#instalação-no-wsl2-windows-subsystem-for-linux) ⭐ **RECOMENDADO PARA WINDOWS**
2. [Pré-requisitos do Sistema](#pré-requisitos-do-sistema)
3. [Instalação de Dependências do Sistema](#instalação-de-dependências-do-sistema)
4. [Configuração do Ambiente](#configuração-do-ambiente)
5. [Instalação do Python e Ambiente Virtual](#instalação-do-python-e-ambiente-virtual)
6. [Instalação do CUDA Toolkit](#instalação-do-cuda-toolkit)
7. [Instalação das Dependências Python](#instalação-das-dependências-python)
8. [Configuração do Banco de Dados (Docker)](#configuração-do-banco-de-dados-docker)
9. [Preparação do Modelo LoRA](#preparação-do-modelo-lora)
10. [Executando o Projeto](#executando-o-projeto)
11. [Troubleshooting](#troubleshooting)

---

## Instalação no WSL2 (Windows Subsystem for Linux)

> ⚠️ **IMPORTANTE**: Esta seção é específica para usuários do Windows que estão usando WSL2. Se você está usando Linux nativo, pule para a seção [Instalação de Dependências do Sistema](#instalação-de-dependências-do-sistema).

### Por que usar WSL2?

- ✅ Melhor performance para desenvolvimento Python/ML
- ✅ Acesso direto à GPU NVIDIA do Windows
- ✅ Ambiente Linux completo sem dual-boot
- ✅ Integração nativa com Docker Desktop
- ✅ Sistema de arquivos Linux mais eficiente

### Pré-requisitos no Windows

Antes de começar, você precisa ter:

1. **Windows 10 versão 2004+ ou Windows 11**
2. **WSL2 instalado e configurado**
3. **Docker Desktop para Windows** (com integração WSL2)
4. **GPU NVIDIA** com drivers atualizados

### Passo 1: Verificar e Instalar WSL2

**No PowerShell do Windows (como Administrador):**

```powershell
# Verificar versão do WSL
wsl --version

# Se não tiver WSL2, instale:
wsl --install

# Ou atualize para WSL2:
wsl --set-default-version 2

# Verificar distribuições instaladas
wsl --list --verbose
```

**Instalar Ubuntu (se ainda não tiver):**

```powershell
# Listar distribuições disponíveis
wsl --list --online

# Instalar Ubuntu 22.04 (recomendado)
wsl --install -d Ubuntu-22.04
```

### Passo 2: Configurar Docker Desktop para WSL2

1. **Baixe e instale Docker Desktop**:
   - https://www.docker.com/products/docker-desktop/
   - Durante a instalação, certifique-se de marcar "Use WSL 2 based engine"

2. **Configurar integração WSL2 no Docker Desktop**:
   - Abra Docker Desktop
   - Vá em **Settings** → **Resources** → **WSL Integration**
   - Ative a integração para sua distribuição WSL (ex: Ubuntu-22.04)
   - Clique em **Apply & Restart**

3. **Verificar Docker no WSL**:

```bash
# No terminal WSL
docker --version
docker-compose --version
docker ps
```

### Passo 3: Instalar Drivers NVIDIA para WSL

⚠️ **CRÍTICO**: Para acessar a GPU do Windows no WSL, você precisa instalar drivers específicos.

1. **No Windows, baixe e instale o driver NVIDIA para WSL**:
   - Acesse: https://www.nvidia.com/Download/index.aspx
   - Selecione seu modelo de GPU
   - **IMPORTANTE**: Baixe a versão mais recente que suporta WSL
   - Instale o driver normalmente no Windows

2. **Verificar GPU no WSL**:

```bash
# No terminal WSL
nvidia-smi
```

Você deve ver informações da sua GPU. Se não aparecer, verifique:
- Drivers NVIDIA estão atualizados no Windows
- WSL2 está usando a versão correta
- Reinicie o WSL: `wsl --shutdown` (no PowerShell) e abra novamente

### Passo 4: Instalar CUDA Toolkit no WSL

⚠️ **IMPORTANTE**: Antes de instalar CUDA no WSL, certifique-se de que os drivers NVIDIA estão instalados no Windows e que `nvidia-smi` funciona no WSL (veja Passo 3).

Siga as instruções da seção [Instalação do CUDA Toolkit](#instalação-do-cuda-toolkit), seção **WSL2**.

**Resumo rápido:**
```bash
# Método recomendado (mais simples)
sudo apt update
sudo apt install -y nvidia-cuda-toolkit
nvcc --version
```

Para método completo com versão específica, veja a seção geral de instalação do CUDA.

### Passo 5: Configurar Ambiente no WSL

**No terminal WSL:**

```bash
# Navegar para o diretório do projeto
# Se o projeto está no Windows, acesse via /mnt/c/...
cd /mnt/c/Users/SeuUsuario/Code/tech-challenge-3

# OU clone diretamente no sistema de arquivos do WSL (mais rápido)
cd ~
git clone <url-do-repositorio>
cd tech-challenge-3
```

**💡 Dica de Performance**: 
- Trabalhar com arquivos no sistema de arquivos do WSL (`~/`) é **muito mais rápido** que no Windows (`/mnt/c/`)
- Recomenda-se clonar o projeto dentro do WSL: `~/Code/tech-challenge-3`

### Passo 6: Instalar Dependências no WSL

Siga as instruções das seções gerais **usando o terminal WSL** (não PowerShell):

1. **[Instalação de Dependências do Sistema](#instalação-de-dependências-do-sistema)**: Instale Python (pyenv recomendado) e dependências básicas
2. **[Instalação do Python e Ambiente Virtual](#instalação-do-python-e-ambiente-virtual)**: Crie o ambiente virtual
3. **[Instalação das Dependências Python](#instalação-das-dependências-python)**: Instale PyTorch, Unsloth e outras dependências

**Notas específicas para WSL:**

- ✅ **Docker**: Já está instalado via Docker Desktop (verifique com `docker --version`)
- ✅ **Unsloth**: Use `unsloth[colab-new]` (mesmo estando no Windows, você está em ambiente Linux)
- ✅ **PyTorch CUDA**: Use `--index-url https://download.pytorch.org/whl/cu126` para CUDA 12.6
- ✅ **Verificação**: Após instalar tudo, execute `python check-cuda.py` para verificar se a GPU está acessível

### Passo 7: Verificar Acesso à GPU

**Executar script de verificação:**

```bash
# No terminal WSL (com ambiente virtual ativado)
python check-wsl-gpu.py
```

O arquivo `check-wsl-gpu.py` já está incluído no projeto e verifica:
- Se o PyTorch detecta CUDA
- Informações da GPU (nome, VRAM)
- Teste básico de operação na GPU
```

### Passo 8: Configurar Docker no WSL

O Docker Desktop já deve estar funcionando. Verifique:

```bash
# No terminal WSL
docker ps
docker-compose --version

# Testar com um container simples
docker run hello-world
```

### Considerações Importantes para WSL

1. **Sistema de Arquivos**:
   - ✅ Use `~/` (sistema de arquivos do WSL) para melhor performance
   - ⚠️ Evite `/mnt/c/` para arquivos grandes ou muitos arquivos pequenos
   - 💡 Clone o projeto dentro do WSL: `~/Code/tech-challenge-3`

2. **Acesso a Arquivos do Windows**:
   - Arquivos do Windows: `/mnt/c/Users/...`
   - Arquivos do WSL: `~/` ou `/home/seu-usuario/`

3. **Performance**:
   - WSL2 usa virtualização, então há uma pequena sobrecarga
   - Para treinamento LoRA, ainda é muito mais rápido que CPU
   - Considere aumentar a memória do WSL no Docker Desktop (Settings → Resources → WSL Integration → Advanced)

4. **Caminhos no .env**:
   - Use caminhos Linux: `./lora_model_qwen3_medquad` ou `~/models/lora_model`
   - Não use caminhos Windows: `C:\Users\...`

### Próximos Passos

Após configurar o WSL, continue com:
- [Configuração do Ambiente](#configuração-do-ambiente)
- [Preparação do Modelo LoRA](#preparação-do-modelo-lora)
- [Executando o Projeto](#executando-o-projeto)

---

## Pré-requisitos do Sistema

### Hardware Mínimo Recomendado

- **CPU**: Processador multi-core (Intel i5 ou AMD equivalente ou superior)
- **RAM**: Mínimo 16GB (32GB recomendado para treinamento LoRA)
- **GPU**: NVIDIA com suporte CUDA (mínimo 6GB VRAM, recomendado 8GB+)
  - Para treinamento LoRA: GPU com pelo menos 8GB VRAM
  - Para inferência apenas: GPU com 4GB VRAM pode funcionar
- **Armazenamento**: Mínimo 20GB de espaço livre (para modelos e datasets)

### Software Necessário

- **Sistema Operacional**: Linux (Ubuntu 20.04+ recomendado), Windows 10/11, ou macOS
- **Python**: 3.10 ou 3.11 (3.10 recomendado para melhor compatibilidade)
- **Docker**: Versão 20.10 ou superior
- **Docker Compose**: Versão 2.0 ou superior
- **Git**: Para clonar repositórios e baixar datasets
- **CUDA Toolkit**: Versão 11.8, 12.1 ou 12.6 (dependendo da sua GPU)

---

## Instalação de Dependências do Sistema

### Linux (Ubuntu/Debian)

#### Opção 1: Instalação com pyenv (Recomendado) ⭐

O pyenv permite gerenciar múltiplas versões do Python facilmente:

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar dependências para compilar Python
sudo apt install -y \
    git \
    curl \
    wget \
    build-essential \
    libssl-dev \
    zlib1g-dev \
    libbz2-dev \
    libreadline-dev \
    libsqlite3-dev \
    libncurses5-dev \
    libncursesw5-dev \
    xz-utils \
    tk-dev \
    libffi-dev \
    liblzma-dev \
    python3-openssl

# Instalar pyenv
curl https://pyenv.run | bash

# Adicionar pyenv ao PATH (adicione ao ~/.bashrc)
echo 'export PYENV_ROOT="$HOME/.pyenv"' >> ~/.bashrc
echo 'command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init -)"' >> ~/.bashrc

# Recarregar o shell
source ~/.bashrc

# Instalar Python 3.10 ou 3.11 com pyenv
pyenv install 3.10.13  # ou 3.11.7
pyenv global 3.10.13    # ou 3.11.7

# Verificar instalação
python --version  # Deve mostrar Python 3.10.x ou 3.11.x
```

#### Opção 2: Instalação via apt (Alternativa)

```bash
# Atualizar pacotes
sudo apt update && sudo apt upgrade -y

# Instalar dependências básicas
sudo apt install -y \
    python3.10 \
    python3.10-venv \
    python3-pip \
    git \
    curl \
    wget \
    build-essential \
    software-properties-common
```

#### Instalar Docker (para ambas as opções)

```bash
# Instalar Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Instalar Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose

# Reiniciar sessão ou fazer logout/login para aplicar mudanças do Docker
```

### Windows

1. **Instalar Python 3.10**:
   - Baixe de: https://www.python.org/downloads/
   - Durante a instalação, marque "Add Python to PATH"
   - Instale também "pip" e "tcl/tk"

2. **Instalar Docker Desktop**:
   - Baixe de: https://www.docker.com/products/docker-desktop/
   - Instale e reinicie o computador
   - Certifique-se de que o WSL2 está habilitado (Docker Desktop faz isso automaticamente)

3. **Instalar Git**:
   - Baixe de: https://git-scm.com/download/win
   - Use as opções padrão durante a instalação

### macOS

```bash
# Instalar Homebrew (se não tiver)
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Instalar dependências
brew install python@3.10 git docker docker-compose

# Iniciar Docker Desktop (baixe de https://www.docker.com/products/docker-desktop/)
```

---

## Configuração do Ambiente

### 1. Clonar o Repositório

```bash
git clone <url-do-repositorio>
cd tech-challenge-3
```

### 2. Criar Arquivo de Ambiente

Copie o arquivo de exemplo e configure as variáveis:

```bash
cp env.example .env
```

Edite o arquivo `.env` com suas configurações:

```bash
# Editor de texto (Linux/macOS)
nano .env
# ou
vim .env

# Windows (Notepad)
notepad .env
```

**Variáveis importantes a configurar:**

#### 1. `LORA_ADAPTER_PATH` - Caminho do Modelo LoRA

Caminho onde o modelo LoRA será salvo (após treinamento) ou carregado (para uso).

**Exemplos:**
```bash
# Caminho relativo (recomendado para WSL/Linux)
LORA_ADAPTER_PATH=./lora_model_qwen3_medquad

# Caminho absoluto no WSL
LORA_ADAPTER_PATH=~/models/lora_model_qwen3_medquad

# Caminho absoluto no Windows (PowerShell)
LORA_ADAPTER_PATH=C:\projetos\tech-challenge-3\lora_model_qwen3_medquad
```

**Importante:**
- ✅ **WSL**: Use caminhos Linux (`./` ou `~/`), nunca caminhos Windows (`C:\`)
- ✅ Se o modelo ainda não existe, ele será criado automaticamente após o treinamento
- ✅ Certifique-se de ter permissões de escrita no diretório

#### 2. `MODEL_BASE` - Modelo Base do HuggingFace

Modelo base que será usado como fundação para o LoRA. O modelo será baixado automaticamente do HuggingFace na primeira execução.

**Opções recomendadas:**
```bash
# Modelo pequeno (1.7B parâmetros) - Requer menos VRAM (~4GB)
MODEL_BASE=unsloth/Qwen3-1.7B

# Modelo médio (7B parâmetros) - Requer mais VRAM (~8GB+)
MODEL_BASE=unsloth/Qwen2.5-7B-Instruct

# Outros modelos disponíveis no HuggingFace
MODEL_BASE=unsloth/Llama-3.2-1B-Instruct
```

**Como escolher:**
- **GPU com 4-6GB VRAM**: Use `unsloth/Qwen3-1.7B`
- **GPU com 8GB+ VRAM**: Use `unsloth/Qwen2.5-7B-Instruct` (melhor qualidade)
- Modelos maiores requerem mais memória, mas geralmente têm melhor performance

#### 3. Configurações do PostgreSQL

##### `DB_HOST` - Host do Banco de Dados
```bash
# Para Docker local (padrão)
DB_HOST=localhost

# Para banco remoto
DB_HOST=192.168.1.100
# ou
DB_HOST=meu-servidor.com
```

##### `DB_PORT` - Porta do PostgreSQL
```bash
# Porta padrão do PostgreSQL
DB_PORT=5432

# Se usar porta customizada
DB_PORT=5433
```

##### `DB_NAME` - Nome do Banco de Dados
```bash
# Nome do banco (deve corresponder ao docker-compose.yaml)
DB_NAME=atividade3-fiap
```

##### `DB_USER` - Usuário do Banco
```bash
# Usuário padrão (deve corresponder ao docker-compose.yaml)
DB_USER=user

# Para produção, use um usuário específico
DB_USER=app_user
```

##### `DB_PASSWORD` - Senha do Banco
```bash
# Senha padrão (deve corresponder ao docker-compose.yaml)
DB_PASSWORD=password

# ⚠️ IMPORTANTE: Para produção, use uma senha forte!
DB_PASSWORD=MinhaSenh@Segura123!
```

**Nota**: Se você estiver usando o `docker-compose.yaml` padrão do projeto, os valores já estão configurados. Apenas certifique-se de que correspondem entre o `.env` e o `docker-compose.yaml`.

#### 4. `AGENT_MODE` - Modo de Execução

Define como o agente será executado:

```bash
# Modo TESTE: Executa queries pré-definidas e encerra
# Útil para testar funcionalidades sem interação
AGENT_MODE=TESTE

# Modo INTERATIVO: Chat interativo
# Permite conversar com o agente em tempo real
AGENT_MODE=INTERATIVO
```

**Quando usar cada modo:**
- **TESTE**: Para verificar se tudo está funcionando, testar queries específicas, ou executar em scripts automatizados
- **INTERATIVO**: Para uso normal, conversar com o agente, fazer perguntas sobre o banco de dados

**Outras variáveis úteis (opcionais):**

- `LOG_LEVEL`: Nível de detalhamento dos logs (`DEBUG`, `INFO`, `WARNING`, `ERROR`)
- `MAX_SEQ_LENGTH`: Comprimento máximo de sequência do modelo (padrão: `2048`)
- `LOAD_IN_4BIT`: Usar quantização 4-bit para economizar memória (`true` ou `false`)

---

## Instalação do Python e Ambiente Virtual

### Criar Ambiente Virtual

#### Se você instalou Python com pyenv:

```bash
# Certifique-se de que a versão correta está ativa
python --version  # Deve mostrar Python 3.10.x ou 3.11.x

# Criar ambiente virtual
python -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate
```

#### Se você instalou Python via apt:

```bash
# Linux / WSL2 / macOS
python3.10 -m venv .venv
# ou
python3.11 -m venv .venv

# Ativar ambiente virtual
source .venv/bin/activate
```

#### Windows (PowerShell, sem WSL):

```bash
python -m venv .venv
.venv\Scripts\activate
```

**Nota para WSL**: Use os comandos Linux (`source .venv/bin/activate`), pois você está em ambiente Linux.

**Nota sobre pyenv**: Se você usou pyenv, o comando `python` já aponta para a versão correta, então use `python -m venv .venv` em vez de `python3.10 -m venv .venv`.

### Verificar Instalação

```bash
python --version  # Deve mostrar Python 3.10.x ou 3.11.x
pip --version
```

---

## Instalação do CUDA Toolkit

### Verificar GPU NVIDIA

```bash
# Linux / WSL
nvidia-smi

# Windows (PowerShell)
# Abra o Gerenciador de Dispositivos e verifique em "Adaptadores de vídeo"
```

### Instalar CUDA Toolkit

**WSL2 (Windows Subsystem for Linux):**

⚠️ **IMPORTANTE**: No WSL, você precisa instalar drivers NVIDIA no Windows primeiro, depois instalar o CUDA Toolkit no WSL.

1. **No Windows**: Instale os drivers NVIDIA mais recentes que suportam WSL
   - Baixe de: https://www.nvidia.com/Download/index.aspx
   - Certifique-se de que a versão suporta WSL

2. **No WSL**: Verifique se a GPU está acessível:
   ```bash
   nvidia-smi
   ```

3. **No WSL**: Instale o CUDA Toolkit:
   ```bash
   # Método recomendado (mais simples)
   sudo apt update
   sudo apt install -y nvidia-cuda-toolkit
   
   # OU instale a versão completa (veja seção WSL acima)
   ```

4. **Verificar Instalação**:
   ```bash
   nvcc --version
   nvidia-smi
   ```

**Linux Nativo:**

1. Verifique a versão do driver NVIDIA:
   ```bash
   nvidia-smi
   ```

2. Baixe o CUDA Toolkit apropriado:
   - CUDA 12.6: https://developer.nvidia.com/cuda-12-6-0-download-archive
   - CUDA 11.8: https://developer.nvidia.com/cuda-11-8-0-download-archive

3. Siga as instruções de instalação do site da NVIDIA

**Windows Nativo (sem WSL):**

1. Baixe o CUDA Toolkit de: https://developer.nvidia.com/cuda-downloads
2. Execute o instalador e siga as instruções
3. Reinicie o computador após a instalação

**Verificar Instalação:**

```bash
nvcc --version
```

---

## Instalação das Dependências Python

### 1. Atualizar pip

```bash
pip install --upgrade pip setuptools wheel
```

### 2. Instalar PyTorch com CUDA

**Para CUDA 12.6:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
```

**Para CUDA 11.8:**
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

**Para CPU apenas (não recomendado para treinamento):**
```bash
pip install torch torchvision torchaudio
```

### 3. Instalar Unsloth

```bash
# Linux / WSL2
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# Windows (PowerShell, sem WSL)
pip install "unsloth[windows] @ git+https://github.com/unslothai/unsloth.git"

# macOS
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"
```

**Nota para WSL**: Use `unsloth[colab-new]` mesmo estando no Windows, pois você está rodando em ambiente Linux.

**Nota**: O Unsloth instala automaticamente várias dependências (transformers, datasets, trl, etc.)

### 4. Instalar Outras Dependências

```bash
pip install -r requirements.txt
```

### 5. Verificar Instalação CUDA no Python

```bash
python check-cuda.py
```

Você deve ver:
```
✅ PyTorch CUDA available: True
✅ GPU Name: [Nome da sua GPU]
```

---

## Configuração do Banco de Dados (Docker)

### 1. Iniciar o PostgreSQL

```bash
docker-compose up -d
```

### 2. Verificar se o Container Está Rodando

```bash
docker-compose ps
```

Você deve ver o container `postgres-atividade3-fiap` com status `Up`.

### 3. Verificar Logs (Opcional)

```bash
docker-compose logs db
```

### 4. Testar Conexão (Opcional)

```bash
# Linux/macOS
docker exec -it postgres-atividade3-fiap psql -U user -d atividade3-fiap

# Windows (PowerShell)
docker exec -it postgres-atividade3-fiap psql -U user -d atividade3-fiap
```

No prompt do PostgreSQL, execute:
```sql
\dt  -- Lista as tabelas
SELECT * FROM ESPECIALIDADES;  -- Testa uma consulta
\q   -- Sair
```

### 5. Parar o Banco (quando necessário)

```bash
docker-compose down
```

**Nota**: Os dados persistem no volume `postgres_data/` mesmo após parar o container.

---

## Preparação do Modelo LoRA

Antes de executar o projeto, você precisa ter um modelo LoRA treinado. Escolha uma das opções abaixo:

**Como saber qual opção usar?**

1. **Verifique se você já tem um modelo:**
   ```bash
   # Verificar se o diretório do modelo existe
   ls -la lora_model_qwen3_medquad/ 2>/dev/null || echo "Modelo não encontrado"
   
   # Ou verifique o caminho configurado no .env
   grep LORA_ADAPTER_PATH .env
   ```

2. **Se o diretório não existe ou está vazio** → Use a **Opção 2** (Treinar o Modelo)
3. **Se o diretório existe e contém os arquivos necessários** → Use a **Opção 1** (Modelo Pré-treinado)

---

### Opção 1: Usar Modelo LoRA Pré-treinado

✅ **Use esta opção se:**
- Você já treinou o modelo anteriormente
- Você recebeu um modelo LoRA de outra pessoa
- O diretório especificado em `LORA_ADAPTER_PATH` já existe e contém os arquivos

**Passos:**

1. **Verifique o caminho configurado no `.env`:**
   ```bash
   grep LORA_ADAPTER_PATH .env
   # Exemplo: LORA_ADAPTER_PATH=./lora_model_qwen3_medquad
   ```

2. **Coloque o modelo no diretório especificado** (se ainda não estiver lá)

3. **Verifique se o modelo contém os arquivos necessários:**
   ```bash
   # Verificar arquivos do modelo
   ls -la lora_model_qwen3_medquad/
   ```
   
   O modelo deve conter:
   - ✅ `adapter_config.json` - Configuração do adaptador LoRA
   - ✅ `adapter_model.bin` ou `adapter_model.safetensors` - Pesos do modelo
   - ✅ `tokenizer_config.json` - Configuração do tokenizer
   - ✅ `tokenizer.json` (ou outros arquivos do tokenizer)

4. **Se algum arquivo estiver faltando**, você precisará treinar o modelo (veja Opção 2)

### Opção 2: Treinar o Modelo LoRA

✅ **Use esta opção se:**
- Você está instalando o projeto pela primeira vez
- O diretório do modelo não existe ou está vazio
- Você quer treinar um modelo personalizado

⚠️ **Requisitos antes de começar:**
- GPU NVIDIA com pelo menos 8GB VRAM (recomendado)
- CUDA instalado e funcionando (verifique com `python check-cuda.py`)
- Ambiente virtual ativado
- PyTorch com suporte CUDA instalado
- Unsloth instalado

#### Passo 1: Preparar o Dataset

Execute os scripts na ordem:

```bash
# Certifique-se de que o ambiente virtual está ativado
source .venv/bin/activate  # Linux/WSL/macOS
# ou
.venv\Scripts\activate     # Windows

# 1. Clonar repositório e extrair XMLs
python lora/01-clonar-repo-trata-dados.py

# 2. Converter XMLs em vetores JSONL
python lora/02-converte-xml-vector.py
```

Isso criará o arquivo `dataset_medquad_ft.jsonl` no diretório raiz do projeto.

**Verificar se o dataset foi criado:**
```bash
ls -lh dataset_medquad_ft.jsonl
```

#### Passo 2: Treinar o Modelo

```bash
# Certifique-se de que o ambiente virtual está ativado
python lora/03-treinamento-lora.py
```

**⚠️ Importante antes de treinar:**
- Verifique se o arquivo `.env` está configurado corretamente
- O caminho `LORA_ADAPTER_PATH` no `.env` será usado para salvar o modelo
- Certifique-se de ter espaço em disco suficiente (pelo menos 2-5GB livres)

**Requisitos para Treinamento:**
- ✅ GPU NVIDIA com pelo menos 8GB VRAM (recomendado)
- ⏱️ Processo pode levar várias horas dependendo do tamanho do dataset
- 💾 Espaço em disco: ~2-5GB para o modelo treinado

**Monitoramento durante o treinamento:**
- O script exibirá logs de progresso no terminal
- Abra outro terminal e monitore a GPU:
  ```bash
  watch -n 1 nvidia-smi
  ```
- Verifique o uso de VRAM (deve estar próximo do máximo da sua GPU)
- O modelo será salvo automaticamente ao finalizar o treinamento

#### Passo 3: Verificar Modelo Treinado

Após o treinamento, verifique se o modelo foi criado corretamente:

```bash
# Verificar se o diretório foi criado
ls -la lora_model_qwen3_medquad/  # Linux/macOS/WSL
dir lora_model_qwen3_medquad      # Windows

# Verificar arquivos essenciais
ls -lh lora_model_qwen3_medquad/ | grep -E "adapter|tokenizer"
```

**Arquivos esperados:**
- ✅ `adapter_config.json`
- ✅ `adapter_model.bin` ou `adapter_model.safetensors`
- ✅ `tokenizer_config.json`
- ✅ `tokenizer.json`
- ✅ Outros arquivos do tokenizer (se houver)

**Se todos os arquivos estiverem presentes**, você pode prosseguir para [Executando o Projeto](#executando-o-projeto).

**Se algum arquivo estiver faltando**, verifique os logs do treinamento para identificar o problema.

---

## Executando o Projeto

### 1. Verificar Configuração

Certifique-se de que:
- ✅ Docker está rodando e o PostgreSQL está ativo (`docker-compose ps`)
- ✅ Arquivo `.env` está configurado corretamente
- ✅ **Modelo LoRA está no caminho especificado** (veja seção [Preparação do Modelo LoRA](#preparação-do-modelo-lora))
- ✅ Ambiente virtual está ativado

**Verificar modelo LoRA:**
```bash
# Verificar se o diretório do modelo existe
ls -la lora_model_qwen3_medquad/ 2>/dev/null && echo "✅ Modelo encontrado" || echo "❌ Modelo não encontrado - você precisa treinar o modelo primeiro"

# Verificar arquivos essenciais
if [ -d "lora_model_qwen3_medquad" ]; then
  echo "Arquivos do modelo:"
  ls -lh lora_model_qwen3_medquad/ | grep -E "adapter|tokenizer"
fi
```

### 2. Executar o Agente

**Opção 1: Definir no arquivo `.env` (Recomendado)** ⭐

Edite o arquivo `.env` e defina:
```bash
AGENT_MODE=TESTE  # ou INTERATIVO
```

Depois execute:
```bash
python main.py
```

**Opção 2: Definir como variável de ambiente**

**Modo de Teste (executa queries pré-definidas):**
```bash
# Linux/macOS/WSL
export AGENT_MODE=TESTE

# Windows CMD
set AGENT_MODE=TESTE

# Windows PowerShell
$env:AGENT_MODE="TESTE"

python main.py
```

**Modo Interativo (chat):**
```bash
# Linux/macOS/WSL
export AGENT_MODE=INTERATIVO

# Windows CMD
set AGENT_MODE=INTERATIVO

# Windows PowerShell
$env:AGENT_MODE="INTERATIVO"

python main.py
```

**Nota**: Se não definir `AGENT_MODE` em nenhum lugar, o padrão é `TESTE`.

### 3. Usar o Chat Interativo

No modo interativo, você pode fazer perguntas como:
- "Quais especialidades temos no hospital?"
- "Liste todos os médicos com suas especialidades"
- "Gostaria de agendar uma consulta com cardiologista para amanhã às 10:00"

Digite `sair` para encerrar.

---

## Troubleshooting

### Problema: CUDA não disponível no PyTorch

**Solução Geral:**
1. Verifique se o CUDA Toolkit está instalado: `nvcc --version`
2. Verifique se o driver NVIDIA está atualizado: `nvidia-smi`
3. Reinstale o PyTorch com a versão correta do CUDA:
   ```bash
   pip uninstall torch torchvision torchaudio
   pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126
   ```

**Solução Específica para WSL:**
1. **Verifique drivers no Windows**:
   - Abra PowerShell como Administrador
   - Execute: `nvidia-smi` (deve funcionar no PowerShell também)
   - Se não funcionar, atualize os drivers NVIDIA no Windows

2. **Verifique GPU no WSL**:
   ```bash
   # No terminal WSL
   nvidia-smi
   ```
   Se não aparecer nada, o problema está na configuração do WSL com GPU.

3. **Reinicie o WSL**:
   ```powershell
   # No PowerShell do Windows
   wsl --shutdown
   # Depois abra o WSL novamente
   ```

4. **Verifique versão do WSL**:
   ```powershell
   wsl --list --verbose
   # Deve mostrar VERSION 2
   ```

5. **Se ainda não funcionar, reinstale CUDA no WSL**:
   ```bash
   # No WSL
   sudo apt remove --purge nvidia-cuda-toolkit
   sudo apt update
   sudo apt install -y nvidia-cuda-toolkit
   ```

### Problema: Erro ao carregar modelo LoRA

**Solução:**
1. Verifique se o caminho `LORA_ADAPTER_PATH` está correto no `.env`
2. Verifique se os arquivos do modelo existem no diretório
3. Se o modelo não existe, você precisa treiná-lo primeiro (veja seção "Preparação do Modelo LoRA")

### Problema: Erro de conexão com PostgreSQL

**Solução:**
1. Verifique se o Docker está rodando: `docker ps`
2. Verifique se o container PostgreSQL está ativo: `docker-compose ps`
3. Verifique as credenciais no arquivo `.env`
4. Tente reiniciar o container: `docker-compose restart`

### Problema: Erro de memória durante treinamento LoRA

**Solução:**
1. Reduza o `per_device_train_batch_size` no script de treinamento
2. Aumente o `gradient_accumulation_steps` para compensar
3. Use `load_in_4bit=True` (já está configurado)
4. Feche outros aplicativos que usam GPU

### Problema: Erro de permissão no Docker (Linux/WSL)

**Solução para Linux Nativo:**
```bash
sudo usermod -aG docker $USER
# Faça logout e login novamente
```

**Solução para WSL:**
No WSL, o Docker Desktop gerencia as permissões automaticamente. Se houver problemas:

1. **Verifique se Docker Desktop está rodando no Windows**
2. **Verifique integração WSL no Docker Desktop**:
   - Settings → Resources → WSL Integration
   - Certifique-se de que sua distribuição WSL está habilitada
3. **Reinicie o WSL**:
   ```powershell
   # No PowerShell
   wsl --shutdown
   ```
4. **Teste novamente no WSL**:
   ```bash
   docker ps
   ```

### Problema: Unsloth não instala no Windows

**Solução:**
1. Certifique-se de usar `unsloth[windows]` em vez de `unsloth[colab-new]`
2. Instale o Visual C++ Build Tools: https://visualstudio.microsoft.com/visual-cpp-build-tools/
3. Tente instalar em um ambiente virtual limpo

### Problema: Erro de multiprocessamento no Windows/WSL

**Solução:**
O script de treinamento já tem `num_proc=1` configurado. Se ainda houver problemas:

1. **No WSL**: Geralmente não há problemas de multiprocessamento
2. **No Windows nativo**: 
   - Adicione `if __name__ == '__main__':` no início do script (já está presente)
   - Certifique-se de executar o script diretamente: `python script.py`

### Problema: nvidia-smi não funciona no WSL

**Solução:**
1. **Verifique drivers no Windows**:
   - Abra PowerShell como Administrador
   - Execute: `nvidia-smi`
   - Se não funcionar no PowerShell, atualize os drivers NVIDIA

2. **Verifique se WSL2 está configurado corretamente**:
   ```powershell
   wsl --list --verbose
   # Deve mostrar VERSION 2
   ```

3. **Reinicie o WSL**:
   ```powershell
   wsl --shutdown
   # Abra o WSL novamente
   ```

4. **Verifique se a GPU está sendo passada para o WSL**:
   ```bash
   # No WSL
   ls /usr/lib/wsl/lib
   # Deve mostrar arquivos relacionados ao NVIDIA
   ```

5. **Se ainda não funcionar, reinstale os drivers NVIDIA no Windows**:
   - Baixe a versão mais recente do site da NVIDIA
   - Certifique-se de que a versão suporta WSL

### Problema: Performance lenta no WSL

**Solução:**
1. **Use sistema de arquivos do WSL** (`~/`) em vez de Windows (`/mnt/c/`):
   ```bash
   # ❌ Lento
   cd /mnt/c/Users/SeuUsuario/Code/tech-challenge-3
   
   # ✅ Rápido
   cd ~/Code/tech-challenge-3
   ```

2. **Aumente memória do WSL no Docker Desktop**:
   - Settings → Resources → WSL Integration → Advanced
   - Aumente a memória alocada (ex: 16GB ou mais)

3. **Desative antivírus para diretórios do WSL** (se aplicável)

4. **Use WSL2** (não WSL1):
   ```powershell
   wsl --set-version Ubuntu-22.04 2
   ```

---

## Estrutura de Diretórios Esperada

Após a instalação completa, sua estrutura deve ser similar a:

```
tech-challenge-3/
├── .env                    # Configurações (criar a partir de .env.example)
├── .venv/                  # Ambiente virtual Python
├── logs/                   # Logs gerados pela aplicação
├── postgres_data/          # Dados persistentes do PostgreSQL (criado pelo Docker)
├── lora_model_qwen3_medquad/  # Modelo LoRA treinado (criar/baixar)
├── dataset_medquad_ft.jsonl  # Dataset para treinamento (criar)
├── init_files/
│   └── init.sql           # Script de inicialização do banco
├── lora/
│   ├── 01-clonar-repo-trata-dados.py
│   ├── 02-converte-xml-vector.py
│   └── 03-treinamento-lora.py
├── agent_graph.py
├── config.py
├── docker-compose.yaml
├── llm_model.py
├── main.py
├── requirements.txt
└── tools.py
```

---

## Próximos Passos

Após a instalação bem-sucedida:

1. **Teste o sistema** com queries simples no modo TESTE
2. **Explore o chat interativo** para entender as capacidades
3. **Personalize o modelo LoRA** treinando com seus próprios dados
4. **Ajuste o SYSTEM_PROMPT** em `config.py` para suas necessidades específicas

---

## Suporte

Para problemas adicionais:
1. Verifique os logs em `logs/`
2. Consulte a documentação das bibliotecas:
   - Unsloth: https://github.com/unslothai/unsloth
   - LangChain: https://python.langchain.com/
   - LangGraph: https://langchain-ai.github.io/langgraph/

---

**Última atualização**: Dezembro 2024

