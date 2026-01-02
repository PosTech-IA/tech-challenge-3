# main.py

import sys
import os
import operator
import json
import warnings
from typing import List, Dict, Any

from langchain_core.messages import HumanMessage
import logging
from dotenv import load_dotenv

# Suprimir warnings do transformers e unsloth
warnings.filterwarnings('ignore', message='.*generation_config.*default values.*')
warnings.filterwarnings('ignore', message='.*Unsloth should be imported before.*')

# Carregar variáveis de ambiente
load_dotenv()

# Importar o grafo
from agent_graph import build_agent_graph
from config import DB_NAME
from logging_llm import setup_logger  # Importar sua função de logging
from audit_logging import RequestContext, get_request_id  # Sistema de auditoria

# ==============================================================================
# 1. CONFIGURAÇÃO DE LOGGING
# ==============================================================================

# Desabilitar propagação para o logger root para evitar logs duplicados
root_logger = logging.getLogger()
root_logger.setLevel(logging.WARNING)
# Remove todos os handlers do root logger
for handler in root_logger.handlers[:]:
    root_logger.removeHandler(handler)
# Desabilitar propagação para evitar que logs subam para o root
root_logger.propagate = False

# Configurar loggers usando a função do logging_llm.py
setup_logger("main", "main.log", logging.DEBUG)
setup_logger("agent_graph", "agent_graph.log", logging.DEBUG)
setup_logger("monitoring", "monitoring.log", logging.DEBUG)
setup_logger("tools", "tools.log", logging.DEBUG)
setup_logger("agent_graph_monitor", "monitoring.log", logging.DEBUG)  # Logger usado pelo MonitoringSystem

# Obter logger para o main
main_logger = logging.getLogger("main")

# ==============================================================================
# 2. FUNÇÕES DE EXECUÇÃO COM LOGGING
# ==============================================================================

def invoke_agent(graph_app, user_input: str, monitor):
    """
    Invoca o agente com uma query de usuário.
    Usa RequestContext para rastreamento completo da requisição.
    """
    # Criar contexto de requisição com request_id único
    with RequestContext() as request_id:
        main_logger.info("="*70)
        main_logger.info(f"AGENTE Dr. IA INICIADO | Request ID: {request_id} | Query: {user_input}")
        main_logger.info("="*70)
        
        # Prints originais comentados para interface limpa
        # print("\n" + "#"*70)
        # print(f"🤖 AGENTE Dr. IA INICIADO | Request ID: {request_id[:8]}")
        # print(f"Query: {user_input}")
        # print("#"*70)
        
        # Inicia o estado com a mensagem do usuário
        initial_state = {
            "messages": [HumanMessage(content=user_input)],
            "monitoring_data": {},
            "request_id": request_id  # Adicionar request_id ao estado
        }
        
        monitor.metrics["total_requests"] += 1
        main_logger.debug(f"Métrica atualizada: total_requests = {monitor.metrics['total_requests']}")
        
        final_output = None
        
        try:
            # Invocar o grafo
            main_logger.info(f"Iniciando stream do grafo [Request ID: {request_id[:8]}]...")
            for step in graph_app.stream(initial_state):
                name, state = next(iter(step.items()))
                main_logger.debug(f"Passo do grafo: {name} [Request ID: {request_id[:8]}]")
                
                if name == 'monitor_end':
                    final_output = state
                    main_logger.info(f"Nó monitor_end alcançado [Request ID: {request_id[:8]}]")
                    break

            # Processar a saída final
            if final_output and final_output.get('messages'):
                last_message = final_output['messages'][-1]
                main_logger.info("="*70)
                main_logger.info(f"RESPOSTA FINAL DO AGENTE [Request ID: {request_id[:8]}]")
                main_logger.info("="*70)
                
                # Prints originais comentados para interface limpa
                # print("\n" + "="*70)
                # print(f"✨ RESPOSTA FINAL DO AGENTE ✨ [Request ID: {request_id[:8]}]")
                # print("="*70)
                # print(last_message.content)
                # print("="*70)
                
                # Mostrar apenas a resposta do agente (limpo e simples)
                print(f"\n{last_message.content}\n")
                
                # Log da resposta (apenas primeiros 500 caracteres para não poluir)
                main_logger.info(f"Resposta final [Request ID: {request_id[:8]}] (primeiros 500 chars): {last_message.content[:500]}...")
            else:
                main_logger.warning(f"O grafo não retornou uma mensagem final [Request ID: {request_id[:8]}]")
                # Print original comentado
                # print("\n⚠️ O grafo não retornou uma mensagem final.")
                print("\n⚠️ Desculpe, não consegui processar sua solicitação. Tente novamente.")
                
        except Exception as e:
            monitor.metrics["errors"] += 1
            main_logger.error(f"ERRO [Request ID: {request_id[:8]}]: Exceção fatal durante a execução do grafo: {e}", exc_info=True)
            
            # Prints originais comentados para interface limpa
            # print("\n" + "🚨"*10)
            # print(f"[DrIA_Agent|ERROR]🚨 ERRO [Request ID: {request_id[:8]}]: Exceção fatal durante a execução do grafo: {e}")
            # import traceback
            # traceback.print_exc()
            # print("🚨"*10)
            
            print("\n❌ Ocorreu um erro ao processar sua solicitação. Por favor, tente novamente.")

def run_tests(app, monitor):
    """
    Executa um conjunto fixo de queries para teste.
    """
    main_logger.info("-"*60)
    main_logger.info("MODO DE TESTE (AGENT_MODE=TESTE) ATIVADO")
    main_logger.info("-"*60)
    
    # Prints originais comentados para interface limpa
    # print("\n" + "---"*20)
    # print("🧪 MODO DE TESTE (AGENT_MODE=TESTE) ATIVADO 🧪")
    # print("---"*20)
    
    print("\n🧪 Executando testes...\n")
    
    test_queries = [
        "Quais especialidades temos no hospital?",
        "Liste todos os médicos com suas especialidades",
        "Gostaria de agendar uma consulta com cardiologista para amanhã às 10:00"
    ]
    
    main_logger.info(f"Executando {len(test_queries)} queries de teste")
    
    for i, query in enumerate(test_queries, 1):
        main_logger.info(f"Teste {i}/{len(test_queries)}: '{query}'")
        print(f"Teste {i}: {query}")
        print("Dr. IA: ", end="", flush=True)
        invoke_agent(app, query, monitor)
        print()  # Linha em branco entre testes

def run_interactive_chat(app, monitor):
    """
    Executa o loop de chat interativo.
    """
    main_logger.info("-"*60)
    main_logger.info("MODO INTERATIVO (CHAT) ATIVADO")
    main_logger.info(f"HOSPITAL: {DB_NAME}")
    main_logger.info("-"*60)
    
    # Prints originais comentados para interface limpa
    # print("\n" + "---"*20)
    # print("💬 MODO INTERATIVO (CHAT) ATIVADO 💬")
    # print(f"HOSPITAL: {DB_NAME}")
    # print("---"*20)
    
    # Mensagem de boas-vindas simples
    print(f"\n👋 Olá! Sou o Dr. IA do Hospital {DB_NAME}.")
    print("Como posso ajudá-lo hoje? (Digite 'sair' para encerrar)")
    
    while True:
        try:
            # Input original comentado
            # user_input = input(f"\n\nPergunte ao Dr. IA ({DB_NAME}) ou 'sair':\n> ")
            user_input = input("\nVocê: ")
            if user_input.lower() == 'sair':
                main_logger.info("Usuário solicitou saída do programa")
                # Print original comentado
                # print("\nPrograma encerrado.")
                print("\nAté logo! 👋\n")
                break
            
            if user_input.strip():
                main_logger.info(f"Usuário perguntou: {user_input}")
                print("Dr. IA: ", end="", flush=True)  # Mostra "Dr. IA: " antes da resposta
                invoke_agent(app, user_input, monitor)
            else:
                main_logger.warning("Usuário enviou entrada vazia")
                
        except KeyboardInterrupt:
            main_logger.info("Programa interrompido pelo usuário (Ctrl+C)")
            # Print original comentado
            # print("\nPrograma encerrado por interrupção do usuário.")
            print("\n\nAté logo! 👋\n")
            break
        except Exception as e:
            main_logger.error(f"Erro inesperado no loop principal: {e}", exc_info=True)
            # Print original comentado
            # print(f"Erro inesperado no loop principal: {e}")
            print("\n❌ Ocorreu um erro. Por favor, tente novamente.\n")

def main():
    """Função principal de execução"""
    
    # Verificar se o arquivo .env existe (opcional, apenas aviso)
    if not os.path.exists('.env'):
        print("⚠️  AVISO: Arquivo .env não encontrado. Usando valores padrão.")
        print("   Para personalizar, copie env.example para .env e ajuste os valores.")
        main_logger.warning("Arquivo .env não encontrado. Usando valores padrão.")
    
    main_logger.info("="*60)
    main_logger.info("INICIANDO DR. IA AGENT")
    main_logger.info("="*60)
    
    # Prints originais comentados para interface limpa
    # print("\n" + "="*60)
    # print("🚀 INICIANDO DR. IA AGENT")
    # print("="*60)
    
    # 1. Construir e compilar o grafo
    main_logger.info("Construindo grafo do agente...")
    app = build_agent_graph()
    main_logger.info("Grafo do agente construído com sucesso")
    
    # Obter a instância do monitor do grafo
    from agent_graph import monitor
    
    # 2. Verificar o modo de execução via Variável de Ambiente
    agent_mode = os.getenv('AGENT_MODE', 'TESTE').upper()
    main_logger.info(f"Modo de execução: {agent_mode}")
    
    if agent_mode == 'TESTE':
        run_tests(app, monitor)
    else:
        run_interactive_chat(app, monitor)

    # 3. Exibir métricas finais (apenas em logs, não no console)
    main_logger.info("-"*60)
    main_logger.info("SUMÁRIO FINAL DE MONITORAMENTO")
    main_logger.info("-"*60)
    
    metrics_summary = monitor.get_metrics_summary()
    main_logger.info(f"Métricas finais: {json.dumps(metrics_summary, indent=2)}")
    
    # Prints originais comentados para interface limpa
    # print("\n" + "---"*20)
    # print("📈 SUMÁRIO FINAL DE MONITORAMENTO")
    # print("---"*20)
    # print(json.dumps(metrics_summary, indent=4, ensure_ascii=False))
    
    # Métricas finais apenas em logs, não no console para não poluir
    # (descomente a linha abaixo se quiser ver as métricas no final)
    # print(f"\n📊 Sessão finalizada: {metrics_summary['total_requests']} requisições processadas")
    
    main_logger.info("="*60)
    main_logger.info("DR. IA AGENT FINALIZADO")
    main_logger.info("="*60)

if __name__ == "__main__":
    main()