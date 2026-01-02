# db_tools.py (REFATORADO)

import json
import time
from typing import Dict, Any
import logging

import psycopg2 
from psycopg2 import extras 
from langchain_core.tools import tool

from config import DB_CONFIG, DB_NAME
from logging_llm import setup_logger  # Importar o setup_logger
from audit_logging import audit_sql_query, audit_tool_call  # Auditoria

# ==============================================================================
# 1. CONFIGURAÇÃO DE LOGGING
# ==============================================================================

# Configurar logger para db_tools
setup_logger("db_tools", "db_tools.log", logging.DEBUG)
db_logger = logging.getLogger("db_tools")

# ==============================================================================
# 2. FUNÇÕES DO BANCO DE DADOS
# ==============================================================================

# Definição das tabelas válidas para consultas (SELECT)
VALID_READ_TABLES = ['PACIENTES', 'ESPECIALIDADES', 'MEDICOS', 'CONSULTAS', 'PRONTUARIOS']
# Definição das tabelas válidas para escrita (INSERT)
VALID_WRITE_TABLES = ['CONSULTAS'] 


def execute_sql_query_impl(query: str) -> str:
    """Implementação da execução SQL (apenas SELECT) com validação de segurança e auditoria."""
    start_time = time.time()
    db_logger.debug("~"*50)
    db_logger.info(f"Iniciando execução de Query SQL (READ)")
    db_logger.debug(f"Query SQL: {query}")
    
    query_lower = query.lower().strip()
    
    # 🎯 Segurança: Apenas SELECT
    if not query_lower.startswith('select'):
        error_msg = "ERRO: Apenas consultas SELECT são permitidas."
        db_logger.error(error_msg)
        duration_ms = (time.time() - start_time) * 1000
        audit_sql_query(db_logger, query, None, duration_ms, None, False, error_msg)
        return json.dumps({"status": "erro_seguranca", "mensagem": error_msg}, ensure_ascii=False)
    
    # 🎯 Validação de Tabelas
    table_used = None
    for table in VALID_READ_TABLES:
        if table.lower() in query_lower:
            table_used = table
            break
    
    if not table_used:
        error_msg = f"ERRO: Tabela não encontrada. Use apenas: {', '.join(VALID_READ_TABLES)}"
        db_logger.error(error_msg)
        duration_ms = (time.time() - start_time) * 1000
        audit_sql_query(db_logger, query, None, duration_ms, None, False, error_msg)
        return json.dumps({"status": "erro_tabela", "mensagem": error_msg}, ensure_ascii=False)
    
    conn = None
    rows_returned = None
    error = None
    success = True
    
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        db_logger.info("Conexão estabelecida com sucesso com o banco de dados")
        
        with conn.cursor(cursor_factory=extras.RealDictCursor) as cur:
            db_logger.debug("Executando comando SQL...")
            cur.execute(query)
            
            result = cur.fetchall()
            rows_returned = len(result)
            db_logger.info(f"SELECT concluído. Linhas retornadas: {rows_returned}")
            
            if len(result) > 0:
                db_logger.debug(f"Primeira linha: {dict(result[0])}")
            else:
                db_logger.debug("Nenhuma linha retornada")
            
            duration_ms = (time.time() - start_time) * 1000
            audit_sql_query(db_logger, query, None, duration_ms, rows_returned, True, None)
                
            return json.dumps(result, ensure_ascii=False, default=str)

    except psycopg2.OperationalError as e:
        error = str(e)
        db_logger.error(f"Falha de CONEXÃO com o banco: {e}", exc_info=True)
        duration_ms = (time.time() - start_time) * 1000
        audit_sql_query(db_logger, query, None, duration_ms, None, False, error)
        return json.dumps({"status": "erro_conexao", "mensagem": f"Erro de conexão: {e}"}, ensure_ascii=False)
        
    except psycopg2.Error as e:
        error = str(e)
        success = False
        db_logger.error(f"Falha de EXECUÇÃO SQL: {e}", exc_info=True)
        if conn:
            conn.rollback()
            db_logger.debug("Rollback executado")
        
        error_suggestion = ""
        if "relation" in str(e) and "does not exist" in str(e):
            error_suggestion = f" Use apenas as tabelas em MAIÚSCULAS: {', '.join(VALID_READ_TABLES)}."
            db_logger.warning(f"Tabela não encontrada: {e}")
        
        duration_ms = (time.time() - start_time) * 1000
        audit_sql_query(db_logger, query, None, duration_ms, None, False, error)
            
        return json.dumps({
            "status": "erro_sql", 
            "mensagem": f"Erro de SQL: {e}",
            "sugestao": error_suggestion
        }, ensure_ascii=False)
        
    finally:
        if conn:
            conn.close()
            db_logger.debug("Conexão com DB fechada")
        db_logger.debug("~"*50)

def _execute_sql_write_impl(query: str, table_name: str) -> bool:
    """Implementação da execução SQL (INSERT/UPDATE/DELETE) com commit."""
    if table_name not in VALID_WRITE_TABLES:
        db_logger.error(f"Tabela não permitida para escrita: {table_name}")
        return False
        
    conn = None
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        db_logger.info(f"Conectando para escrita na tabela: {table_name}")
        
        with conn.cursor() as cur:
            db_logger.debug(f"Executando query de escrita: {query}")
            cur.execute(query)
            conn.commit()
            db_logger.info(f"Escrita concluída com sucesso na tabela {table_name}")
            return True
            
    except psycopg2.Error as e:
        db_logger.error(f"Falha de EXECUÇÃO SQL de escrita: {e}", exc_info=True)
        if conn:
            conn.rollback()
            db_logger.debug("Rollback executado após erro de escrita")
        return False
        
    finally:
        if conn:
            conn.close()
            db_logger.debug("Conexão de escrita fechada")


@tool
def SQL_query_tool(query: str) -> str:
    """Executa uma consulta SELECT SQL no banco de dados"""
    start_time = time.time()
    db_logger.info(f"Chamando SQL_query_tool com query: {query[:100]}...")
    
    result = execute_sql_query_impl(query)
    duration_ms = (time.time() - start_time) * 1000
    
    # Auditoria da tool call
    try:
        result_data = json.loads(result)
        result_preview = str(result_data)[:500] if result_data else None
    except:
        result_preview = result[:500]
    
    audit_tool_call(
        db_logger,
        tool_name="SQL_query_tool",
        arguments={"query": query},
        result=result_preview,
        duration_ms=duration_ms,
        success=True
    )
    
    return result

# ==============================================================================
# 3. NOVAS FERRAMENTAS DE NEGÓCIO
# ==============================================================================

@tool
def check_and_schedule_availability(medico_id: int, data_hora: str, paciente_id: int) -> str:
    """
    VERIFICA se um médico está livre e AGENDA a consulta na tabela CONSULTAS.
    Esta ferramenta DEVE ser usada para finalizar um pedido de agendamento.
    Requer o ID exato do médico, a data/hora exata (YYYY-MM-DD HH:MI:SS) e o ID do paciente.
    """
    start_time = time.time()
    db_logger.info("~"*50)
    db_logger.info(f"Verificação e Agendamento de Consulta")
    db_logger.info(f"Dados: Médico ID={medico_id}, Data/Hora={data_hora}, Paciente ID={paciente_id}")
    
    arguments = {
        "medico_id": medico_id,
        "data_hora": data_hora,
        "paciente_id": paciente_id
    }
    
    try:
        # 1. Checar Disponibilidade (Query SELECT)
        availability_query = f"""
        SELECT consulta_id
        FROM CONSULTAS
        WHERE medico_id = {medico_id} AND data_hora = '{data_hora}';
        """
        
        db_logger.debug(f"Query de verificação de disponibilidade: {availability_query}")
        
        # Reutiliza a função de leitura para checar
        try:
            result_json = execute_sql_query_impl(availability_query)
            result_data = json.loads(result_json)
            db_logger.debug(f"Resultado da verificação: {result_data}")
        except Exception as e:
            db_logger.error(f"Falha ao checar disponibilidade: {e}", exc_info=True)
            error_msg = f"Erro interno ao checar disponibilidade: {e}"
            result = json.dumps({
                "status": "erro_verificacao",
                "mensagem": error_msg
            })
            duration_ms = (time.time() - start_time) * 1000
            audit_tool_call(db_logger, "check_and_schedule_availability", arguments, result, duration_ms, False, error_msg)
            return result

        if result_data:
            # Consulta já existe, médico ocupado
            db_logger.warning(f"Médico {medico_id} está OCUPADO em {data_hora}")
            result = json.dumps({
                "status": "data_indisponivel",
                "mensagem": f"O médico com ID {medico_id} já possui uma consulta agendada para {data_hora}. Por favor, escolha outro horário."
            })
            duration_ms = (time.time() - start_time) * 1000
            audit_tool_call(db_logger, "check_and_schedule_availability", arguments, result, duration_ms, True, None)
            return result
        else:
            # 2. Agendar (Query INSERT)
            insert_query = f"""
            INSERT INTO CONSULTAS (medico_id, paciente_id, data_hora)
            VALUES ({medico_id}, {paciente_id}, '{data_hora}');
            """
            
            db_logger.debug(f"Query de agendamento: {insert_query}")
            
            # Usa a nova função de escrita
            success = _execute_sql_write_impl(insert_query, "CONSULTAS")

            if success:
                db_logger.info(f"Consulta agendada com sucesso! Médico ID={medico_id}, Data={data_hora}")
                # Nota: Em um sistema real, você retornaria o ID da nova consulta
                result = json.dumps({
                    "status": "agendado_sucesso",
                    "medico_id": medico_id,
                    "data_hora": data_hora,
                    "paciente_id": paciente_id,
                    "mensagem": f"Consulta agendada com sucesso com o médico ID {medico_id} para {data_hora}."
                })
                duration_ms = (time.time() - start_time) * 1000
                audit_tool_call(db_logger, "check_and_schedule_availability", arguments, result, duration_ms, True, None)
                return result
            else:
                db_logger.error("Falha ao salvar a consulta no banco")
                error_msg = "Falha ao salvar a consulta no banco de dados"
                result = json.dumps({
                    "status": "erro_persistente",
                    "mensagem": "Falha ao salvar a consulta no banco de dados. Tente novamente mais tarde."
                })
                duration_ms = (time.time() - start_time) * 1000
                audit_tool_call(db_logger, "check_and_schedule_availability", arguments, result, duration_ms, False, error_msg)
                return result
                
    except Exception as e:
        error_msg = str(e)
        db_logger.error(f"Erro inesperado em check_and_schedule_availability: {e}", exc_info=True)
        result = json.dumps({
            "status": "erro_inesperado",
            "mensagem": f"Erro inesperado: {error_msg}"
        })
        duration_ms = (time.time() - start_time) * 1000
        audit_tool_call(db_logger, "check_and_schedule_availability", arguments, result, duration_ms, False, error_msg)
        return result
    finally:
        db_logger.debug("~"*50)


# OBSERVAÇÃO: A antiga tool 'schedule_appointment' foi removida, 
# pois a nova 'check_and_schedule_availability' é mais completa e robusta.

tools = [SQL_query_tool, check_and_schedule_availability]
tool_map = {tool.name: tool for tool in tools}