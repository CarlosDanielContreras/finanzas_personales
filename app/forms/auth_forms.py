"""
Formularios de Autenticación
app/forms/auth_forms.py
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app.models.usuario import Usuario

class LoginForm(FlaskForm):
    """Formulario de inicio de sesión"""
    
    email = StringField('Correo Electrónico', 
                       validators=[
                           DataRequired(message='El correo es obligatorio'),
                           Email(message='Ingresa un correo válido')
                       ],
                       render_kw={'placeholder': 'tu@email.com', 'class': 'form-control'})
    
    password = PasswordField('Contraseña',
                            validators=[DataRequired(message='La contraseña es obligatoria')],
                            render_kw={'placeholder': '••••••••', 'class': 'form-control'})
    
    recordar = BooleanField('Recordarme', render_kw={'class': 'form-check-input'})
    
    submit = SubmitField('Iniciar Sesión', render_kw={'class': 'btn btn-primary w-100'})


class RegistroForm(FlaskForm):
    """Formulario de registro de nuevo usuario"""
    
    nombre_completo = StringField('Nombre Completo',
                                  validators=[
                                      DataRequired(message='El nombre es obligatorio'),
                                      Length(min=3, max=100, message='El nombre debe tener entre 3 y 100 caracteres')
                                  ],
                                  render_kw={'placeholder': 'Juan Pérez', 'class': 'form-control'})
    
    email = StringField('Correo Electrónico',
                       validators=[
                           DataRequired(message='El correo es obligatorio'),
                           Email(message='Ingresa un correo válido')
                       ],
                       render_kw={'placeholder': 'tu@email.com', 'class': 'form-control'})
    
    password = PasswordField('Contraseña',
                            validators=[
                                DataRequired(message='La contraseña es obligatoria'),
                                Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
                            ],
                            render_kw={'placeholder': '••••••••', 'class': 'form-control'})
    
    confirmar_password = PasswordField('Confirmar Contraseña',
                                      validators=[
                                          DataRequired(message='Debes confirmar la contraseña'),
                                          EqualTo('password', message='Las contraseñas no coinciden')
                                      ],
                                      render_kw={'placeholder': '••••••••', 'class': 'form-control'})
    
    aceptar_terminos = BooleanField('Acepto los términos y condiciones',
                                   validators=[DataRequired(message='Debes aceptar los términos y condiciones')],
                                   render_kw={'class': 'form-check-input'})
    
    submit = SubmitField('Registrarme', render_kw={'class': 'btn btn-primary w-100'})
    
    def validate_email(self, email):
        """
        Valida que el correo no esté ya registrado
        
        Args:
            email: Campo de email del formulario
            
        Raises:
            ValidationError: Si el email ya existe
        """
        usuario = Usuario.query.filter_by(email=email.data.lower()).first()
        if usuario:
            raise ValidationError('Este correo ya está registrado. Por favor inicia sesión.')
    
    def validate_password(self, password):
        """
        Valida que la contraseña cumpla con requisitos de seguridad
        
        Args:
            password: Campo de contraseña del formulario
            
        Raises:
            ValidationError: Si la contraseña no cumple los requisitos
        """
        password_str = password.data
        
        # Verificar que tenga al menos una letra mayúscula
        if not any(c.isupper() for c in password_str):
            raise ValidationError('La contraseña debe contener al menos una letra mayúscula')
        
        # Verificar que tenga al menos una letra minúscula
        if not any(c.islower() for c in password_str):
            raise ValidationError('La contraseña debe contener al menos una letra minúscula')
        
        # Verificar que tenga al menos un número
        if not any(c.isdigit() for c in password_str):
            raise ValidationError('La contraseña debe contener al menos un número')


class CambiarPasswordForm(FlaskForm):
    """Formulario para cambiar contraseña"""
    
    password_actual = PasswordField('Contraseña Actual',
                                   validators=[DataRequired(message='Ingresa tu contraseña actual')],
                                   render_kw={'placeholder': '••••••••', 'class': 'form-control'})
    
    password_nueva = PasswordField('Nueva Contraseña',
                                  validators=[
                                      DataRequired(message='Ingresa la nueva contraseña'),
                                      Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
                                  ],
                                  render_kw={'placeholder': '••••••••', 'class': 'form-control'})
    
    confirmar_password_nueva = PasswordField('Confirmar Nueva Contraseña',
                                            validators=[
                                                DataRequired(message='Confirma la nueva contraseña'),
                                                EqualTo('password_nueva', message='Las contraseñas no coinciden')
                                            ],
                                            render_kw={'placeholder': '••••••••', 'class': 'form-control'})
    
    submit = SubmitField('Cambiar Contraseña', render_kw={'class': 'btn btn-primary'})


class RecuperarPasswordForm(FlaskForm):
    """Formulario para recuperar contraseña"""
    
    email = StringField('Correo Electrónico',
                       validators=[
                           DataRequired(message='El correo es obligatorio'),
                           Email(message='Ingresa un correo válido')
                       ],
                       render_kw={'placeholder': 'tu@email.com', 'class': 'form-control'})
    
    submit = SubmitField('Enviar Instrucciones', render_kw={'class': 'btn btn-primary w-100'})
    
    def validate_email(self, email):
        """
        Valida que el correo exista en el sistema
        
        Args:
            email: Campo de email del formulario
            
        Raises:
            ValidationError: Si el email no existe
        """
        usuario = Usuario.query.filter_by(email=email.data.lower()).first()
        if not usuario:
            raise ValidationError('No existe una cuenta con este correo electrónico.')