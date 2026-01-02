"""
Sistema de Logging Avançado para Auditoria e Rastreamento
Implementa logging estruturado (JSON), correlation IDs, mascaramento de dados sensíveis,
e rotação de logs.
"""

import logging
import json
import os
import re
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from contextvars import ContextVar
import threading

# Context variable para armazenar o request_id atual
request_id_context: ContextVar[str] = ContextVar('request_id', default=None)

# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

LOG_DIR = os.getenv('LOG_DIR', 'logs')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '30'))
# LOG_MAX_BYTES: 10MB por padrão
LOG_MAX_BYTES = int(os.getenv('LOG_MAX_BYTES', str(10 * 1024 * 1024)))
LOG_BACKUP_COUNT = int(os.getenv('LOG_BACKUP_COUNT', '5'))

# Padrões para mascaramento de dados sensíveis
SENSITIVE_PATTERNS = {
    'cpf': r'\b\d{3}\.?\d{3}\.?\d{3}-?\d{2}\b',
    'phone': r'\(?\d{2}\)?\s?\d{4,5}-?\d{4}',
    'email': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
    'password': r'(?i)(password|senha|pwd)\s*[:=]\s*["\']?([^"\'\s]+)',
    'token': r'(?i)(token|api_key|secret)\s*[:=]\s*["\']?([A-Za-z0-9_-]{20,})',
}

# ==============================================================================
# FUNÇÕES DE MASCARAMENTO
# ==============================================================================

def mask_sensitive_data(text: str) -> str:
    """
    Mascara dados sensíveis em strings de texto.
    """
    if not isinstance(text, str):
        text = str(text)
    
    masked = text
    
    # Mascarar CPF
    masked = re.sub(SENSITIVE_PATTERNS['cpf'], r'***.***.***-**', masked)
    
    # Mascarar telefone
    masked = re.sub(SENSITIVE_PATTERNS['phone'], r'(**) ****-****', masked)
    
    # Mascarar email (mantém domínio visível)
    masked = re.sub(
        SENSITIVE_PATTERNS['email'],
        lambda m: f"***@{m.group(0).split('@')[1]}",
        masked
    )
    
    # Mascarar senhas e tokens
    masked = re.sub(
        SENSITIVE_PATTERNS['password'],
        r'\1: ***MASKED***',
        masked
    )
    masked = re.sub(
        SENSITIVE_PATTERNS['token'],
        r'\1: ***MASKED***',
        masked
    )
    
    return masked

def mask_dict_sensitive_data(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Mascara dados sensíveis em dicionários recursivamente.
    """
    if not isinstance(data, dict):
        return data
    
    masked = {}
    sensitive_keys = ['cpf', 'password', 'senha', 'token', 'api_key', 'secret', 
                     'telefone', 'phone', 'email', 'endereco', 'address']
    
    for key, value in data.items():
        key_lower = key.lower()
        
        # Se a chave é sensível, mascarar
        if any(sensitive in key_lower for sensitive in sensitive_keys):
            masked[key] = '***MASKED***'
        elif isinstance(value, dict):
            masked[key] = mask_dict_sensitive_data(value)
        elif isinstance(value, list):
            masked[key] = [
                mask_dict_sensitive_data(item) if isinstance(item, dict) 
                else mask_sensitive_data(str(item)) if isinstance(item, str)
                else item
                for item in value
            ]
        elif isinstance(value, str):
            masked[key] = mask_sensitive_data(value)
        else:
            masked[key] = value
    
    return masked

# ==============================================================================
# FORMATTER ESTRUTURADO (JSON)
# ==============================================================================

class StructuredJSONFormatter(logging.Formatter):
    """
    Formatter que converte logs para JSON estruturado.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o log record como JSON estruturado.
        """
        # Obter request_id do contexto
        request_id = request_id_context.get()
        
        # Construir objeto de log estruturado
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Adicionar request_id se disponível
        if request_id:
            log_data['request_id'] = request_id
        
        # Adicionar thread ID
        log_data['thread_id'] = threading.get_ident()
        
        # Adicionar exception info se houver
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Adicionar campos extras (se passados como dict no extra)
        if hasattr(record, 'audit_data'):
            # Mascarar dados sensíveis nos dados de auditoria
            log_data['audit'] = mask_dict_sensitive_data(record.audit_data)
        
        # Adicionar outros campos extras
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'levelno', 'lineno', 'module', 'msecs',
                          'message', 'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'audit_data']:
                if isinstance(value, (str, int, float, bool, type(None))):
                    log_data[key] = mask_sensitive_data(str(value)) if isinstance(value, str) else value
                elif isinstance(value, dict):
                    log_data[key] = mask_dict_sensitive_data(value)
        
        return json.dumps(log_data, ensure_ascii=False, default=str)

class HumanReadableFormatter(logging.Formatter):
    """
    Formatter legível para console (não JSON).
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Formata o log record de forma legível.
        """
        request_id = request_id_context.get()
        request_str = f"[{request_id[:8]}] " if request_id else ""
        
        # Mascarar mensagem se contiver dados sensíveis
        message = mask_sensitive_data(record.getMessage())
        
        base_format = f"%(asctime)s [%(levelname)s] {request_str}%(name)s: {message}"
        
        if record.exc_info:
            base_format += f"\n{self.formatException(record.exc_info)}"
        
        formatter = logging.Formatter(base_format)
        return formatter.format(record)

# ==============================================================================
# SETUP DE LOGGERS
# ==============================================================================

def generate_request_id() -> str:
    """
    Gera um novo request ID único.
    """
    return str(uuid.uuid4())

def set_request_id(request_id: str):
    """
    Define o request_id no contexto atual.
    """
    request_id_context.set(request_id)

def get_request_id() -> Optional[str]:
    """
    Obtém o request_id atual do contexto.
    """
    return request_id_context.get()

def setup_audit_logger(
    name: str,
    log_file: str,
    level: int = logging.INFO,
    use_json: bool = True,
    enable_rotation: bool = True,
    console_output: Optional[bool] = None
) -> logging.Logger:
    """
    Configura um logger com suporte a auditoria, rotação e logging estruturado.
    
    Args:
        name: Nome do logger
        log_file: Nome do arquivo de log
        level: Nível de log
        use_json: Se True, usa formato JSON estruturado
        enable_rotation: Se True, habilita rotação de logs
        console_output: Se True, exibe logs no console. Se None, usa LOG_CONSOLE env var (padrão: False)
    
    Returns:
        Logger configurado
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Desabilitar propagação para evitar logs no root logger
    logger.propagate = False
    
    # Evitar duplicação de handlers
    if logger.handlers:
        return logger
    
    # Criar diretório de logs se não existir
    os.makedirs(LOG_DIR, exist_ok=True)
    log_path = os.path.join(LOG_DIR, log_file)
    
    # Handler para arquivo com rotação
    if enable_rotation:
        # Rotação baseada em tamanho
        file_handler = RotatingFileHandler(
            log_path,
            maxBytes=LOG_MAX_BYTES,
            backupCount=LOG_BACKUP_COUNT,
            encoding='utf-8'
        )
    else:
        file_handler = logging.FileHandler(log_path, encoding='utf-8')
    
    file_handler.setLevel(logging.DEBUG)  # Arquivo sempre em DEBUG
    
    # Aplicar formatters
    if use_json:
        file_handler.setFormatter(StructuredJSONFormatter())
    else:
        formatter = HumanReadableFormatter()
        file_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    
    # Handler para console (apenas se habilitado)
    # Por padrão, console está desabilitado para interface limpa
    if console_output is None:
        console_output = os.getenv('LOG_CONSOLE', 'false').lower() in ('true', '1', 'yes')
    
    # NUNCA adicionar console handler por padrão - apenas se explicitamente habilitado
    if console_output:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        
        # Aplicar formatters para console
        if use_json:
            if os.getenv('LOG_FORMAT', 'human') == 'json':
                console_handler.setFormatter(StructuredJSONFormatter())
            else:
                console_handler.setFormatter(HumanReadableFormatter())
        else:
            console_handler.setFormatter(HumanReadableFormatter())
        
        logger.addHandler(console_handler)
    
    return logger

# ==============================================================================
# FUNÇÕES DE AUDITORIA ESPECÍFICAS
# ==============================================================================

def audit_sql_query(
    logger: logging.Logger,
    query: str,
    params: Optional[Dict[str, Any]] = None,
    duration_ms: Optional[float] = None,
    rows_returned: Optional[int] = None,
    success: bool = True,
    error: Optional[str] = None
):
    """
    Registra uma query SQL para auditoria.
    """
    audit_data = {
        'event_type': 'sql_query',
        'query': mask_sensitive_data(query),
        'params': mask_dict_sensitive_data(params) if params else None,
        'duration_ms': duration_ms,
        'rows_returned': rows_returned,
        'success': success,
        'error': error
    }
    
    log_record = logger.makeRecord(
        logger.name, logging.INFO, '', 0, '', (), None
    )
    log_record.audit_data = audit_data
    
    if success:
        logger.handle(log_record)
    else:
        log_record.levelno = logging.ERROR
        log_record.levelname = 'ERROR'
        logger.handle(log_record)

def audit_tool_call(
    logger: logging.Logger,
    tool_name: str,
    arguments: Dict[str, Any],
    result: Optional[Any] = None,
    duration_ms: Optional[float] = None,
    success: bool = True,
    error: Optional[str] = None
):
    """
    Registra uma chamada de ferramenta para auditoria.
    """
    audit_data = {
        'event_type': 'tool_call',
        'tool_name': tool_name,
        'arguments': mask_dict_sensitive_data(arguments),
        'result': mask_dict_sensitive_data(result) if isinstance(result, dict) else str(result)[:500] if result else None,
        'duration_ms': duration_ms,
        'success': success,
        'error': error
    }
    
    log_record = logger.makeRecord(
        logger.name, logging.INFO, '', 0, '', (), None
    )
    log_record.audit_data = audit_data
    
    if success:
        logger.handle(log_record)
    else:
        log_record.levelno = logging.ERROR
        log_record.levelname = 'ERROR'
        logger.handle(log_record)

def audit_llm_call(
    logger: logging.Logger,
    prompt: str,
    response: str,
    model: str,
    duration_ms: Optional[float] = None,
    tokens_used: Optional[int] = None,
    success: bool = True,
    error: Optional[str] = None
):
    """
    Registra uma chamada ao LLM para auditoria.
    """
    audit_data = {
        'event_type': 'llm_call',
        'model': model,
        'prompt_length': len(prompt),
        'response_length': len(response),
        'prompt_preview': mask_sensitive_data(prompt[:200]) + '...' if len(prompt) > 200 else mask_sensitive_data(prompt),
        'response_preview': mask_sensitive_data(response[:200]) + '...' if len(response) > 200 else mask_sensitive_data(response),
        'duration_ms': duration_ms,
        'tokens_used': tokens_used,
        'success': success,
        'error': error
    }
    
    log_record = logger.makeRecord(
        logger.name, logging.INFO, '', 0, '', (), None
    )
    log_record.audit_data = audit_data
    
    if success:
        logger.handle(log_record)
    else:
        log_record.levelno = logging.ERROR
        log_record.levelname = 'ERROR'
        logger.handle(log_record)

def audit_state_change(
    logger: logging.Logger,
    from_state: str,
    to_state: str,
    context: Optional[Dict[str, Any]] = None
):
    """
    Registra uma mudança de estado no grafo do agente.
    """
    audit_data = {
        'event_type': 'state_change',
        'from_state': from_state,
        'to_state': to_state,
        'context': mask_dict_sensitive_data(context) if context else None
    }
    
    log_record = logger.makeRecord(
        logger.name, logging.DEBUG, '', 0, '', (), None
    )
    log_record.audit_data = audit_data
    logger.handle(log_record)

# ==============================================================================
# CONTEXT MANAGER PARA REQUEST ID
# ==============================================================================

class RequestContext:
    """
    Context manager para gerenciar request_id durante uma requisição.
    """
    
    def __init__(self, request_id: Optional[str] = None):
        self.request_id = request_id or generate_request_id()
        self._token = None
    
    def __enter__(self):
        self._token = request_id_context.set(self.request_id)
        return self.request_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._token:
            request_id_context.reset(self._token)

