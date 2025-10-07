"""
Modelo de Cuenta
app/models/cuenta.py
"""

from app import db
from datetime import datetime
from sqlalchemy import Enum

class Cuenta(db.Model):
    """
    Modelo para cuentas bancarias y métodos de pago del usuario
    """
    
    __tablename__ = 'cuentas'
    
    # Campos principales
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False, index=True)
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(Enum('efectivo', 'banco', 'tarjeta_credito', 'tarjeta_debito', 'billetera_digital', 
                          name='tipo_cuenta_enum'), nullable=False)
    
    # Campos de saldo
    saldo_inicial = db.Column(db.Numeric(15, 2), default=0.00)
    saldo_actual = db.Column(db.Numeric(15, 2), default=0.00)
    moneda = db.Column(db.String(3), default='COP')
    
    # Campos de control
    activo = db.Column(db.Boolean, default=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relaciones
    transacciones = db.relationship('Transaccion', backref='cuenta', lazy='dynamic')
    
    def __init__(self, **kwargs):
        """Constructor del modelo Cuenta"""
        super(Cuenta, self).__init__(**kwargs)
        # Si no se especifica saldo_actual, tomar el saldo_inicial
        if 'saldo_actual' not in kwargs and 'saldo_inicial' in kwargs:
            self.saldo_actual = kwargs['saldo_inicial']
    
    def actualizar_saldo(self, monto, tipo_transaccion):
        """
        Actualiza el saldo de la cuenta según el tipo de transacción
        
        Args:
            monto (float): Monto de la transacción
            tipo_transaccion (str): 'ingreso' o 'egreso'
        """
        if tipo_transaccion == 'ingreso':
            self.saldo_actual = float(self.saldo_actual) + monto
        elif tipo_transaccion == 'egreso':
            self.saldo_actual = float(self.saldo_actual) - monto
        db.session.commit()
    
    def tiene_saldo_suficiente(self, monto):
        """
        Verifica si la cuenta tiene saldo suficiente para un egreso
        
        Args:
            monto (float): Monto a verificar
            
        Returns:
            bool: True si hay saldo suficiente
        """
        # Las tarjetas de crédito no tienen límite de saldo (conceptualmente)
        if self.tipo == 'tarjeta_credito':
            return True
        return float(self.saldo_actual) >= monto
    
    def get_transacciones_mes(self, mes=None, anio=None):
        """
        Obtiene las transacciones de la cuenta para un mes específico
        
        Args:
            mes (int): Mes a consultar (por defecto mes actual)
            anio (int): Año a consultar (por defecto año actual)
            
        Returns:
            list: Lista de transacciones
        """
        from sqlalchemy import extract
        
        if mes is None:
            mes = datetime.now().month
        if anio is None:
            anio = datetime.now().year
        
        return self.transacciones.filter(
            extract('month', Transaccion.fecha_transaccion) == mes,
            extract('year', Transaccion.fecha_transaccion) == anio
        ).order_by(Transaccion.fecha_transaccion.desc()).all()
    
    def get_ingresos_totales(self):
        """
        Calcula el total de ingresos en esta cuenta
        
        Returns:
            float: Total de ingresos
        """
        from sqlalchemy import func
        
        resultado = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.cuenta_id == self.id,
            Transaccion.tipo == 'ingreso'
        ).scalar()
        
        return float(resultado) if resultado else 0.0
    
    def get_egresos_totales(self):
        """
        Calcula el total de egresos en esta cuenta
        
        Returns:
            float: Total de egresos
        """
        from sqlalchemy import func
        
        resultado = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.cuenta_id == self.id,
            Transaccion.tipo == 'egreso'
        ).scalar()
        
        return float(resultado) if resultado else 0.0
    
    def calcular_balance(self):
        """
        Calcula el balance de la cuenta (saldo_inicial + ingresos - egresos)
        
        Returns:
            float: Balance calculado
        """
        return float(self.saldo_inicial) + self.get_ingresos_totales() - self.get_egresos_totales()
    
    def recalcular_saldo(self):
        """
        Recalcula el saldo actual basándose en las transacciones
        Útil para corregir inconsistencias
        """
        self.saldo_actual = self.calcular_balance()
        db.session.commit()
    
    def puede_eliminar(self):
        """
        Verifica si la cuenta puede ser eliminada
        
        Returns:
            bool: True si puede eliminarse
        """
        return self.transacciones.count() == 0
    
    def get_tipo_icono(self):
        """
        Obtiene el icono de Font Awesome según el tipo de cuenta
        
        Returns:
            str: Clase de icono
        """
        iconos = {
            'efectivo': 'fa-money-bill-wave',
            'banco': 'fa-university',
            'tarjeta_credito': 'fa-credit-card',
            'tarjeta_debito': 'fa-credit-card',
            'billetera_digital': 'fa-wallet'
        }
        return iconos.get(self.tipo, 'fa-circle')
    
    def get_tipo_nombre(self):
        """
        Obtiene el nombre legible del tipo de cuenta
        
        Returns:
            str: Nombre del tipo
        """
        nombres = {
            'efectivo': 'Efectivo',
            'banco': 'Cuenta Bancaria',
            'tarjeta_credito': 'Tarjeta de Crédito',
            'tarjeta_debito': 'Tarjeta de Débito',
            'billetera_digital': 'Billetera Digital'
        }
        return nombres.get(self.tipo, 'Desconocido')
    
    def to_dict(self):
        """
        Convierte el objeto a diccionario
        
        Returns:
            dict: Representación de la cuenta
        """
        return {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'tipo_nombre': self.get_tipo_nombre(),
            'saldo_inicial': float(self.saldo_inicial),
            'saldo_actual': float(self.saldo_actual),
            'moneda': self.moneda,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'icono': self.get_tipo_icono()
        }
    
    def __repr__(self):
        return f'<Cuenta {self.nombre} - ${self.saldo_actual}>'