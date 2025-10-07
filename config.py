"""
Configuración de Flask
Aplicación de Finanzas Personales
Versión Mejorada con Seguridad y Logging
"""

import os
from datetime import timedelta

# Directorio base del proyecto
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    """Configuración base para la aplicación"""
    
    # ==========================================
    # CONFIGURACIÓN GENERAL
    # ==========================================
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production-2024'
    APP_NAME = 'Finanzas Personales'
    
    # ==========================================
    # CONFIGURACIÓN DE BASE DE DATOS
    # ==========================================
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:@localhost/finanzas_personales'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ECHO = False  # True para ver queries SQL en consola
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_TIMEOUT = 30
    SQLALCHEMY_POOL_RECYCLE = 3600
    SQLALCHEMY_MAX_OVERFLOW = 20
    
    # ==========================================
    # CONFIGURACIÓN DE SESIONES
    # ==========================================
    PERMANENT_SESSION_LIFETIME = timedelta(days=int(os.environ.get('SESSION_LIFETIME_DAYS', 7)))
    SESSION_COOKIE_SECURE = False  # True en producción con HTTPS
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_NAME = 'finanzas_session'
    REMEMBER_COOKIE_DURATION = timedelta(days=30)
    REMEMBER_COOKIE_SECURE = False  # True en producción
    REMEMBER_COOKIE_HTTPONLY = True
    
    # ==========================================
    # CONFIGURACIÓN DE ARCHIVOS
    # ==========================================
    MAX_CONTENT_LENGTH = int(os.environ.get('MAX_FILE_SIZE', 16 * 1024 * 1024))  # 16MB
    UPLOAD_FOLDER = os.environ.get('UPLOAD_FOLDER') or os.path.join(basedir, 'uploads')
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'gif', 'xlsx', 'csv'}
    
    # Asegurar que la carpeta de uploads existe
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)
    
    # ==========================================
    # CONFIGURACIÓN DE PAGINACIÓN
    # ==========================================
    ITEMS_PER_PAGE = 20
    TRANSACCIONES_PER_PAGE = 50
    
    # ==========================================
    # CONFIGURACIÓN DE SEGURIDAD
    # ==========================================
    BCRYPT_LOG_ROUNDS = 12
    WTF_CSRF_ENABLED = True
    WTF_CSRF_TIME_LIMIT = None  # Sin límite de tiempo para CSRF
    WTF_CSRF_SSL_STRICT = False  # True en producción con HTTPS
    
    # Headers de seguridad
    SEND_FILE_MAX_AGE_DEFAULT = 0
    
    # ==========================================
    # CONFIGURACIÓN DE CORREO
    # ==========================================
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@finanzas.com')
    
    # ==========================================
    # CONFIGURACIÓN DE ZONA HORARIA
    # ==========================================
    TIMEZONE = os.environ.get('TIMEZONE', 'America/Bogota')
    
    # ==========================================
    # CONFIGURACIÓN DE LOGGING
    # ==========================================
    LOG_TO_STDOUT = os.environ.get('LOG_TO_STDOUT', 'False').lower() == 'true'
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.path.join(basedir, 'logs', 'app.log')
    
    # ==========================================
    # CONFIGURACIÓN DE CACHE
    # ==========================================
    CACHE_TYPE = os.environ.get('CACHE_TYPE', 'simple')
    CACHE_DEFAULT_TIMEOUT = 300
    
    # ==========================================
    # CONFIGURACIÓN DE RATE LIMITING
    # ==========================================
    RATELIMIT_ENABLED = True
    RATELIMIT_STORAGE_URL = os.environ.get('RATELIMIT_STORAGE_URL', 'memory://')
    RATELIMIT_STRATEGY = 'fixed-window'
    RATELIMIT_HEADERS_ENABLED = True
    
    # ==========================================
    # CONFIGURACIÓN DE BACKUP
    # ==========================================
    BACKUP_FOLDER = os.environ.get('BACKUP_FOLDER') or os.path.join(basedir, 'backups')
    AUTO_BACKUP_ENABLED = os.environ.get('AUTO_BACKUP_ENABLED', 'False').lower() == 'true'
    BACKUP_RETENTION_DAYS = int(os.environ.get('BACKUP_RETENTION_DAYS', 30))
    
    # Asegurar que la carpeta de backups existe
    if not os.path.exists(BACKUP_FOLDER):
        os.makedirs(BACKUP_FOLDER)
    
    # ==========================================
    # CONFIGURACIÓN DE REPORTES
    # ==========================================
    REPORTS_FOLDER = os.path.join(basedir, 'reports')
    if not os.path.exists(REPORTS_FOLDER):
        os.makedirs(REPORTS_FOLDER)
    
    # ==========================================
    # CONFIGURACIÓN DE API EXTERNA (FUTURO)
    # ==========================================
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    STRIPE_API_KEY = os.environ.get('STRIPE_API_KEY')
    SENDGRID_API_KEY = os.environ.get('SENDGRID_API_KEY')
    
    # ==========================================
    # CONFIGURACIÓN DE MONEDAS SOPORTADAS
    # ==========================================
    SUPPORTED_CURRENCIES = ['COP', 'USD', 'EUR', 'MXN', 'ARS']
    DEFAULT_CURRENCY = 'COP'
    
    # ==========================================
    # CONFIGURACIÓN DE IDIOMAS
    # ==========================================
    SUPPORTED_LANGUAGES = ['es', 'en']
    DEFAULT_LANGUAGE = 'es'
    BABEL_DEFAULT_LOCALE = 'es'
    BABEL_DEFAULT_TIMEZONE = TIMEZONE
    
    @staticmethod
    def init_app(app):
        """Inicialización de la configuración"""
        # Crear carpetas necesarias
        folders = [
            app.config['UPLOAD_FOLDER'],
            app.config['BACKUP_FOLDER'],
            app.config['REPORTS_FOLDER'],
            os.path.join(basedir, 'logs')
        ]
        
        for folder in folders:
            if not os.path.exists(folder):
                os.makedirs(folder)


class DevelopmentConfig(Config):
    """Configuración para desarrollo"""
    DEBUG = True
    TESTING = False
    SQLALCHEMY_ECHO = True  # Ver queries en desarrollo
    
    # Seguridad relajada en desarrollo
    WTF_CSRF_ENABLED = True  # Mantener CSRF incluso en dev
    SESSION_COOKIE_SECURE = False
    
    # Logging más verboso en desarrollo
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Configuración para producción"""
    DEBUG = False
    TESTING = False
    
    # En producción, estas variables DEBEN venir de variables de entorno
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    
    # Seguridad estricta en producción
    SESSION_COOKIE_SECURE = True  # Solo HTTPS
    REMEMBER_COOKIE_SECURE = True
    WTF_CSRF_SSL_STRICT = True
    PREFERRED_URL_SCHEME = 'https'
    
    # Configuración de logging para producción
    LOG_TO_STDOUT = True
    LOG_LEVEL = 'WARNING'
    
    # Habilitar backups automáticos en producción
    AUTO_BACKUP_ENABLED = True
    
    @classmethod
    def init_app(cls, app):
        """Validaciones adicionales para producción"""
        Config.init_app(app)
        
        # Validar que las variables críticas estén configuradas
        if not cls.SECRET_KEY or cls.SECRET_KEY == 'dev-secret-key-change-in-production-2024':
            raise ValueError("❌ SECRET_KEY no configurada correctamente en producción")
        
        if not cls.SQLALCHEMY_DATABASE_URI or 'localhost' in cls.SQLALCHEMY_DATABASE_URI:
            raise ValueError("❌ DATABASE_URL no configurada para producción")
        
        # Logging para syslog en producción
        import logging
        from logging.handlers import SysLogHandler
        
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)


class TestingConfig(Config):
    """Configuración para pruebas"""
    TESTING = True
    DEBUG = False
    
    # Base de datos de prueba separada
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'mysql+pymysql://root:@localhost/finanzas_personales_test'
    
    # Deshabilitar CSRF en tests
    WTF_CSRF_ENABLED = False
    
    # No requerir confirmación de email en tests
    MAIL_SUPPRESS_SEND = True
    
    # Cache deshabilitado en tests
    CACHE_TYPE = 'null'
    
    # Rate limiting deshabilitado en tests
    RATELIMIT_ENABLED = False
    
    @classmethod
    def init_app(cls, app):
        """Inicialización para tests"""
        Config.init_app(app)


class DockerConfig(ProductionConfig):
    """Configuración para Docker"""
    
    @classmethod
    def init_app(cls, app):
        """Inicialización para Docker"""
        ProductionConfig.init_app(app)
        
        # Logging a stdout para Docker
        import logging
        import sys
        
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setLevel(logging.INFO)
        app.logger.addHandler(stream_handler)


# Diccionario de configuraciones disponibles
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'docker': DockerConfig,
    'default': DevelopmentConfig
}


# Función helper para obtener la configuración actual
def get_config(config_name=None):
    """
    Obtiene la configuración según el nombre o variable de entorno
    
    Args:
        config_name: Nombre de la configuración ('development', 'production', etc.)
    
    Returns:
        Clase de configuración correspondiente
    """
    if config_name is None:
        config_name = os.getenv('FLASK_ENV', 'development')
    
    return config.get(config_name, DevelopmentConfig)