"""
Configuración de logging
"""
import logging
from logging.handlers import RotatingFileHandler
import os

def setup_logging(app):
    """Configura el sistema de logging"""
    if not app.debug:
        # Crear carpeta de logs si no existe
        if not os.path.exists('logs'):
            os.mkdir('logs')
        
        # Handler para archivo
        file_handler = RotatingFileHandler(
            'logs/finanzas.log',
            maxBytes=10240000,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
            '[in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('Aplicación de Finanzas Personales iniciada')