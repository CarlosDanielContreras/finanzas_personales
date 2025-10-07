"""
Inicialización de la aplicación Flask
app/__init__.py
"""

from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from config import config

# Inicializar extensiones
db = SQLAlchemy()
bcrypt = Bcrypt()
login_manager = LoginManager()

def create_app(config_name='development'):
    """
    Factory pattern para crear la aplicación Flask
    
    Args:
        config_name: Nombre de la configuración a usar ('development', 'production', 'testing')
    
    Returns:
        app: Instancia de la aplicación Flask configurada
    """
    
    # Crear instancia de Flask
    app = Flask(__name__)
    
    # Cargar configuración
    app.config.from_object(config[config_name])
    
    # Inicializar extensiones con la app
    db.init_app(app)
    bcrypt.init_app(app)
    login_manager.init_app(app)
    
    # Configuración de Flask-Login
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
    login_manager.login_message_category = 'info'
    
    # Crear carpeta de uploads si no existe
    import os
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    
    # Registrar Blueprints (rutas)
    from app.routes import auth, main, transacciones, reportes, admin
    
    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(transacciones.bp)
    app.register_blueprint(reportes.bp)
    app.register_blueprint(admin.bp)
    
    # Registrar filtros personalizados de Jinja2
    from app.utils import filters
    filters.register_filters(app)
    
    # Manejadores de errores
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden(e):
        return render_template('errors/403.html'), 403
    
    # Contexto global para templates
    @app.context_processor
    def inject_global_vars():
        from datetime import datetime
        return {
            'current_year': datetime.now().year,
            'app_name': 'Finanzas Personales'
        }
    
    return app


# Cargar modelo de usuario para Flask-Login
@login_manager.user_loader
def load_user(user_id):
    from app.models.usuario import Usuario
    return Usuario.query.get(int(user_id))