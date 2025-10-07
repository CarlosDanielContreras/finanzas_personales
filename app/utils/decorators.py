"""
Decoradores Personalizados
app/utils/decorators.py
"""

from functools import wraps
from flask import redirect, url_for, flash, abort
from flask_login import current_user

def login_required(f):
    """
    Decorador para requerir que el usuario esté autenticado
    (Ya incluido en Flask-Login, pero aquí está como referencia)
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


def admin_required(f):
    """
    Decorador para requerir que el usuario sea administrador
    
    Uso:
        @admin_required
        def vista_admin():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.is_admin():
            flash('No tienes permisos para acceder a esta página.', 'danger')
            abort(403)
        
        return f(*args, **kwargs)
    return decorated_function


def usuario_activo_required(f):
    """
    Decorador para verificar que el usuario esté activo
    
    Uso:
        @usuario_activo_required
        def vista_protegida():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Debes iniciar sesión para acceder a esta página.', 'warning')
            return redirect(url_for('auth.login'))
        
        if not current_user.activo:
            flash('Tu cuenta ha sido desactivada. Contacta al administrador.', 'danger')
            return redirect(url_for('auth.login'))
        
        return f(*args, **kwargs)
    return decorated_function


def ajax_required(f):
    """
    Decorador para rutas que solo aceptan peticiones AJAX
    
    Uso:
        @ajax_required
        def api_endpoint():
            ...
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        if not request.is_json and not request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            abort(400, description='Solo se permiten peticiones AJAX')
        return f(*args, **kwargs)
    return decorated_function