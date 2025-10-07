"""
Modelo de Categoría
app/models/categoria.py
"""

from app import db
from sqlalchemy import Enum

class Categoria(db.Model):
    """
    Modelo para categorías de transacciones
    Puede ser predefinida del sistema (usuario_id=NULL) o personalizada por usuario
    """
    
    __tablename__ = 'categorias'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(50), nullable=False)
    tipo = db.Column(Enum('ingreso', 'egreso', name='tipo_categoria_enum'), nullable=False, index=True)
    color = db.Column(db.String(7), default='#3498db')
    icono = db.Column(db.String(50), default='fa-circle')
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=True, index=True)
    activo = db.Column(db.Boolean, default=True)
    
    # Relaciones
    transacciones = db.relationship('Transaccion', backref='categoria', lazy='dynamic')
    presupuestos = db.relationship('Presupuesto', backref='categoria', lazy='dynamic')
    
    def __init__(self, **kwargs):
        """Constructor del modelo Categoria"""
        super(Categoria, self).__init__(**kwargs)
    
    def es_predefinida(self):
        """
        Verifica si la categoría es predefinida del sistema
        
        Returns:
            bool: True si es predefinida, False si es personalizada
        """
        return self.usuario_id is None
    
    def puede_eliminar(self):
        """
        Verifica si la categoría puede ser eliminada
        Las categorías con transacciones asociadas no pueden eliminarse
        
        Returns:
            bool: True si puede eliminarse, False en caso contrario
        """
        return self.transacciones.count() == 0
    
    def get_total_gastado_mes(self, mes=None, anio=None):
        """
        Obtiene el total gastado en esta categoría para un mes específico
        
        Args:
            mes (int): Mes a consultar (por defecto mes actual)
            anio (int): Año a consultar (por defecto año actual)
            
        Returns:
            float: Total gastado en la categoría
        """
        from datetime import datetime
        from sqlalchemy import func, extract
        
        if mes is None:
            mes = datetime.now().month
        if anio is None:
            anio = datetime.now().year
        
        resultado = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.categoria_id == self.id,
            Transaccion.tipo == 'egreso',
            extract('month', Transaccion.fecha_transaccion) == mes,
            extract('year', Transaccion.fecha_transaccion) == anio
        ).scalar()
        
        return float(resultado) if resultado else 0.0
    
    def get_numero_transacciones(self):
        """
        Obtiene el número total de transacciones en esta categoría
        
        Returns:
            int: Número de transacciones
        """
        return self.transacciones.count()
    
    def to_dict(self):
        """
        Convierte el objeto a diccionario
        
        Returns:
            dict: Representación de la categoría
        """
        return {
            'id': self.id,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'color': self.color,
            'icono': self.icono,
            'usuario_id': self.usuario_id,
            'activo': self.activo,
            'es_predefinida': self.es_predefinida(),
            'numero_transacciones': self.get_numero_transacciones()
        }
    
    @staticmethod
    def get_categorias_disponibles(usuario_id, tipo=None):
        """
        Obtiene todas las categorías disponibles para un usuario
        (predefinidas del sistema + personalizadas del usuario)
        
        Args:
            usuario_id (int): ID del usuario
            tipo (str): Filtrar por tipo ('ingreso' o 'egreso')
            
        Returns:
            list: Lista de categorías disponibles
        """
        query = Categoria.query.filter(
            db.or_(
                Categoria.usuario_id == None,
                Categoria.usuario_id == usuario_id
            ),
            Categoria.activo == True
        )
        
        if tipo:
            query = query.filter(Categoria.tipo == tipo)
        
        return query.order_by(Categoria.nombre).all()
    
    def __repr__(self):
        return f'<Categoria {self.nombre} ({self.tipo})>'