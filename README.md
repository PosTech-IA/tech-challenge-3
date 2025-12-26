# Tech Challenge 3 - Dr. IA Agent

Sistema de agente médico inteligente baseado em LangGraph, utilizando modelo LLM fine-tuned com LoRA (Unsloth + Qwen3) para interagir com banco de dados PostgreSQL e gerenciar agendamentos de consultas.

## 🚀 Início Rápido

Para uma instalação completa e detalhada, consulte o **[Guia de Instalação Completo](INSTALL.md)**.

> ⚠️ **Usuários Windows**: Recomendamos usar **WSL2** para melhor performance e acesso à GPU. Veja a seção [Instalação no WSL2](INSTALL.md#instalação-no-wsl2-windows-subsystem-for-linux) no guia de instalação.

### Pré-requisitos Mínimos

- Python 3.10 ou 3.11
- Docker e Docker Compose
- NVIDIA GPU com CUDA (recomendado 8GB+ VRAM)
- CUDA Toolkit 11.8, 12.1 ou 12.6
- 16GB+ RAM
- **Windows**: WSL2 recomendado (veja guia de instalação)

### Instalação Rápida

**Para WSL2 (Recomendado no Windows):**

```bash
# No terminal WSL
# 1. Clonar repositório (dentro do WSL para melhor performance)
cd ~
git clone <url-do-repositorio>
cd tech-challenge-3

# 2. Criar arquivo de configuração
cp env.example .env
# Edite o .env com suas configurações

# 3. Criar ambiente virtual
python3.10 -m venv .venv
source .venv/bin/activate

# 4. Instalar PyTorch com CUDA
pip install --upgrade pip setuptools wheel
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# 5. Instalar Unsloth (use colab-new no WSL)
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# 6. Instalar outras dependências
pip install -r requirements.txt

# 7. Verificar GPU
python check-cuda.py

# 8. Iniciar banco de dados (Docker Desktop deve estar rodando no Windows)
docker-compose up -d

# 9. Executar o agente
python main.py
```

**Para Linux/macOS:**

```bash
# 1. Clonar repositório
git clone <url-do-repositorio>
cd tech-challenge-3

# 2. Criar arquivo de configuração
cp env.example .env
# Edite o .env com suas configurações

# 3. Criar ambiente virtual
python3.10 -m venv .venv
source .venv/bin/activate

# 4. Instalar PyTorch com CUDA
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu126

# 5. Instalar Unsloth
pip install "unsloth[colab-new] @ git+https://github.com/unslothai/unsloth.git"

# 6. Instalar outras dependências
pip install -r requirements.txt

# 7. Iniciar banco de dados
docker-compose up -d

# 8. Executar o agente
python main.py
```

## 📚 Documentação

- **[INSTALL.md](INSTALL.md)** - Guia completo de instalação passo a passo
- **[PROPOSTAS_MELHORIAS.md](PROPOSTAS_MELHORIAS.md)** - Propostas de melhorias no código para facilitar instalação

## 🏗️ Arquitetura

O projeto utiliza:

- **LangGraph**: Para construção do grafo de agente
- **Unsloth + Qwen3**: Modelo LLM base com fine-tuning LoRA
- **PostgreSQL**: Banco de dados relacional
- **LangChain**: Framework para construção de agentes
- **Docker**: Para containerização do banco de dados

## 📁 Estrutura do Projeto

```
tech-challenge-3/
├── INSTALL.md              # Guia de instalação completo
├── PROPOSTAS_MELHORIAS.md  # Propostas de melhorias
├── env.example             # Template de configuração
├── requirements.txt        # Dependências Python
├── docker-compose.yaml     # Configuração do PostgreSQL
├── config.py               # Configurações do projeto
├── main.py                 # Ponto de entrada principal
├── agent_graph.py          # Definição do grafo LangGraph
├── llm_model.py            # Carregamento e uso do modelo LoRA
├── tools.py                # Ferramentas do agente (SQL, agendamento)
├── monitoring.py           # Sistema de monitoramento
├── logging_llm.py          # Configuração de logging
├── lora/                   # Scripts de preparação e treinamento
│   ├── 01-clonar-repo-trata-dados.py
│   ├── 02-converte-xml-vector.py
│   └── 03-treinamento-lora.py
└── init_files/             # Scripts SQL de inicialização
    └── init.sql
```

## 🔧 Configuração

1. Copie `env.example` para `.env`
2. Edite o arquivo `.env` com suas configurações:
   - Caminho do modelo LoRA
   - Configurações do banco de dados
   - Modo de execução do agente

## 🎯 Funcionalidades

- **Consulta de Informações**: Busca de especialidades, médicos, pacientes, consultas
- **Agendamento de Consultas**: Verificação de disponibilidade e agendamento automático
- **Chat Interativo**: Interface de conversação natural em português
- **Monitoramento**: Sistema de métricas e logging detalhado

## 🚦 Uso

### Modo de Teste

```bash
export AGENT_MODE=TESTE  # Linux/macOS
python main.py
```

### Modo Interativo

```bash
export AGENT_MODE=INTERATIVO  # Linux/macOS
python main.py
```

## 📝 Notas de Instalação

### Instalação Manual (Resumo)

As dependências principais devem ser instaladas nesta ordem:

1. **PyTorch com CUDA** (instalar primeiro)
2. **Unsloth** (instala automaticamente transformers, datasets, trl, etc.)
3. **Outras dependências** via `requirements.txt`

Consulte o [INSTALL.md](INSTALL.md) para instruções detalhadas.

### Treinamento do Modelo LoRA

Para treinar seu próprio modelo:

1. Execute `lora/01-clonar-repo-trata-dados.py` para preparar dados
2. Execute `lora/02-converte-xml-vector.py` para converter para JSONL
3. Execute `lora/03-treinamento-lora.py` para treinar o modelo

**Requisitos**: GPU com 8GB+ VRAM, processo pode levar várias horas.

## 🐛 Troubleshooting

Consulte a seção [Troubleshooting](INSTALL.md#troubleshooting) no guia de instalação para soluções de problemas comuns.

## 📄 Licença

[Especificar licença do projeto]

## 🤝 Contribuindo

[Instruções de contribuição]

---

**Última atualização**: Dezembro 2024
