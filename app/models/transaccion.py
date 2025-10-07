"""
Modelo de Transacción
app/models/transaccion.py
"""

from app import db
from datetime import datetime, time
from sqlalchemy import Enum

class Transaccion(db.Model):
    """
    Modelo para transacciones (ingresos y egresos)
    Núcleo de la aplicación
    """
    
    __tablename__ = 'transacciones'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    cuenta_id = db.Column(db.Integer, db.ForeignKey('cuentas.id', ondelete='RESTRICT'), nullable=False)
    categoria_id = db.Column(db.Integer, db.ForeignKey('categorias.id', ondelete='RESTRICT'), nullable=False, index=True)
    
    # Detalles de la transacción
    tipo = db.Column(Enum('ingreso', 'egreso', name='tipo_transaccion_enum'), nullable=False, index=True)
    monto = db.Column(db.Numeric(15, 2), nullable=False)
    descripcion = db.Column(db.Text)
    
    # Fechas
    fecha_transaccion = db.Column(db.Date, nullable=False, index=True)
    hora_transaccion = db.Column(db.Time, default=time(0, 0, 0))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Transacciones recurrentes
    recurrente = db.Column(db.Boolean, default=False)
    frecuencia_recurrencia = db.Column(Enum('diaria', 'semanal', 'quincenal', 'mensual', 'anual', 
                                            name='frecuencia_enum'), nullable=True)
    
    # Campos adicionales
    etiquetas = db.Column(db.String(255))  # Tags separados por comas
    comprobante_url = db.Column(db.String(255))
    
    def __init__(self, **kwargs):
        """Constructor del modelo Transaccion"""
        super(Transaccion, self).__init__(**kwargs)
        
        # Si no se especifica fecha_transaccion, usar la fecha actual
        if 'fecha_transaccion' not in kwargs:
            self.fecha_transaccion = datetime.now().date()
        
        # Si no se especifica hora, usar la hora actual
        if 'hora_transaccion' not in kwargs:
            self.hora_transaccion = datetime.now().time()
    
    def get_etiquetas_lista(self):
        """
        Obtiene las etiquetas como lista
        
        Returns:
            list: Lista de etiquetas
        """
        if not self.etiquetas:
            return []
        return [tag.strip() for tag in self.etiquetas.split(',') if tag.strip()]
    
    def set_etiquetas_lista(self, lista_etiquetas):
        """
        Establece las etiquetas desde una lista
        
        Args:
            lista_etiquetas (list): Lista de etiquetas
        """
        if lista_etiquetas:
            self.etiquetas = ','.join([tag.strip() for tag in lista_etiquetas if tag.strip()])
        else:
            self.etiquetas = None
    
    def get_fecha_hora_completa(self):
        """
        Combina fecha y hora en un datetime
        
        Returns:
            datetime: Fecha y hora combinadas
        """
        return datetime.combine(self.fecha_transaccion, self.hora_transaccion)
    
    def es_ingreso(self):
        """Verifica si la transacción es un ingreso"""
        return self.tipo == 'ingreso'
    
    def es_egreso(self):
        """Verifica si la transacción es un egreso"""
        return self.tipo == 'egreso'
    
    def get_monto_formateado(self, incluir_signo=True):
        """
        Obtiene el monto formateado con su signo
        
        Args:
            incluir_signo (bool): Si debe incluir + o -
            
        Returns:
            str: Monto formateado
        """
        monto = float(self.monto)
        if incluir_signo:
            signo = '+' if self.es_ingreso() else '-'
            return f'{signo}${monto:,.2f}'
        return f'${monto:,.2f}'
    
    def get_tipo_clase_css(self):
        """
        Obtiene la clase CSS según el tipo de transacción
        
        Returns:
            str: Clase CSS
        """
        return 'text-success' if self.es_ingreso() else 'text-danger'
    
    def puede_editar(self, usuario_id):
        """
        Verifica si un usuario puede editar esta transacción
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            bool: True si puede editar
        """
        return self.usuario_id == usuario_id
    
    def to_dict(self):
        """
        Convierte el objeto a diccionario
        
        Returns:
            dict: Representación de la transacción
        """
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'cuenta_id': self.cuenta_id,
            'cuenta_nombre': self.cuenta.nombre if self.cuenta else None,
            'categoria_id': self.categoria_id,
            'categoria_nombre': self.categoria.nombre if self.categoria else None,
            'categoria_color': self.categoria.color if self.categoria else None,
            'tipo': self.tipo,
            'monto': float(self.monto),
            'monto_formateado': self.get_monto_formateado(),
            'descripcion': self.descripcion,
            'fecha_transaccion': self.fecha_transaccion.isoformat(),
            'hora_transaccion': self.hora_transaccion.isoformat() if self.hora_transaccion else None,
            'recurrente': self.recurrente,
            'frecuencia_recurrencia': self.frecuencia_recurrencia,
            'etiquetas': self.get_etiquetas_lista(),
            'comprobante_url': self.comprobante_url
        }
    
    @staticmethod
    def get_transacciones_por_periodo(usuario_id, fecha_inicio, fecha_fin):
        """
        Obtiene transacciones de un usuario en un período específico
        
        Args:
            usuario_id (int): ID del usuario
            fecha_inicio (date): Fecha de inicio
            fecha_fin (date): Fecha de fin
            
        Returns:
            list: Lista de transacciones
        """
        return Transaccion.query.filter(
            Transaccion.usuario_id == usuario_id,
            Transaccion.fecha_transaccion >= fecha_inicio,
            Transaccion.fecha_transaccion <= fecha_fin
        ).order_by(Transaccion.fecha_transaccion.desc(), Transaccion.hora_transaccion.desc()).all()
    
    @staticmethod
    def get_resumen_por_categoria(usuario_id, fecha_inicio, fecha_fin, tipo=None):
        """
        Obtiene un resumen de transacciones agrupadas por categoría
        
        Args:
            usuario_id (int): ID del usuario
            fecha_inicio (date): Fecha de inicio
            fecha_fin (date): Fecha de fin
            tipo (str): 'ingreso' o 'egreso' (opcional)
            
        Returns:
            list: Lista de tuplas (categoria, total)
        """
        from sqlalchemy import func
        from app.models.categoria import Categoria
        
        query = db.session.query(
            Categoria.nombre,
            Categoria.color,
            func.sum(Transaccion.monto).label('total')
        ).join(Transaccion).filter(
            Transaccion.usuario_id == usuario_id,
            Transaccion.fecha_transaccion >= fecha_inicio,
            Transaccion.fecha_transaccion <= fecha_fin
        )
        
        if tipo:
            query = query.filter(Transaccion.tipo == tipo)
        
        return query.group_by(Categoria.id).all()
    
    def __repr__(self):
        return f'<Transaccion {self.tipo} ${self.monto} - {self.fecha_transaccion}>'