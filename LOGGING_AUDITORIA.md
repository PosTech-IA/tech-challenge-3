# 📋 Sistema de Logging e Auditoria

Este documento descreve o sistema de logging detalhado implementado para rastreamento e auditoria do projeto.

## 🎯 Funcionalidades Implementadas

### ✅ 1. Logging Estruturado (JSON)
- Logs em formato JSON estruturado para fácil processamento
- Formato legível para console (opcional)
- Metadados completos em cada log (timestamp, nível, módulo, função, linha, etc.)

### ✅ 2. Correlation IDs (Request IDs)
- Cada requisição recebe um UUID único
- Request ID propagado por todo o fluxo de execução
- Permite rastrear uma requisição completa através de todos os logs

### ✅ 3. Mascaramento de Dados Sensíveis
- Mascaramento automático de:
  - CPF (***.***.***-**)
  - Telefones ((**) ****-****)
  - Emails (***@dominio.com)
  - Senhas e tokens (***MASKED***)
- Aplicado em logs de SQL queries, tool calls e respostas

### ✅ 4. Auditoria Completa de Operações

#### SQL Queries
- Query executada (mascarada)
- Parâmetros (mascarados)
- Duração em milissegundos
- Número de linhas retornadas
- Status (sucesso/falha)
- Erros (se houver)

#### Tool Calls
- Nome da ferramenta
- Argumentos (mascarados)
- Resultado (mascarado)
- Duração em milissegundos
- Status (sucesso/falha)
- Erros (se houver)

#### LLM Calls
- Modelo usado
- Tamanho do prompt e resposta
- Preview do prompt e resposta (mascarados)
- Duração em milissegundos
- Tokens usados (se disponível)
- Status (sucesso/falha)

#### State Changes
- Estado anterior
- Estado novo
- Contexto adicional

### ✅ 5. Rotação e Retenção de Logs
- Rotação baseada em tamanho (10MB por padrão)
- Mantém até 5 arquivos de backup
- Configurável via variáveis de ambiente

## 📁 Arquivos Criados/Modificados

### Novos Arquivos
- `audit_logging.py` - Sistema completo de logging e auditoria

### Arquivos Modificados
- `logging_llm.py` - Atualizado para usar novo sistema (mantém compatibilidade)
- `tools.py` - Adicionada auditoria de SQL queries e tool calls
- `main.py` - Adicionado RequestContext para rastreamento
- `agent_graph.py` - Adicionada auditoria de LLM calls e state changes
- `env.example` - Adicionadas novas variáveis de configuração

## ⚙️ Configuração

### Variáveis de Ambiente

Adicione ao arquivo `.env`:

```bash
# Formato de log (human = legível, json = estruturado JSON)
LOG_FORMAT=human

# Retenção de logs (dias)
LOG_RETENTION_DAYS=30

# Tamanho máximo de arquivo de log antes de rotacionar (bytes)
LOG_MAX_BYTES=10485760  # 10MB

# Número de arquivos de backup a manter
LOG_BACKUP_COUNT=5
```

### Usar Logs em JSON

Para gerar logs em formato JSON (útil para análise automatizada):

```bash
export LOG_FORMAT=json
python main.py
```

## 📊 Exemplos de Logs

### Log Estruturado (JSON)

```json
{
  "timestamp": "2025-12-26T16:30:00.123Z",
  "level": "INFO",
  "logger": "db_tools",
  "message": "Query executada com sucesso",
  "module": "tools",
  "function": "execute_sql_query_impl",
  "line": 75,
  "request_id": "abc123-def456-ghi789",
  "thread_id": 12345,
  "audit": {
    "event_type": "sql_query",
    "query": "SELECT * FROM PACIENTES WHERE CPF = '***.***.***-**'",
    "duration_ms": 45.2,
    "rows_returned": 1,
    "success": true
  }
}
```

### Log Legível (Human)

```
2025-12-26 16:30:00,123 [INFO] [abc12345] db_tools: Query executada com sucesso
```

## 🔍 Rastreamento de Requisições

Cada requisição recebe um Request ID único que aparece em todos os logs relacionados:

```
[abc12345] - Aparece em todos os logs da mesma requisição
```

Isso permite:
- Filtrar logs por requisição específica
- Rastrear o fluxo completo de uma query
- Correlacionar erros com a requisição que os causou

## 🛡️ Segurança

### Dados Mascarados Automaticamente

- **CPF**: `123.456.789-00` → `***.***.***-**`
- **Telefone**: `(11) 98765-4321` → `(**) ****-****`
- **Email**: `usuario@exemplo.com` → `***@exemplo.com`
- **Senhas/Tokens**: `password: senha123` → `password: ***MASKED***`

### O que é Auditado

✅ Todas as queries SQL (com parâmetros mascarados)  
✅ Todas as chamadas de ferramentas (com argumentos mascarados)  
✅ Todas as chamadas ao LLM (com previews mascarados)  
✅ Todas as mudanças de estado no grafo  
✅ Todos os erros e exceções  

## 📈 Métricas Coletadas

Para cada operação auditada:
- **Timestamp** preciso
- **Duração** em milissegundos
- **Status** (sucesso/falha)
- **Dados relevantes** (mascarados)
- **Request ID** para correlação

## 🔧 Uso Programático

### Usar RequestContext

```python
from audit_logging import RequestContext

with RequestContext() as request_id:
    # Todo código aqui terá o mesmo request_id
    # nos logs
    do_something()
```

### Auditoria Manual

```python
from audit_logging import audit_sql_query, audit_tool_call, audit_llm_call

# Auditoria de SQL
audit_sql_query(
    logger,
    query="SELECT * FROM ...",
    duration_ms=45.2,
    rows_returned=10,
    success=True
)

# Auditoria de Tool
audit_tool_call(
    logger,
    tool_name="SQL_query_tool",
    arguments={"query": "SELECT ..."},
    result={"status": "ok"},
    duration_ms=50.1,
    success=True
)

# Auditoria de LLM
audit_llm_call(
    logger,
    prompt="...",
    response="...",
    model="unsloth/Qwen3-1.7B",
    duration_ms=1200.5,
    tokens_used=150,
    success=True
)
```

## 📝 Logs Gerados

Os seguintes arquivos de log são gerados em `logs/`:

- `main.log` - Logs do módulo principal
- `agent_graph.log` - Logs do grafo do agente
- `db_tools.log` - Logs de operações SQL
- `tools.log` - Logs de ferramentas
- `monitoring.log` - Logs de monitoramento
- `llm_model.log` - Logs do modelo LLM

Cada arquivo é rotacionado automaticamente quando atinge o tamanho máximo.

## 🎯 Benefícios

1. **Rastreabilidade Completa**: Cada requisição pode ser rastreada do início ao fim
2. **Auditoria**: Todas as operações críticas são registradas
3. **Segurança**: Dados sensíveis são automaticamente mascarados
4. **Análise**: Logs estruturados facilitam análise automatizada
5. **Debugging**: Request IDs facilitam identificar problemas específicos
6. **Compliance**: Atende requisitos de auditoria e rastreamento

## 🔄 Compatibilidade

O sistema mantém compatibilidade com código existente. A função `setup_logger()` continua funcionando, mas agora usa o novo sistema internamente.

---

**Última atualização**: Dezembro 2024

