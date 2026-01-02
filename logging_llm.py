"""
Sistema de Logging - Compatibilidade e Wrapper
Mantém compatibilidade com código existente enquanto usa o novo sistema de auditoria.
"""

import logging
import os
from audit_logging import setup_audit_logger, LOG_LEVEL

# Define o diretório para os logs (compatibilidade)
LOG_DIR = os.getenv('LOG_DIR', 'logs')
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

# Converter string de nível para constante
LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}

def setup_logger(name, log_file, level=logging.INFO):
    """
    Função para configurar um logger nomeado com handlers de arquivo e console.
    
    Esta função mantém compatibilidade com código existente, mas agora usa
    o sistema de logging estruturado com auditoria.
    
    Args:
        name: Nome do logger
        log_file: Nome do arquivo de log
        level: Nível de log (pode ser string ou constante)
    
    Returns:
        Logger configurado
    """
    # Converter nível se for string
    if isinstance(level, str):
        level = LEVEL_MAP.get(level.upper(), logging.INFO)
    
    # Usar o novo sistema de auditoria
    # Por padrão, usa JSON para arquivo e formato legível para console
    use_json = os.getenv('LOG_FORMAT', 'human') == 'json'
    
    # Por padrão, console está desabilitado para interface limpa
    # Use LOG_CONSOLE=true no .env se quiser ver logs no terminal
    console_output = os.getenv('LOG_CONSOLE', 'false').lower() == 'true'
    
    return setup_audit_logger(
        name=name,
        log_file=log_file,
        level=level,
        use_json=use_json,
        enable_rotation=True,
        console_output=console_output
    )
