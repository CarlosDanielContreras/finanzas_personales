"""
Modelos Auxiliares
app/models/otros.py
"""

from app import db
from datetime import datetime
from sqlalchemy import Enum

class ConsejoFinanciero(db.Model):
    """
    Modelo para consejos financieros automáticos o generados por admin
    """
    
    __tablename__ = 'consejos_financieros'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=True, index=True)
    tipo_consejo = db.Column(Enum('ahorro', 'gasto', 'inversion', 'deuda', 'general', 
                                  name='tipo_consejo_enum'), nullable=False)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_generacion = db.Column(db.DateTime, default=datetime.utcnow)
    visto = db.Column(db.Boolean, default=False, index=True)
    relevancia = db.Column(db.Integer, default=5)  # 1-10
    
    def marcar_como_visto(self):
        """Marca el consejo como visto"""
        self.visto = True
        db.session.commit()
    
    def es_general(self):
        """Verifica si el consejo es general (para todos los usuarios)"""
        return self.usuario_id is None
    
    def get_icono(self):
        """
        Obtiene el icono según el tipo de consejo
        
        Returns:
            str: Clase de icono Font Awesome
        """
        iconos = {
            'ahorro': 'fa-piggy-bank',
            'gasto': 'fa-shopping-cart',
            'inversion': 'fa-chart-line',
            'deuda': 'fa-credit-card',
            'general': 'fa-lightbulb'
        }
        return iconos.get(self.tipo_consejo, 'fa-info-circle')
    
    def get_clase_css(self):
        """
        Obtiene la clase CSS según el tipo
        
        Returns:
            str: Clase CSS de Bootstrap
        """
        clases = {
            'ahorro': 'success',
            'gasto': 'warning',
            'inversion': 'info',
            'deuda': 'danger',
            'general': 'primary'
        }
        return clases.get(self.tipo_consejo, 'secondary')
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'tipo_consejo': self.tipo_consejo,
            'titulo': self.titulo,
            'contenido': self.contenido,
            'fecha_generacion': self.fecha_generacion.isoformat(),
            'visto': self.visto,
            'relevancia': self.relevancia,
            'icono': self.get_icono()
        }
    
    @staticmethod
    def get_consejos_no_vistos(usuario_id):
        """
        Obtiene los consejos no vistos de un usuario
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            list: Lista de consejos no vistos
        """
        return ConsejoFinanciero.query.filter(
            db.or_(
                ConsejoFinanciero.usuario_id == usuario_id,
                ConsejoFinanciero.usuario_id == None
            ),
            ConsejoFinanciero.visto == False
        ).order_by(ConsejoFinanciero.relevancia.desc()).all()
    
    def __repr__(self):
        return f'<ConsejoFinanciero {self.titulo}>'


class Sesion(db.Model):
    """
    Modelo para control de sesiones activas (seguridad)
    """
    
    __tablename__ = 'sesiones'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    token_sesion = db.Column(db.String(255), unique=True, nullable=False, index=True)
    ip_address = db.Column(db.String(45))
    user_agent = db.Column(db.Text)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_expiracion = db.Column(db.DateTime, nullable=False)
    activa = db.Column(db.Boolean, default=True, index=True)
    
    def esta_expirada(self):
        """
        Verifica si la sesión ha expirado
        
        Returns:
            bool: True si está expirada
        """
        return datetime.utcnow() > self.fecha_expiracion
    
    def cerrar_sesion(self):
        """Cierra la sesión"""
        self.activa = False
        db.session.commit()
    
    def renovar_sesion(self, dias=7):
        """
        Renueva la sesión extendiendo su fecha de expiración
        
        Args:
            dias (int): Días a extender
        """
        from datetime import timedelta
        self.fecha_expiracion = datetime.utcnow() + timedelta(days=dias)
        db.session.commit()
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'ip_address': self.ip_address,
            'fecha_creacion': self.fecha_creacion.isoformat(),
            'fecha_expiracion': self.fecha_expiracion.isoformat(),
            'activa': self.activa,
            'expirada': self.esta_expirada()
        }
    
    @staticmethod
    def limpiar_sesiones_expiradas():
        """Elimina todas las sesiones expiradas"""
        sesiones_expiradas = Sesion.query.filter(
            Sesion.fecha_expiracion < datetime.utcnow()
        ).all()
        
        for sesion in sesiones_expiradas:
            db.session.delete(sesion)
        
        db.session.commit()
        return len(sesiones_expiradas)
    
    def __repr__(self):
        return f'<Sesion usuario_id={self.usuario_id} activa={self.activa}>'


class LogActividad(db.Model):
    """
    Modelo para registro de actividades (auditoría)
    """
    
    __tablename__ = 'logs_actividad'
    
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='SET NULL'), nullable=True, index=True)
    accion = db.Column(db.String(100), nullable=False, index=True)
    detalle = db.Column(db.Text)
    ip_address = db.Column(db.String(45))
    fecha_hora = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'accion': self.accion,
            'detalle': self.detalle,
            'ip_address': self.ip_address,
            'fecha_hora': self.fecha_hora.isoformat()
        }
    
    @staticmethod
    def registrar(usuario_id, accion, detalle=None, ip_address=None):
        """
        Registra una actividad en el log
        
        Args:
            usuario_id (int): ID del usuario
            accion (str): Acción realizada
            detalle (str): Detalles adicionales
            ip_address (str): Dirección IP
            
        Returns:
            LogActividad: El log creado
        """
        log = LogActividad(
            usuario_id=usuario_id,
            accion=accion,
            detalle=detalle,
            ip_address=ip_address
        )
        db.session.add(log)
        db.session.commit()
        return log
    
    @staticmethod
    def get_actividad_reciente(usuario_id=None, limite=50):
        """
        Obtiene la actividad reciente
        
        Args:
            usuario_id (int): ID del usuario (opcional, None para todos)
            limite (int): Número máximo de registros
            
        Returns:
            list: Lista de logs
        """
        query = LogActividad.query
        
        if usuario_id:
            query = query.filter(LogActividad.usuario_id == usuario_id)
        
        return query.order_by(LogActividad.fecha_hora.desc()).limit(limite).all()
    
    def __repr__(self):
        return f'<LogActividad {self.accion} - {self.fecha_hora}>'


class EstadisticaApp(db.Model):
    """
    Modelo para estadísticas de la aplicación (dashboard admin)
    """
    
    __tablename__ = 'estadisticas_app'
    
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.Date, nullable=False, unique=True, index=True)
    usuarios_activos = db.Column(db.Integer, default=0)
    nuevos_usuarios = db.Column(db.Integer, default=0)
    transacciones_totales = db.Column(db.Integer, default=0)
    volumen_transacciones = db.Column(db.Numeric(15, 2), default=0.00)
    errores_sistema = db.Column(db.Integer, default=0)
    tiempo_promedio_sesion = db.Column(db.Integer, default=0)  # en segundos
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'fecha': self.fecha.isoformat(),
            'usuarios_activos': self.usuarios_activos,
            'nuevos_usuarios': self.nuevos_usuarios,
            'transacciones_totales': self.transacciones_totales,
            'volumen_transacciones': float(self.volumen_transacciones),
            'errores_sistema': self.errores_sistema,
            'tiempo_promedio_sesion': self.tiempo_promedio_sesion
        }
    
    @staticmethod
    def actualizar_estadistica_hoy():
        """
        Actualiza o crea la estadística del día actual
        """
        from app.models.usuario import Usuario
        from app.models.transaccion import Transaccion
        from sqlalchemy import func
        
        hoy = datetime.now().date()
        
        # Buscar o crear estadística del día
        estadistica = EstadisticaApp.query.filter_by(fecha=hoy).first()
        if not estadistica:
            estadistica = EstadisticaApp(fecha=hoy)
            db.session.add(estadistica)
        
        # Calcular usuarios activos (con sesión hoy)
        estadistica.usuarios_activos = Usuario.query.filter(
            Usuario.ultimo_acceso >= datetime.combine(hoy, datetime.min.time())
        ).count()
        
        # Calcular nuevos usuarios
        estadistica.nuevos_usuarios = Usuario.query.filter(
            func.date(Usuario.fecha_registro) == hoy
        ).count()
        
        # Calcular transacciones del día
        transacciones_hoy = Transaccion.query.filter(
            Transaccion.fecha_transaccion == hoy
        ).all()
        
        estadistica.transacciones_totales = len(transacciones_hoy)
        estadistica.volumen_transacciones = sum(float(t.monto) for t in transacciones_hoy)
        
        db.session.commit()
        return estadistica
    
    def __repr__(self):
        return f'<EstadisticaApp {self.fecha}>'