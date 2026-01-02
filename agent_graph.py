# agent_graph.py

import operator
import time
import re
import json
import warnings
from typing import TypedDict, Annotated, List, Dict, Any
import logging
import logging_llm
from langchain_core.messages import BaseMessage, HumanMessage, ToolMessage, AIMessage
from langgraph.graph import StateGraph, END

# Suprimir warnings do transformers sobre generation_config
warnings.filterwarnings('ignore', message='.*generation_config.*default values.*')
warnings.filterwarnings('ignore', category=UserWarning, module='transformers')

from config import SYSTEM_PROMPT, DB_NAME
from monitoring import MonitoringSystem
from tools import tool_map, tools
import psycopg2
from psycopg2 import extras
from transformers import GenerationConfig
from llm_model import (
    model, 
    tokenizer, 
    convert_messages_to_qwen_format, 
    convert_tools_to_qwen_format, 
    parse_tool_calls_from_response, 
    clean_llm_response,
    compress_context
)
from audit_logging import audit_llm_call, audit_state_change, get_request_id

# ==============================================================================
# 1. CONFIGURAÇÃO DE LOGGING
# ==============================================================================

# Criar logger para o agent_graph
agent_logger = logging.getLogger("agent_graph")

# ==============================================================================
# 2. DEFINIÇÃO DO ESTADO DO AGENTE COM MONITORING
# ==============================================================================

class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], operator.add]
    monitoring_data: Dict[str, Any] 

# ==============================================================================
# 3. NÓS DO LANGGRAPH COM MONITORING E LOGGING
# ==============================================================================

def monitor_node(state: AgentState):
    """
    NÓ DE MONITORAMENTO - Coleta métricas e analytics
    """
    start_time = time.time()
    
    agent_logger.info("MONITOR NODE - Analytics em Tempo Real")
    
    # Auditoria de state change
    request_id = get_request_id()
    previous_state = "execute_tools" if state.get('messages') and len(state['messages']) > 0 else "initial"
    audit_state_change(agent_logger, previous_state, "monitor", {"request_id": request_id})
    
    # Coletar métricas do estado atual
    last_message = state['messages'][-1] if state.get('messages') else None
    
    # Exibir analytics (comentado para interface limpa - ainda logado)
    # monitor.print_real_time_metrics("monitor", state)  # Comentado para interface limpa
    
    # Análise detalhada do estado
    if last_message:
        if isinstance(last_message, AIMessage) and last_message.tool_calls:
            agent_logger.info(f"Tool Calls Detectados: {len(last_message.tool_calls)}")
            for tc in last_message.tool_calls:
                agent_logger.debug(f"Tool: {tc['name']} - Args: {tc.get('args', {})}")
        elif isinstance(last_message, ToolMessage):
            agent_logger.info(f"Última Tool Result: {last_message.content[:100]}...")
        elif isinstance(last_message, AIMessage):
            agent_logger.info(f"Resposta do Assistente: {last_message.content[:100]}...")
    
    duration = time.time() - start_time
    monitor.log_node_execution("monitor", duration)
    
    agent_logger.debug("="*60)
    return state

def call_model_with_tools(state: AgentState):
    """Nó 1: LLM (Qwen3) que decide qual tool usar, sem forçar ferramentas de consulta."""
    start_time = time.time()
    
    agent_logger.info("="*40)
    agent_logger.info("NÓ: call_model_with_tools (LLM)")
    
    # Auditoria de state change
    request_id = get_request_id()
    audit_state_change(agent_logger, "previous", "call_model", {"request_id": request_id})
    
    messages = state["messages"]
    
    # COMPRIMIR CONTEXTO
    compressed_messages = compress_context(messages)
    agent_logger.info(f"Contexto comprimido: {len(messages)} -> {len(compressed_messages)} mensagens")
    
    # Garantir system prompt
    system_prompt_found = any(
        isinstance(msg, HumanMessage) and hasattr(msg, 'name') and msg.name == 'system' 
        for msg in compressed_messages
    )
    
    if not system_prompt_found:
        compressed_messages.insert(0, HumanMessage(content=SYSTEM_PROMPT, name="system"))
    
    # Converter formatos para Qwen3
    qwen_messages = convert_messages_to_qwen_format(compressed_messages)
    # CRÍTICO: 'tools' deve conter a nova tool 'check_and_schedule_availability'
    qwen_tools = convert_tools_to_qwen_format(tools)
    
    # Aplicar template
    text_input = tokenizer.apply_chat_template(
        qwen_messages,
        tokenize=False,
        add_generation_prompt=True,
        tools=qwen_tools,
    )
    
    inputs = tokenizer(text_input, return_tensors="pt").to(model.device)
    
    # Configurar GenerationConfig com todos os parâmetros explicitamente para evitar warnings
    # O warning aparece porque o transformers quer que definamos explicitamente os valores padrão
    generation_config = GenerationConfig(
        max_new_tokens=800,
        max_length=40960,  # Valor padrão do modelo
        temperature=0.7, 
        do_sample=False,
        top_k=20,  # Valor padrão do modelo
        top_p=0.95,  # Valor padrão do modelo
        pad_token_id=tokenizer.eos_token_id,
        eos_token_id=tokenizer.eos_token_id,
        bos_token_id=151643,  # Valor padrão do modelo
    )

    # Extrair prompt para auditoria
    prompt_for_audit = text_input[-1000:] if len(text_input) > 1000 else text_input
    
    output_tokens = model.generate(**inputs, generation_config=generation_config)
    response_text = tokenizer.decode(output_tokens[0], skip_special_tokens=False)
    
    agent_logger.debug(f"Resposta bruta do LLM (primeiros 500 chars):\n{response_text[:500]}...")
    
    # Parse tool calls PRIMEIRO
    tool_calls = parse_tool_calls_from_response(response_text)
    
    if tool_calls:
        # EXTRAIR THINKING MESMO COM TOOL CALLS
        think_content = ""
        if "<think>" in response_text and "</think>" in response_text:
            think_match = re.search(r'<think>(.*?)</think>', response_text, re.DOTALL)
            if think_match:
                think_content = think_match.group(1).strip()
                agent_logger.debug(f"Thinking com tool call: {think_content[:100]}...")
        
        # SE TEM THINKING, criar mensagem com thinking + tool calls
        if think_content:
            ai_message = AIMessage(
                content=f"**Raciocínio do Assistente:**\n\n{think_content}",
                tool_calls=tool_calls
            )
        else:
            ai_message = AIMessage(content="", tool_calls=tool_calls)
            
        agent_logger.info(f"Tool Call detectado: {tool_calls[0]['name']}")
        result = {"messages": [ai_message]}
        response_for_audit = f"Tool calls: {[tc['name'] for tc in tool_calls]}"
    else:
        # SEM TOOL CALLS: limpeza normal
        clean_response = clean_llm_response(response_text, text_input)
        agent_logger.info(f"Resposta limpa: {clean_response[:100]}...")
        result = {"messages": [AIMessage(content=clean_response)]}
        response_for_audit = clean_response
    
    duration = time.time() - start_time
    duration_ms = duration * 1000
    
    # Auditoria da chamada LLM
    from config import MODEL_BASE
    audit_llm_call(
        agent_logger,
        prompt=prompt_for_audit,
        response=response_for_audit,
        model=MODEL_BASE,
        duration_ms=duration_ms,
        tokens_used=len(output_tokens[0]) if output_tokens is not None else None,
        success=True
    )
    
    monitor.log_node_execution("call_model", duration)
    agent_logger.debug(f"Tempo de execução do nó call_model: {duration:.2f}s")
    
    return result

def generate_natural_response(tool_results: List[Dict], state: AgentState) -> str:
    """Gera resposta natural baseada nos resultados das tools - VERSÃO CORRIGIDA"""
    
    user_query = ""
    # Achar a última mensagem de usuário para contexto
    for msg in reversed(state["messages"]):
        if isinstance(msg, HumanMessage) and (not hasattr(msg, 'name') or msg.name != 'system'):
            user_query = msg.content.lower()
            break
    
    tool_result = tool_results[0]
    tool_name = tool_result["name"]
    tool_output = tool_result["output"]
    
    agent_logger.info(f"Gerando resposta para: '{user_query}'")
    
    try:
        data = json.loads(tool_output)
        
        if tool_name == "SQL_query_tool":
            # DETECÇÃO MAIS INTELIGENTE BASEADA NOS DADOS
            if isinstance(data, list) and len(data) > 0:
                first_item = data[0]
                
                # SE TEM 'nome' E 'nome_especialidade' → É LISTA DE MÉDICOS
                if 'nome' in first_item and 'nome_especialidade' in first_item:
                    medicos = [f"**{item['nome']}** - {item['nome_especialidade']}" for item in data]
                    return f"**Corpo Médico do Hospital {DB_NAME}:**\n\n" + "\n".join(medicos) + f"\n\nTotal de {len(medicos)} profissionais em nossa equipe."
                
                # SE TEM APENAS 'nome_especialidade' → É LISTA DE ESPECIALIDADES
                elif 'nome_especialidade' in first_item and 'nome' not in first_item:
                    especialidades = [item['nome_especialidade'] for item in data]
                    return f"**Especialidades Médicas Disponíveis:**\n\nNo hospital {DB_NAME}, temos {len(especialidades)} especialidades:\n\n• " + "\n• ".join(especialidades) + f"\n\nEstas são todas as especialidades do nosso corpo clínico."
                
                # SE TEM 'nome' APENAS → É LISTA DE NOMES
                elif 'nome' in first_item:
                    nomes = [item['nome'] for item in data]
                    return f"**Registros Encontrados ({len(data)}):**\n\n• " + "\n• ".join(nomes)
            
            # Resposta para lista vazia
            elif isinstance(data, list) and len(data) == 0:
                return "**Resultado da Consulta:**\n\nNão encontrei registros correspondentes à sua pesquisa."
            
            # Resposta genérica
            else:
                return f"📊 **Consulta Realizada:**\n\nProcessei sua solicitação e obtive {len(data) if isinstance(data, list) else 1} registro(s)."
        
        elif tool_name == "check_and_schedule_availability":
            # O output já é um JSON
            agendamento_data = data
            if agendamento_data.get("status") == "agendado_sucesso":
                return f"**Agendamento Confirmado!**\n\n• Médico: {agendamento_data.get('medico', 'N/A')}\n• Especialidade: {agendamento_data.get('especialidade', 'N/A')}\n• Data/Hora: {agendamento_data.get('data', 'N/A')}\n\n{agendamento_data.get('mensagem', 'Agendamento realizado com sucesso!')}"
            else:
                return f"❌ **Falha no Agendamento:**\n\n{agendamento_data.get('mensagem', 'Não foi possível completar o agendamento.')}"
        
        # Fallback genérico para JSON que não se encaixa nas regras
        return f"🤖 **Resposta Final:**\n\nConsegui processar sua solicitação e os dados obtidos foram:\n{tool_output[:500]}..."

    except json.JSONDecodeError:
        # Se a tool retornou algo que não é JSON (ex: erro de conexão do DB)
        agent_logger.error(f"Erro JSON ao processar output da tool {tool_name}: {tool_output[:200]}")
        return f"**Alerta do Sistema:**\n\nA ferramenta retornou um erro inesperado:\n\n{tool_output}"
    except Exception as e:
        agent_logger.error(f"Erro ao gerar resposta natural: {e}")
        return f"**Erro na Geração da Resposta:**\n\nHouve um erro ao formatar os dados de resposta: {e}"

def execute_tools(state: AgentState):
    """Nó 2: Executa tools e GERA RESPOSTA NATURAL"""
    start_time = time.time()
    
    agent_logger.info("="*40)
    agent_logger.info("NÓ: execute_tools (Tool Execution + Resposta Natural)")
    
    # Auditoria de state change
    request_id = get_request_id()
    audit_state_change(agent_logger, "call_model", "execute_tools", {"request_id": request_id})
    
    ai_message = state["messages"][-1]
    
    # PRESERVAR O THINKING DA MENSAGEM ORIGINAL
    # A mensagem pode vir com conteúdo como: "**Raciocínio do Assistente:**..."
    original_thinking = ai_message.content if ai_message.content else ""
    
    if not ai_message.tool_calls:
        agent_logger.error("Última mensagem não continha Tool Calls.")
        duration = time.time() - start_time
        monitor.log_node_execution("execute_tools", duration, success=False)
        return {"messages": [AIMessage(content="Erro: Tool call não encontrado.")]}

    success = True
    tool_results = []
    tool_messages = []
    
    for tool_call in ai_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]
        
        agent_logger.info(f"Executando ferramenta: {tool_name}")
        agent_logger.debug(f"Argumentos: {tool_args}")
            
        if tool_name in tool_map:
            tool_func = tool_map[tool_name]
            try:
                # CRÍTICO: Usa tool_func.invoke(tool_args) onde tool_args já é um dicionário
                tool_output = tool_func.invoke(tool_args) 
                monitor.log_tool_call(tool_name)
                agent_logger.info(f"Resultado da Tool: {tool_output[:200]}...")

                tool_results.append({
                    "name": tool_name,
                    "args": tool_args,
                    "output": tool_output
                })

                tool_messages.append(
                    ToolMessage(
                        content=tool_output,
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    )
                )
            except Exception as e:
                success = False
                error_msg = f"Erro ao executar tool {tool_name}: {str(e)}"
                agent_logger.error(f"{error_msg}")
                tool_messages.append(
                    ToolMessage(
                        content=error_msg,
                        tool_call_id=tool_call["id"],
                        name=tool_name
                    )
                )
        else:
            success = False
            agent_logger.error(f"Tool não encontrada: {tool_name}")
            tool_messages.append(
                ToolMessage(
                    content=f"Erro: Tool '{tool_name}' não encontrada.",
                    tool_call_id=tool_call["id"],
                    name=tool_name
                )
            )
    
    duration = time.time() - start_time
    monitor.log_node_execution("execute_tools", duration, success=success)
    agent_logger.debug(f"Tempo de execução do nó execute_tools: {duration:.2f}s")
    
    # CRÍTICO: GERAR RESPOSTA NATURAL PRESERVANDO THINKING
    # Se houver resultados ou sucesso, tenta gerar uma resposta natural
    if tool_results and success:
        resposta_natural = generate_natural_response(tool_results, state)
        
        # COMBINAR THINKING ORIGINAL COM RESPOSTA NATURAL
        final_response = ""
        # Verifica se o thinking original existe e o anexa
        if original_thinking and "🧠" in original_thinking:
            final_response = f"{original_thinking}\n\n---\n\n{resposta_natural}"
        else:
            final_response = resposta_natural
            
        agent_logger.info(f"RESPOSTA FINAL COM THINKING: {final_response[:150]}...")
        return {"messages": [AIMessage(content=final_response)]}
        
    else:
        # Se falhou, retorna mensagem de erro ou as tool_messages para o LLM re-analisar
        # Aqui, vamos retornar uma mensagem de erro final para evitar loop infinito
        error_msg = "Ocorreu um erro ao processar sua solicitação ou a ferramenta falhou."
        if original_thinking and "🧠" in original_thinking:
            error_msg = f"{original_thinking}\n\n---\n\n{error_msg}"
        
        agent_logger.warning("Falha na execução das tools, retornando tool_messages para re-análise")
        # Se o LLM precisa de mais uma chance, retorne tool_messages para o call_model_with_tools.
        # Caso contrário, retorne AIMessage de erro final.
        return {"messages": tool_messages} # Retorna ToolMessages para o LLM (call_model) tentar novamente.

def route_tools(state: AgentState) -> str:
    """Roteador para decidir o próximo passo"""
    
    last_message = state["messages"][-1]
    
    if isinstance(last_message, AIMessage) and last_message.tool_calls:
        agent_logger.debug("Tool calls detectados. Próximo nó: execute_tools")
        return "execute_tools"
    
    if isinstance(last_message, ToolMessage):
        agent_logger.debug("Resultado de Tool detectado. Próximo nó: call_model_with_tools (Re-análise)")
        return "call_model_with_tools"
    
    agent_logger.debug("Resposta Final detectada. Próximo nó: END")
    return "end"

# ==============================================================================
# 4. CONSTRUÇÃO DO GRAFO
# ==============================================================================

def build_agent_graph():
    """Constrói e compila o grafo do agente"""
    workflow = StateGraph(AgentState)
    
    # Inicializar sistema de monitoramento
    global monitor
    monitor = MonitoringSystem(logger_name='agent_graph_monitor')
    
    agent_logger.info("Iniciando construção do grafo do agente...")

    # 1. Adicionar nós
    workflow.add_node("monitor_start", monitor_node)
    workflow.add_node("call_model_with_tools", call_model_with_tools)
    workflow.add_node("execute_tools", execute_tools)
    workflow.add_node("monitor_end", monitor_node)

    # 2. Definir entrada
    workflow.set_entry_point("monitor_start")

    # 3. Definir edges (conexões)
    
    # Monitor (Início) -> LLM
    workflow.add_edge("monitor_start", "call_model_with_tools")
    
    # LLM -> Roteador
    workflow.add_conditional_edges(
        "call_model_with_tools",
        route_tools,
        {
            "execute_tools": "execute_tools",
            "end": "monitor_end"
        }
    )
    
    # Execução de Tools -> Roteador
    workflow.add_conditional_edges(
        "execute_tools",
        route_tools,
        {
            "call_model_with_tools": "call_model_with_tools", # Tool Message -> LLM re-analisa
            "end": "monitor_end"
        }
    )

    # Monitor (Fim) -> END
    workflow.add_edge("monitor_end", END)

    # 4. Compilar
    app = workflow.compile()
    agent_logger.info("LangGraph compilado com sucesso.")
    
    return app

# A função build_agent_graph será chamada no main.py