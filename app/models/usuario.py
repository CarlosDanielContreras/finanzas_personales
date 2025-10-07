"""
Modelo de Usuario
app/models/usuario.py
"""

from app import db, bcrypt
from flask_login import UserMixin
from datetime import datetime
from sqlalchemy import Enum

class Usuario(UserMixin, db.Model):
    """
    Modelo para la tabla usuarios
    Hereda de UserMixin para integración con Flask-Login
    """
    
    __tablename__ = 'usuarios'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    nombre_completo = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    rol = db.Column(Enum('usuario', 'admin', name='rol_enum'), default='usuario', index=True)
    
    # Campos de control
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    ultimo_acceso = db.Column(db.DateTime)
    activo = db.Column(db.Boolean, default=True)
    
    # Campos de perfil
    avatar_url = db.Column(db.String(255))
    moneda_preferida = db.Column(db.String(3), default='COP')
    
    # Relaciones
    configuracion = db.relationship('ConfiguracionUsuario', backref='usuario', lazy=True, uselist=False, cascade='all, delete-orphan')
    categorias = db.relationship('Categoria', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    cuentas = db.relationship('Cuenta', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    transacciones = db.relationship('Transaccion', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    presupuestos = db.relationship('Presupuesto', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    metas_ahorro = db.relationship('MetaAhorro', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    consejos = db.relationship('ConsejoFinanciero', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    sesiones = db.relationship('Sesion', backref='usuario', lazy='dynamic', cascade='all, delete-orphan')
    logs = db.relationship('LogActividad', backref='usuario', lazy='dynamic')
    
    def __init__(self, **kwargs):
        """Constructor del modelo Usuario"""
        super(Usuario, self).__init__(**kwargs)
    
    def set_password(self, password):
        """
        Hashea y guarda la contraseña del usuario
        
        Args:
            password (str): Contraseña en texto plano
        """
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
    
    def check_password(self, password):
        """
        Verifica si la contraseña proporcionada es correcta
        
        Args:
            password (str): Contraseña a verificar
            
        Returns:
            bool: True si la contraseña es correcta, False en caso contrario
        """
        return bcrypt.check_password_hash(self.password_hash, password)
    
    def is_admin(self):
        """
        Verifica si el usuario tiene rol de administrador
        
        Returns:
            bool: True si es admin, False en caso contrario
        """
        return self.rol == 'admin'
    
    def actualizar_ultimo_acceso(self):
        """Actualiza la fecha y hora del último acceso del usuario"""
        self.ultimo_acceso = datetime.utcnow()
        db.session.commit()
    
    def get_balance_total(self):
        """
        Calcula el balance total del usuario sumando todas sus cuentas
        
        Returns:
            float: Balance total en la moneda preferida del usuario
        """
        total = 0.0
        for cuenta in self.cuentas.filter_by(activo=True):
            total += float(cuenta.saldo_actual)
        return total
    
    def get_ingresos_mes_actual(self):
        """
        Obtiene el total de ingresos del mes actual
        
        Returns:
            float: Total de ingresos del mes
        """
        from sqlalchemy import func, extract
        
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        
        resultado = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.usuario_id == self.id,
            Transaccion.tipo == 'ingreso',
            extract('month', Transaccion.fecha_transaccion) == mes_actual,
            extract('year', Transaccion.fecha_transaccion) == anio_actual
        ).scalar()
        
        return float(resultado) if resultado else 0.0
    
    def get_egresos_mes_actual(self):
        """
        Obtiene el total de egresos del mes actual
        
        Returns:
            float: Total de egresos del mes
        """
        from sqlalchemy import func, extract
        
        mes_actual = datetime.now().month
        anio_actual = datetime.now().year
        
        resultado = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.usuario_id == self.id,
            Transaccion.tipo == 'egreso',
            extract('month', Transaccion.fecha_transaccion) == mes_actual,
            extract('year', Transaccion.fecha_transaccion) == anio_actual
        ).scalar()
        
        return float(resultado) if resultado else 0.0
    
    def get_balance_mes_actual(self):
        """
        Calcula el balance del mes actual (ingresos - egresos)
        
        Returns:
            float: Balance del mes actual
        """
        return self.get_ingresos_mes_actual() - self.get_egresos_mes_actual()
    
    def get_estadisticas_resumen(self):
        """
        Obtiene un resumen de estadísticas del usuario
        
        Returns:
            dict: Diccionario con estadísticas principales
        """
        return {
            'balance_total': self.get_balance_total(),
            'ingresos_mes': self.get_ingresos_mes_actual(),
            'egresos_mes': self.get_egresos_mes_actual(),
            'balance_mes': self.get_balance_mes_actual(),
            'total_cuentas': self.cuentas.filter_by(activo=True).count(),
            'total_transacciones': self.transacciones.count(),
            'metas_activas': self.metas_ahorro.filter_by(completada=False).count()
        }
    
    def to_dict(self):
        """
        Convierte el objeto Usuario a diccionario (útil para JSON)
        
        Returns:
            dict: Representación del usuario en diccionario
        """
        return {
            'id': self.id,
            'nombre_completo': self.nombre_completo,
            'email': self.email,
            'rol': self.rol,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'ultimo_acceso': self.ultimo_acceso.isoformat() if self.ultimo_acceso else None,
            'activo': self.activo,
            'moneda_preferida': self.moneda_preferida
        }
    
    def __repr__(self):
        """Representación en string del objeto"""
        return f'<Usuario {self.email}>'


class ConfiguracionUsuario(db.Model):
    """
    Modelo para configuraciones personalizadas del usuario
    """
    
    __tablename__ = 'configuracion_usuario'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False)
    
    # Configuraciones
    notificaciones_email = db.Column(db.Boolean, default=True)
    tema = db.Column(Enum('claro', 'oscuro', name='tema_enum'), default='claro')
    idioma = db.Column(db.String(5), default='es')
    
    def __repr__(self):
        return f'<ConfiguracionUsuario usuario_id={self.usuario_id}>'