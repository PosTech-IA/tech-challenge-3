# 📋 Como Ver os Logs de Atividade

Guia rápido para visualizar e analisar os logs do sistema.

## 📁 Localização dos Logs

Todos os logs são salvos no diretório `logs/`:

```
logs/
├── main.log              # Logs do módulo principal
├── agent_graph.log       # Logs do grafo do agente
├── db_tools.log          # Logs de operações SQL
├── tools.log             # Logs de ferramentas
├── monitoring.log        # Logs de monitoramento
└── llm_model.log         # Logs do modelo LLM
```

## 🔍 Formas de Visualizar

### 1. Ver Logs em Tempo Real (Tail)

**Ver todos os logs em tempo real:**
```bash
tail -f logs/*.log
```

**Ver log específico em tempo real:**
```bash
tail -f logs/main.log
tail -f logs/db_tools.log
tail -f logs/agent_graph.log
```

**Ver múltiplos logs simultaneamente:**
```bash
tail -f logs/main.log logs/agent_graph.log logs/db_tools.log
```

### 2. Ver Últimas Linhas

**Últimas 50 linhas de um log:**
```bash
tail -n 50 logs/main.log
```

**Últimas 100 linhas de todos os logs:**
```bash
tail -n 100 logs/*.log
```

### 3. Ver Logs Completos

**Ver todo o conteúdo de um log:**
```bash
cat logs/main.log
less logs/main.log        # Navegação com setas (q para sair)
more logs/main.log        # Paginação (espaço para avançar)
```

### 4. Filtrar por Request ID

**Buscar todas as ocorrências de um Request ID:**
```bash
# Encontre o Request ID primeiro (ex: abc12345)
grep "abc12345" logs/*.log

# Ou mais detalhado
grep -r "abc12345" logs/
```

**Ver logs de uma requisição específica:**
```bash
# Substitua REQUEST_ID pelo ID que você quer rastrear
grep -A 5 -B 5 "REQUEST_ID" logs/*.log
```

### 5. Filtrar por Tipo de Evento

**Ver apenas queries SQL:**
```bash
grep "sql_query" logs/db_tools.log
```

**Ver apenas tool calls:**
```bash
grep "tool_call" logs/tools.log
```

**Ver apenas chamadas LLM:**
```bash
grep "llm_call" logs/agent_graph.log
```

**Ver apenas erros:**
```bash
grep -i "error\|exception\|erro" logs/*.log
```

### 6. Ver Logs por Data/Hora

**Logs de hoje:**
```bash
grep "$(date +%Y-%m-%d)" logs/*.log
```

**Logs de uma data específica:**
```bash
grep "2025-12-26" logs/*.log
```

**Logs das últimas horas:**
```bash
# Última hora
grep "$(date -d '1 hour ago' +%Y-%m-%d)" logs/*.log
```

### 7. Ver Logs Estruturados (JSON)

Se você configurou `LOG_FORMAT=json`, os logs estarão em JSON:

**Ver e formatar JSON:**
```bash
# Ver último log JSON formatado
tail -n 1 logs/main.log | python3 -m json.tool

# Ver todos os logs JSON formatados
cat logs/main.log | python3 -m json.tool | less
```

**Filtrar logs JSON por campo:**
```bash
# Ver apenas logs de erro
cat logs/main.log | python3 -c "import json, sys; [print(json.dumps(json.loads(line), indent=2)) for line in sys.stdin if json.loads(line).get('level') == 'ERROR']"

# Ver apenas logs com request_id específico
cat logs/main.log | python3 -c "import json, sys; [print(json.dumps(json.loads(line), indent=2)) for line in sys.stdin if json.loads(line).get('request_id') == 'SEU_REQUEST_ID']"
```

### 8. Estatísticas dos Logs

**Contar erros:**
```bash
grep -c "ERROR\|ERRO" logs/*.log
```

**Contar queries SQL:**
```bash
grep -c "sql_query" logs/db_tools.log
```

**Ver distribuição de níveis de log:**
```bash
grep -o "\[INFO\]\|\[ERROR\]\|\[WARNING\]\|\[DEBUG\]" logs/*.log | sort | uniq -c
```

### 9. Buscar Texto Específico

**Buscar por texto em todos os logs:**
```bash
grep -r "texto_a_buscar" logs/
```

**Buscar com contexto (linhas antes e depois):**
```bash
grep -A 10 -B 10 "texto_a_buscar" logs/main.log
```

**Buscar case-insensitive:**
```bash
grep -i "texto" logs/*.log
```

### 10. Ver Logs de Auditoria Específicos

**Ver apenas logs de auditoria (com campo 'audit'):**
```bash
# Se estiver em formato JSON
cat logs/db_tools.log | python3 -c "import json, sys; [print(json.dumps(json.loads(line), indent=2)) for line in sys.stdin if 'audit' in json.loads(line)]"
```

**Ver todas as queries SQL auditadas:**
```bash
grep "event_type.*sql_query" logs/db_tools.log
```

**Ver todas as tool calls auditadas:**
```bash
grep "event_type.*tool_call" logs/tools.log
```

## 🎯 Comandos Úteis Combinados

### Ver Logs Recentes de Erros
```bash
tail -n 100 logs/*.log | grep -i error
```

### Ver Logs de uma Sessão Completa (por Request ID)
```bash
# 1. Execute o programa e anote o Request ID do início
# 2. Busque todas as ocorrências
grep "SEU_REQUEST_ID" logs/*.log | less
```

### Monitorar Erros em Tempo Real
```bash
tail -f logs/*.log | grep --line-buffered -i error
```

### Ver Resumo de Atividade
```bash
echo "=== RESUMO DE LOGS ===" && \
echo "Total de linhas:" && wc -l logs/*.log && \
echo -e "\nErros:" && grep -c "ERROR\|ERRO" logs/*.log && \
echo -e "\nQueries SQL:" && grep -c "sql_query" logs/db_tools.log && \
echo -e "\nTool Calls:" && grep -c "tool_call" logs/tools.log
```

## 📊 Análise Avançada

### Script Python para Análise de Logs JSON

Crie um script `analyze_logs.py`:

```python
import json
from collections import Counter
from pathlib import Path

log_dir = Path("logs")

# Contar eventos por tipo
event_types = Counter()
request_ids = Counter()
errors = []

for log_file in log_dir.glob("*.log"):
    with open(log_file) as f:
        for line in f:
            try:
                log_data = json.loads(line.strip())
                if 'audit' in log_data:
                    event_type = log_data['audit'].get('event_type')
                    if event_type:
                        event_types[event_type] += 1
                
                if 'request_id' in log_data:
                    request_ids[log_data['request_id']] += 1
                
                if log_data.get('level') == 'ERROR':
                    errors.append(log_data)
            except:
                pass

print("=== ESTATÍSTICAS ===")
print(f"\nEventos por tipo:")
for event, count in event_types.most_common():
    print(f"  {event}: {count}")

print(f"\nTotal de requisições: {len(request_ids)}")
print(f"\nTotal de erros: {len(errors)}")
```

Execute:
```bash
python analyze_logs.py
```

## 🔧 Configuração para Melhor Visualização

### Usar `less` com cores (se disponível)
```bash
less -R logs/main.log
```

### Usar `bat` (se instalado) - visualizador moderno
```bash
bat logs/main.log
```

### Usar `jq` para logs JSON (se instalado)
```bash
cat logs/main.log | jq '.'
cat logs/main.log | jq 'select(.level == "ERROR")'
```

## 💡 Dicas

1. **Request IDs**: Cada requisição tem um ID único. Use-o para rastrear todo o fluxo.

2. **Logs em JSON**: Se usar `LOG_FORMAT=json`, os logs são mais fáceis de processar programaticamente.

3. **Rotação**: Os logs são rotacionados automaticamente quando atingem 10MB.

4. **Mascaramento**: Dados sensíveis são automaticamente mascarados nos logs.

5. **Múltiplos Terminais**: Use um terminal para executar o programa e outro para ver os logs em tempo real.

---

**Exemplo Prático:**

```bash
# Terminal 1: Ver logs em tempo real
tail -f logs/main.log logs/db_tools.log

# Terminal 2: Executar o programa
python main.py
```

Os logs aparecerão em tempo real no Terminal 1!

