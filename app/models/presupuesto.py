"""
Modelo de Presupuesto
app/models/presupuesto.py
"""

from app import db
from datetime import datetime
from sqlalchemy import Enum

class Presupuesto(db.Model):
    """
    Modelo para presupuestos de gasto por categoría
    """
    
    __tablename__ = 'presupuestos'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id', ondelete='CASCADE'), nullable=False)
    
    # Detalles del presupuesto
    monto_limite = db.Column(db.Numeric(15, 2), nullable=False)
    periodo = db.Column(Enum('semanal', 'mensual', 'anual', name='periodo_enum'), default='mensual', index=True)
    fecha_inicio = db.Column(db.Date, nullable=False)
    fecha_fin = db.Column(db.Date, nullable=False)
    
    # Alertas
    alertas_activas = db.Column(db.Boolean, default=True)
    porcentaje_alerta = db.Column(db.Integer, default=80)  # Alerta al 80% del límite
    
    def __init__(self, **kwargs):
        """Constructor del modelo Presupuesto"""
        super(Presupuesto, self).__init__(**kwargs)
    
    def get_monto_gastado(self):
        """
        Calcula el monto gastado en este presupuesto
        
        Returns:
            float: Monto gastado
        """
        from sqlalchemy import func
        from app.models.transaccion import Transaccion
        
        resultado = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.usuario_id == self.usuario_id,
            Transaccion.categoria_id == self.categoria_id,
            Transaccion.tipo == 'egreso',
            Transaccion.fecha_transaccion >= self.fecha_inicio,
            Transaccion.fecha_transaccion <= self.fecha_fin
        ).scalar()
        
        return float(resultado) if resultado else 0.0
    
    def get_monto_disponible(self):
        """
        Calcula el monto disponible del presupuesto
        
        Returns:
            float: Monto disponible
        """
        return float(self.monto_limite) - self.get_monto_gastado()
    
    def get_porcentaje_usado(self):
        """
        Calcula el porcentaje usado del presupuesto
        
        Returns:
            float: Porcentaje usado (0-100)
        """
        if float(self.monto_limite) == 0:
            return 0.0
        
        porcentaje = (self.get_monto_gastado() / float(self.monto_limite)) * 100
        return min(porcentaje, 100.0)  # Máximo 100%
    
    def esta_en_alerta(self):
        """
        Verifica si el presupuesto ha alcanzado el porcentaje de alerta
        
        Returns:
            bool: True si está en alerta
        """
        if not self.alertas_activas:
            return False
        return self.get_porcentaje_usado() >= self.porcentaje_alerta
    
    def esta_excedido(self):
        """
        Verifica si el presupuesto ha sido excedido
        
        Returns:
            bool: True si está excedido
        """
        return self.get_monto_gastado() > float(self.monto_limite)
    
    def esta_activo(self):
        """
        Verifica si el presupuesto está activo (dentro del período)
        
        Returns:
            bool: True si está activo
        """
        hoy = datetime.now().date()
        return self.fecha_inicio <= hoy <= self.fecha_fin
    
    def get_estado(self):
        """
        Obtiene el estado del presupuesto
        
        Returns:
            str: 'excedido', 'alerta', 'normal', 'inactivo'
        """
        if not self.esta_activo():
            return 'inactivo'
        if self.esta_excedido():
            return 'excedido'
        if self.esta_en_alerta():
            return 'alerta'
        return 'normal'
    
    def get_clase_css_estado(self):
        """
        Obtiene la clase CSS según el estado
        
        Returns:
            str: Clase CSS de Bootstrap
        """
        estado = self.get_estado()
        clases = {
            'excedido': 'danger',
            'alerta': 'warning',
            'normal': 'success',
            'inactivo': 'secondary'
        }
        return clases.get(estado, 'secondary')
    
    def get_dias_restantes(self):
        """
        Calcula los días restantes del período
        
        Returns:
            int: Número de días restantes
        """
        hoy = datetime.now().date()
        if hoy > self.fecha_fin:
            return 0
        return (self.fecha_fin - hoy).days
    
    def to_dict(self):
        """
        Convierte el objeto a diccionario
        
        Returns:
            dict: Representación del presupuesto
        """
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'categoria_id': self.categoria_id,
            'categoria_nombre': self.categoria.nombre if self.categoria else None,
            'categoria_color': self.categoria.color if self.categoria else None,
            'monto_limite': float(self.monto_limite),
            'monto_gastado': self.get_monto_gastado(),
            'monto_disponible': self.get_monto_disponible(),
            'porcentaje_usado': self.get_porcentaje_usado(),
            'periodo': self.periodo,
            'fecha_inicio': self.fecha_inicio.isoformat(),
            'fecha_fin': self.fecha_fin.isoformat(),
            'dias_restantes': self.get_dias_restantes(),
            'estado': self.get_estado(),
            'alertas_activas': self.alertas_activas,
            'porcentaje_alerta': self.porcentaje_alerta
        }
    
    @staticmethod
    def get_presupuestos_activos(usuario_id):
        """
        Obtiene todos los presupuestos activos de un usuario
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            list: Lista de presupuestos activos
        """
        hoy = datetime.now().date()
        return Presupuesto.query.filter(
            Presupuesto.usuario_id == usuario_id,
            Presupuesto.fecha_inicio <= hoy,
            Presupuesto.fecha_fin >= hoy
        ).all()
    
    @staticmethod
    def get_presupuestos_en_alerta(usuario_id):
        """
        Obtiene los presupuestos que están en alerta
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            list: Lista de presupuestos en alerta
        """
        presupuestos = Presupuesto.get_presupuestos_activos(usuario_id)
        return [p for p in presupuestos if p.esta_en_alerta()]
    
    def __repr__(self):
        return f'<Presupuesto {self.categoria.nombre if self.categoria else "N/A"} - ${self.monto_limite}>'