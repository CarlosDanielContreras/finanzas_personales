"""
Rutas de Autenticación
app/routes/auth.py
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, current_user
from app import db
from app.models.usuario import Usuario, ConfiguracionUsuario
from app.models.otros import LogActividad
from app.forms.auth_forms import LoginForm, RegistroForm, CambiarPasswordForm, RecuperarPasswordForm
from datetime import datetime

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Ruta para iniciar sesión"""
    
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        # Buscar usuario por email
        usuario = Usuario.query.filter_by(email=form.email.data.lower()).first()
        
        # Verificar credenciales
        if usuario and usuario.check_password(form.password.data):
            
            # Verificar si el usuario está activo
            if not usuario.activo:
                flash('Tu cuenta ha sido desactivada. Contacta al administrador.', 'danger')
                return redirect(url_for('auth.login'))
            
            # Iniciar sesión
            login_user(usuario, remember=form.recordar.data)
            
            # Actualizar último acceso
            usuario.actualizar_ultimo_acceso()
            
            # Registrar en el log
            LogActividad.registrar(
                usuario_id=usuario.id,
                accion='login',
                detalle='Inicio de sesión exitoso',
                ip_address=request.remote_addr
            )
            
            flash(f'¡Bienvenido de nuevo, {usuario.nombre_completo}!', 'success')
            
            # Redirigir a la página solicitada o al dashboard
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.dashboard'))
        else:
            flash('Correo o contraseña incorrectos. Por favor intenta de nuevo.', 'danger')
            
            # Registrar intento fallido
            if usuario:
                LogActividad.registrar(
                    usuario_id=usuario.id,
                    accion='login_fallido',
                    detalle='Intento de inicio de sesión con contraseña incorrecta',
                    ip_address=request.remote_addr
                )
    
    return render_template('auth/login.html', form=form)


@bp.route('/registro', methods=['GET', 'POST'])
def registro():
    """Ruta para registrar nuevo usuario"""
    
    # Si el usuario ya está autenticado, redirigir al dashboard
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RegistroForm()
    
    if form.validate_on_submit():
        try:
            # Crear nuevo usuario
            nuevo_usuario = Usuario(
                nombre_completo=form.nombre_completo.data.strip(),
                email=form.email.data.lower().strip(),
                rol='usuario',
                moneda_preferida='COP'
            )
            nuevo_usuario.set_password(form.password.data)
            
            db.session.add(nuevo_usuario)
            db.session.commit()
            
            # Crear configuración por defecto
            configuracion = ConfiguracionUsuario(
                usuario_id=nuevo_usuario.id,
                notificaciones_email=True,
                tema='claro',
                idioma='es'
            )
            db.session.add(configuracion)
            db.session.commit()
            
            # Registrar en el log
            LogActividad.registrar(
                usuario_id=nuevo_usuario.id,
                accion='registro',
                detalle='Nuevo usuario registrado',
                ip_address=request.remote_addr
            )
            
            flash('¡Registro exitoso! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('auth.login'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al registrar usuario: {str(e)}', 'danger')
    
    return render_template('auth/registro.html', form=form)


@bp.route('/logout')
def logout():
    """Ruta para cerrar sesión"""
    
    if current_user.is_authenticated:
        # Registrar en el log
        LogActividad.registrar(
            usuario_id=current_user.id,
            accion='logout',
            detalle='Cierre de sesión',
            ip_address=request.remote_addr
        )
        
        # Cerrar sesión
        logout_user()
        flash('Has cerrado sesión correctamente.', 'info')
    
    return redirect(url_for('auth.login'))


@bp.route('/cambiar-password', methods=['GET', 'POST'])
def cambiar_password():
    """Ruta para cambiar contraseña (requiere estar autenticado)"""
    
    if not current_user.is_authenticated:
        flash('Debes iniciar sesión para acceder a esta página.', 'warning')
        return redirect(url_for('auth.login'))
    
    form = CambiarPasswordForm()
    
    if form.validate_on_submit():
        # Verificar contraseña actual
        if not current_user.check_password(form.password_actual.data):
            flash('La contraseña actual es incorrecta.', 'danger')
            return render_template('auth/cambiar_password.html', form=form)
        
        # Cambiar contraseña
        current_user.set_password(form.password_nueva.data)
        db.session.commit()
        
        # Registrar en el log
        LogActividad.registrar(
            usuario_id=current_user.id,
            accion='cambio_password',
            detalle='Contraseña cambiada exitosamente',
            ip_address=request.remote_addr
        )
        
        flash('Contraseña cambiada exitosamente.', 'success')
        return redirect(url_for('main.dashboard'))
    
    return render_template('auth/cambiar_password.html', form=form)


@bp.route('/recuperar-password', methods=['GET', 'POST'])
def recuperar_password():
    """Ruta para recuperar contraseña (envío de email)"""
    
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    
    form = RecuperarPasswordForm()
    
    if form.validate_on_submit():
        usuario = Usuario.query.filter_by(email=form.email.data.lower()).first()
        
        if usuario:
            # TODO: Implementar envío de email con token de recuperación
            # Por ahora solo mostramos un mensaje
            
            # Registrar en el log
            LogActividad.registrar(
                usuario_id=usuario.id,
                accion='solicitud_recuperacion_password',
                detalle='Solicitud de recuperación de contraseña',
                ip_address=request.remote_addr
            )
            
            flash('Se han enviado las instrucciones a tu correo electrónico.', 'info')
            return redirect(url_for('auth.login'))
    
    return render_template('auth/recuperar_password.html', form=form)


@bp.route('/verificar-email/<token>')
def verificar_email(token):
    """Ruta para verificar email (implementación futura)"""
    # TODO: Implementar verificación de email con token
    flash('Función de verificación de email en desarrollo.', 'info')
    return redirect(url_for('auth.login'))