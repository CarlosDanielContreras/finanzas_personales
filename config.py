"""
Configuración de Flask
Aplicación de Finanzas Personales
"""

import os
from datetime import timedelta

class Config:
    """Configuración base para la aplicación"""
    
    # Configuración general
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'
    
    # Configuración de base de datos
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:@localhost/finanzas_personales'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # Cambiar a True para ver queries SQL en consola
    
    # Configuración de sesiones
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)
    SESSION_COOKIE_SECURE = False  # True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Configuración de archivos
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB máximo
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}
    
    # Configuración de paginación
    ITEMS_PER_PAGE = 20
    
    # Configuración de seguridad
    BCRYPT_LOG_ROUNDS = 12
    
    # Zona horaria
    TIMEZONE = 'America/Bogota'


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Ver queries en desarrollo


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
    # En producción, estas variables DEBEN venir de variables de entorno
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    SESSION_COOKIE_SECURE = True  # Solo HTTPS en producción
    
    # Validar que las variables críticas estén configuradas
    @classmethod
    def init_app(cls, app):
        if not cls.SECRET_KEY:
            raise ValueError("SECRET_KEY no configurada en producción")
        if not cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("DATABASE_URL no configurada en producción")


class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://root:@localhost/finanzas_personales_test'
    WTF_CSRF_ENABLED = False


# Diccionario de configuraciones
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}