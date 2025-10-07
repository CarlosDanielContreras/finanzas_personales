"""
Modelo de Meta de Ahorro
app/models/meta_ahorro.py
"""

from app import db
from datetime import datetime

class MetaAhorro(db.Model):
    """
    Modelo para metas de ahorro del usuario
    """
    
    __tablename__ = 'metas_ahorro'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False)
    descripcion = db.Column(db.Text)
    
    # Montos
    monto_objetivo = db.Column(db.Numeric(15, 2), nullable=False)
    monto_actual = db.Column(db.Numeric(15, 2), default=0.00)
    
    # Fechas
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_objetivo = db.Column(db.Date, nullable=False)
    completada = db.Column(db.Boolean, default=False, index=True)
    fecha_completada = db.Column(db.Date, nullable=True)
    
    # Relaciones
    aportes = db.relationship('AporteMeta', backref='meta', lazy='dynamic', cascade='all, delete-orphan')
    
    def __init__(self, **kwargs):
        """Constructor del modelo MetaAhorro"""
        super(MetaAhorro, self).__init__(**kwargs)
        if 'fecha_inicio' not in kwargs:
            self.fecha_inicio = datetime.now().date()
    
    def agregar_aporte(self, monto, notas=None):
        """
        Agrega un aporte a la meta
        
        Args:
            monto (float): Monto del aporte
            notas (str): Notas opcionales
            
        Returns:
            AporteMeta: El aporte creado
        """
        aporte = AporteMeta(
            meta_id=self.id,
            monto=monto,
            fecha_aporte=datetime.now().date(),
            notas=notas
        )
        
        self.monto_actual = float(self.monto_actual) + monto
        
        # Verificar si se completó la meta
        if self.monto_actual >= float(self.monto_objetivo) and not self.completada:
            self.completar_meta()
        
        db.session.add(aporte)
        db.session.commit()
        
        return aporte
    
    def completar_meta(self):
        """Marca la meta como completada"""
        self.completada = True
        self.fecha_completada = datetime.now().date()
        db.session.commit()
    
    def reabrir_meta(self):
        """Reabre una meta completada"""
        self.completada = False
        self.fecha_completada = None
        db.session.commit()
    
    def get_porcentaje_completado(self):
        """
        Calcula el porcentaje completado de la meta
        
        Returns:
            float: Porcentaje completado (0-100)
        """
        if float(self.monto_objetivo) == 0:
            return 0.0
        
        porcentaje = (float(self.monto_actual) / float(self.monto_objetivo)) * 100
        return min(porcentaje, 100.0)
    
    def get_monto_faltante(self):
        """
        Calcula el monto faltante para completar la meta
        
        Returns:
            float: Monto faltante
        """
        faltante = float(self.monto_objetivo) - float(self.monto_actual)
        return max(faltante, 0.0)
    
    def get_dias_restantes(self):
        """
        Calcula los días restantes para alcanzar la meta
        
        Returns:
            int: Número de días restantes
        """
        hoy = datetime.now().date()
        if hoy > self.fecha_objetivo:
            return 0
        return (self.fecha_objetivo - hoy).days
    
    def get_dias_transcurridos(self):
        """
        Calcula los días transcurridos desde el inicio
        
        Returns:
            int: Número de días transcurridos
        """
        hoy = datetime.now().date()
        return (hoy - self.fecha_inicio).days
    
    def get_ahorro_sugerido_mensual(self):
        """
        Calcula el ahorro mensual sugerido para alcanzar la meta
        
        Returns:
            float: Monto mensual sugerido
        """
        dias_restantes = self.get_dias_restantes()
        if dias_restantes <= 0:
            return 0.0
        
        monto_faltante = self.get_monto_faltante()
        meses_restantes = dias_restantes / 30
        
        if meses_restantes <= 0:
            return monto_faltante
        
        return monto_faltante / meses_restantes
    
    def get_ahorro_sugerido_semanal(self):
        """
        Calcula el ahorro semanal sugerido
        
        Returns:
            float: Monto semanal sugerido
        """
        dias_restantes = self.get_dias_restantes()
        if dias_restantes <= 0:
            return 0.0
        
        monto_faltante = self.get_monto_faltante()
        semanas_restantes = dias_restantes / 7
        
        if semanas_restantes <= 0:
            return monto_faltante
        
        return monto_faltante / semanas_restantes
    
    def esta_en_tiempo(self):
        """
        Verifica si la meta está en tiempo de cumplirse
        
        Returns:
            bool: True si está en tiempo
        """
        if self.completada:
            return True
        
        dias_restantes = self.get_dias_restantes()
        dias_totales = (self.fecha_objetivo - self.fecha_inicio).days
        
        if dias_totales == 0:
            return False
        
        progreso_tiempo = ((dias_totales - dias_restantes) / dias_totales) * 100
        progreso_ahorro = self.get_porcentaje_completado()
        
        return progreso_ahorro >= progreso_tiempo
    
    def get_estado(self):
        """
        Obtiene el estado de la meta
        
        Returns:
            str: 'completada', 'en_tiempo', 'atrasada', 'vencida'
        """
        if self.completada:
            return 'completada'
        
        if self.get_dias_restantes() <= 0:
            return 'vencida'
        
        if self.esta_en_tiempo():
            return 'en_tiempo'
        
        return 'atrasada'
    
    def get_clase_css_estado(self):
        """
        Obtiene la clase CSS según el estado
        
        Returns:
            str: Clase CSS de Bootstrap
        """
        estado = self.get_estado()
        clases = {
            'completada': 'success',
            'en_tiempo': 'info',
            'atrasada': 'warning',
            'vencida': 'danger'
        }
        return clases.get(estado, 'secondary')
    
    def get_total_aportes(self):
        """
        Obtiene el número total de aportes
        
        Returns:
            int: Número de aportes
        """
        return self.aportes.count()
    
    def get_promedio_aporte(self):
        """
        Calcula el promedio de los aportes
        
        Returns:
            float: Promedio de aportes
        """
        total_aportes = self.get_total_aportes()
        if total_aportes == 0:
            return 0.0
        return float(self.monto_actual) / total_aportes
    
    def to_dict(self):
        """
        Convierte el objeto a diccionario
        
        Returns:
            dict: Representación de la meta
        """
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nombre': self.nombre,
            'descripcion': self.descripcion,
            'monto_objetivo': float(self.monto_objetivo),
            'monto_actual': float(self.monto_actual),
            'monto_faltante': self.get_monto_faltante(),
            'porcentaje_completado': self.get_porcentaje_completado(),
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_objetivo': self.fecha_objetivo.isoformat(),
            'dias_restantes': self.get_dias_restantes(),
            'dias_transcurridos': self.get_dias_transcurridos(),
            'ahorro_sugerido_mensual': self.get_ahorro_sugerido_mensual(),
            'ahorro_sugerido_semanal': self.get_ahorro_sugerido_semanal(),
            'completada': self.completada,
            'fecha_completada': self.fecha_completada.isoformat() if self.fecha_completada else None,
            'estado': self.get_estado(),
            'total_aportes': self.get_total_aportes(),
            'promedio_aporte': self.get_promedio_aporte()
        }
    
    def __repr__(self):
        return f'<MetaAhorro {self.nombre} - {self.get_porcentaje_completado():.1f}%>'


class AporteMeta(db.Model):
    """
    Modelo para aportes a las metas de ahorro
    """
    
    __tablename__ = 'aportes_metas'
    
    id = db.Column(db.Integer, primary_key=True)
    meta_id = db.Column(db.Integer, db.ForeignKey('metas_ahorro.id', ondelete='CASCADE'), nullable=False, index=True)
    monto = db.Column(db.Numeric(15, 2), nullable=False)
    fecha_aporte = db.Column(db.Date, nullable=False)
    notas = db.Column(db.Text)
    
    def to_dict(self):
        """Convierte el objeto a diccionario"""
        return {
            'id': self.id,
            'meta_id': self.meta_id,
            'monto': float(self.monto),
            'fecha_aporte': self.fecha_aporte.isoformat(),
            'notas': self.notas
        }
    
    def __repr__(self):
        return f'<AporteMeta ${self.monto} - {self.fecha_aporte}>'