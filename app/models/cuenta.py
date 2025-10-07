"""
Modelo de Cuenta Completo y Mejorado
app/models/cuenta.py

Este es el archivo COMPLETO que debes usar.
Integra todas las partes (1, 2 y 3) en un solo archivo.

Mejoras implementadas:
- Validaciones con @validates
- Manejo de errores robusto
- Logging de operaciones críticas
- Métodos de auditoría
- Optimización de consultas
- Documentación completa
- Event listeners
- Métodos estáticos útiles
"""

from app import db
from datetime import datetime
from sqlalchemy import Enum, event
from sqlalchemy.orm import validates
from decimal import Decimal
import logging

# Configurar logger
logger = logging.getLogger(__name__)


class Cuenta(db.Model):
    """
    Modelo para cuentas bancarias y métodos de pago del usuario
    
    Tipos de cuenta soportados:
    - efectivo: Dinero en efectivo
    - banco: Cuenta bancaria
    - tarjeta_credito: Tarjeta de crédito
    - tarjeta_debito: Tarjeta de débito
    - billetera_digital: Wallets digitales (PayPal, Nequi, etc.)
    """
    
    __tablename__ = 'cuentas'
    
    # ==========================================
    # CAMPOS PRINCIPALES
    # ==========================================
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(
        db.Integer, 
        db.ForeignKey('usuarios.id', ondelete='CASCADE'), 
        nullable=False, 
        index=True
    )
    nombre = db.Column(db.String(100), nullable=False)
    tipo = db.Column(
        Enum('efectivo', 'banco', 'tarjeta_credito', 'tarjeta_debito', 'billetera_digital', 
             name='tipo_cuenta_enum'), 
        nullable=False
    )
    
    # ==========================================
    # CAMPOS DE SALDO
    # ==========================================
    saldo_inicial = db.Column(db.Numeric(15, 2), default=0.00)
    saldo_actual = db.Column(db.Numeric(15, 2), default=0.00)
    moneda = db.Column(db.String(3), default='COP')
    
    # ==========================================
    # CAMPOS DE CONTROL
    # ==========================================
    activo = db.Column(db.Boolean, default=True, index=True)
    fecha_creacion = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ==========================================
    # CAMPOS ADICIONALES
    # ==========================================
    descripcion = db.Column(db.Text, nullable=True)
    numero_cuenta = db.Column(db.String(50), nullable=True)
    entidad_financiera = db.Column(db.String(100), nullable=True)
    
    # ==========================================
    # RELACIONES
    # ==========================================
    transacciones = db.relationship('Transaccion', backref='cuenta', lazy='dynamic')
    
    def __init__(self, **kwargs):
        """Constructor del modelo Cuenta"""
        super(Cuenta, self).__init__(**kwargs)
        if 'saldo_actual' not in kwargs and 'saldo_inicial' in kwargs:
            self.saldo_actual = kwargs['saldo_inicial']
    
    # ==========================================
    # VALIDACIONES
    # ==========================================
    
    @validates('nombre')
    def validate_nombre(self, key, nombre):
        """Valida el nombre de la cuenta"""
        if not nombre or len(nombre.strip()) < 3:
            raise ValueError("El nombre de la cuenta debe tener al menos 3 caracteres")
        if len(nombre) > 100:
            raise ValueError("El nombre de la cuenta no puede exceder 100 caracteres")
        return nombre.strip()
    
    @validates('saldo_inicial', 'saldo_actual')
    def validate_saldo(self, key, saldo):
        """Valida los saldos"""
        if saldo is None:
            return Decimal('0.00')
        
        saldo = Decimal(str(saldo))
        
        if self.tipo != 'tarjeta_credito' and saldo < 0:
            raise ValueError(f"El {key.replace('_', ' ')} no puede ser negativo para este tipo de cuenta")
        
        return saldo
    
    @validates('tipo')
    def validate_tipo(self, key, tipo):
        """Valida el tipo de cuenta"""
        tipos_validos = ['efectivo', 'banco', 'tarjeta_credito', 'tarjeta_debito', 'billetera_digital']
        if tipo not in tipos_validos:
            raise ValueError(f"Tipo de cuenta inválido. Debe ser uno de: {', '.join(tipos_validos)}")
        return tipo
    
    @validates('moneda')
    def validate_moneda(self, key, moneda):
        """Valida la moneda"""
        monedas_validas = ['COP', 'USD', 'EUR', 'MXN', 'ARS', 'CLP', 'PEN', 'BRL']
        if moneda not in monedas_validas:
            logger.warning(f"Moneda no estándar detectada: {moneda}")
        return moneda.upper()
    
    # ==========================================
    # MÉTODOS DE SALDO
    # ==========================================
    
    def actualizar_saldo(self, monto, tipo_transaccion, commit=True):
        """
        Actualiza el saldo de la cuenta según el tipo de transacción
        
        Args:
            monto (float/Decimal): Monto de la transacción
            tipo_transaccion (str): 'ingreso' o 'egreso'
            commit (bool): Si debe hacer commit a la base de datos
            
        Raises:
            ValueError: Si el tipo de transacción es inválido o no hay saldo suficiente
        """
        try:
            monto = Decimal(str(monto))
            
            if tipo_transaccion == 'ingreso':
                self.saldo_actual = Decimal(str(self.saldo_actual)) + monto
                logger.info(f"Ingreso de {monto} a cuenta {self.id} ({self.nombre})")
                
            elif tipo_transaccion == 'egreso':
                if not self.tiene_saldo_suficiente(monto):
                    raise ValueError(
                        f"Saldo insuficiente en {self.nombre}. "
                        f"Saldo actual: {self.saldo_actual}, "
                        f"Monto requerido: {monto}"
                    )
                
                self.saldo_actual = Decimal(str(self.saldo_actual)) - monto
                logger.info(f"Egreso de {monto} de cuenta {self.id} ({self.nombre})")
                
            else:
                raise ValueError(f"Tipo de transacción inválido: {tipo_transaccion}")
            
            self.fecha_modificacion = datetime.utcnow()
            
            if commit:
                db.session.commit()
                
        except ValueError as ve:
            db.session.rollback()
            logger.error(f"Error en actualización de saldo: {str(ve)}")
            raise ve
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error inesperado al actualizar saldo: {str(e)}")
            raise Exception(f"Error al actualizar saldo: {str(e)}")
    
    def tiene_saldo_suficiente(self, monto):
        """Verifica si la cuenta tiene saldo suficiente para un egreso"""
        if self.tipo == 'tarjeta_credito':
            return True
        monto = Decimal(str(monto))
        return Decimal(str(self.saldo_actual)) >= monto
    
    def recalcular_saldo(self, commit=True):
        """Recalcula el saldo actual basándose en las transacciones"""
        try:
            saldo_anterior = Decimal(str(self.saldo_actual))
            saldo_calculado = self.calcular_balance()
            diferencia = saldo_calculado - saldo_anterior
            
            self.saldo_actual = saldo_calculado
            self.fecha_modificacion = datetime.utcnow()
            
            if commit:
                db.session.commit()
            
            resultado = {
                'saldo_anterior': float(saldo_anterior),
                'saldo_nuevo': float(saldo_calculado),
                'diferencia': float(diferencia),
                'mensaje': 'Saldo recalculado correctamente'
            }
            
            if diferencia != 0:
                logger.warning(
                    f"Diferencia detectada en cuenta {self.id}: "
                    f"{diferencia} (anterior: {saldo_anterior}, nuevo: {saldo_calculado})"
                )
            
            return resultado
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al recalcular saldo: {str(e)}")
            raise e
    
    # ==========================================
    # MÉTODOS DE CONSULTA
    # ==========================================
    
    def get_transacciones_mes(self, mes=None, anio=None):
        """Obtiene las transacciones de la cuenta para un mes específico"""
        from sqlalchemy import extract
        from app.models.transaccion import Transaccion
        
        if mes is None:
            mes = datetime.now().month
        if anio is None:
            anio = datetime.now().year
        
        return self.transacciones.filter(
            extract('month', Transaccion.fecha_transaccion) == mes,
            extract('year', Transaccion.fecha_transaccion) == anio
        ).order_by(Transaccion.fecha_transaccion.desc()).all()
    
    def get_ingresos_totales(self, fecha_inicio=None, fecha_fin=None):
        """Calcula el total de ingresos en esta cuenta"""
        from sqlalchemy import func
        from app.models.transaccion import Transaccion
        
        query = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.cuenta_id == self.id,
            Transaccion.tipo == 'ingreso'
        )
        
        if fecha_inicio:
            query = query.filter(Transaccion.fecha_transaccion >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Transaccion.fecha_transaccion <= fecha_fin)
        
        resultado = query.scalar()
        return Decimal(str(resultado)) if resultado else Decimal('0.00')
    
    def get_egresos_totales(self, fecha_inicio=None, fecha_fin=None):
        """Calcula el total de egresos en esta cuenta"""
        from sqlalchemy import func
        from app.models.transaccion import Transaccion
        
        query = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.cuenta_id == self.id,
            Transaccion.tipo == 'egreso'
        )
        
        if fecha_inicio:
            query = query.filter(Transaccion.fecha_transaccion >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Transaccion.fecha_transaccion <= fecha_fin)
        
        resultado = query.scalar()
        return Decimal(str(resultado)) if resultado else Decimal('0.00')
    
    def calcular_balance(self):
        """Calcula el balance de la cuenta"""
        ingresos = self.get_ingresos_totales()
        egresos = self.get_egresos_totales()
        balance = Decimal(str(self.saldo_inicial)) + ingresos - egresos
        return balance
    
    def get_estadisticas(self, mes=None, anio=None):
        """Obtiene estadísticas de la cuenta para un período"""
        from datetime import date
        
        if mes and anio:
            from calendar import monthrange
            fecha_inicio = date(anio, mes, 1)
            ultimo_dia = monthrange(anio, mes)[1]
            fecha_fin = date(anio, mes, ultimo_dia)
        else:
            fecha_inicio = None
            fecha_fin = None
        
        ingresos = self.get_ingresos_totales(fecha_inicio, fecha_fin)
        egresos = self.get_egresos_totales(fecha_inicio, fecha_fin)
        
        return {
            'saldo_actual': float(self.saldo_actual),
            'saldo_inicial': float(self.saldo_inicial),
            'ingresos': float(ingresos),
            'egresos': float(egresos),
            'balance': float(ingresos - egresos),
            'num_transacciones': self.get_numero_transacciones(fecha_inicio, fecha_fin)
        }
    
    def get_numero_transacciones(self, fecha_inicio=None, fecha_fin=None):
        """Obtiene el número de transacciones en un rango de fechas"""
        from app.models.transaccion import Transaccion
        
        query = self.transacciones
        
        if fecha_inicio:
            query = query.filter(Transaccion.fecha_transaccion >= fecha_inicio)
        if fecha_fin:
            query = query.filter(Transaccion.fecha_transaccion <= fecha_fin)
        
        return query.count()
    
    # ==========================================
    # MÉTODOS DE VALIDACIÓN
    # ==========================================
    
    def puede_eliminar(self):
        """Verifica si la cuenta puede ser eliminada"""
        num_transacciones = self.transacciones.count()
        
        if num_transacciones > 0:
            return False, f"No se puede eliminar. La cuenta tiene {num_transacciones} transacción(es)."
        
        return True, "La cuenta puede ser eliminada."
    
    def puede_desactivar(self):
        """Verifica si la cuenta puede ser desactivada"""
        if not self.activo:
            return False, "La cuenta ya está desactivada."
        
        saldo = Decimal(str(self.saldo_actual))
        if saldo != 0:
            return False, f"No se puede desactivar. La cuenta tiene un saldo de {self.saldo_actual}."
        
        return True, "La cuenta puede ser desactivada."
    
    def desactivar(self, commit=True):
        """Desactiva la cuenta"""
        puede, mensaje = self.puede_desactivar()
        
        if not puede:
            raise ValueError(mensaje)
        
        self.activo = False
        self.fecha_modificacion = datetime.utcnow()
        
        if commit:
            db.session.commit()
        
        logger.info(f"Cuenta {self.id} ({self.nombre}) desactivada")
    
    def activar(self, commit=True):
        """Activa la cuenta"""
        self.activo = True
        self.fecha_modificacion = datetime.utcnow()
        
        if commit:
            db.session.commit()
        
        logger.info(f"Cuenta {self.id} ({self.nombre}) activada")
    
    # ==========================================
    # MÉTODOS DE UTILIDAD
    # ==========================================
    
    def get_tipo_icono(self):
        """Obtiene el icono de Font Awesome según el tipo de cuenta"""
        iconos = {
            'efectivo': 'fa-money-bill-wave',
            'banco': 'fa-university',
            'tarjeta_credito': 'fa-credit-card',
            'tarjeta_debito': 'fa-credit-card',
            'billetera_digital': 'fa-wallet'
        }
        return iconos.get(self.tipo, 'fa-circle')
    
    def get_tipo_nombre(self):
        """Obtiene el nombre legible del tipo de cuenta"""
        nombres = {
            'efectivo': 'Efectivo',
            'banco': 'Cuenta Bancaria',
            'tarjeta_credito': 'Tarjeta de Crédito',
            'tarjeta_debito': 'Tarjeta de Débito',
            'billetera_digital': 'Billetera Digital'
        }
        return nombres.get(self.tipo, 'Desconocido')
    
    def get_color_tipo(self):
        """Obtiene un color representativo según el tipo de cuenta"""
        colores = {
            'efectivo': '#2ecc71',
            'banco': '#3498db',
            'tarjeta_credito': '#e74c3c',
            'tarjeta_debito': '#9b59b6',
            'billetera_digital': '#f39c12'
        }
        return colores.get(self.tipo, '#95a5a6')
    
    def get_saldo_formateado(self, incluir_moneda=True):
        """Obtiene el saldo actual formateado"""
        saldo = float(self.saldo_actual)
        
        if incluir_moneda:
            simbolos = {
                'COP': '$',
                'USD': 'US$',
                'EUR': '€',
                'MXN': 'MX$',
                'ARS': 'AR$',
                'CLP': 'CL$',
                'PEN': 'S/.',
                'BRL': 'R$'
            }
            simbolo = simbolos.get(self.moneda, self.moneda + ' ')
            return f'{simbolo}{saldo:,.2f}'
        
        return f'{saldo:,.2f}'
    
    def to_dict(self, incluir_estadisticas=False):
        """Convierte el objeto a diccionario"""
        datos = {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'nombre': self.nombre,
            'tipo': self.tipo,
            'tipo_nombre': self.get_tipo_nombre(),
            'saldo_inicial': float(self.saldo_inicial),
            'saldo_actual': float(self.saldo_actual),
            'saldo_formateado': self.get_saldo_formateado(),
            'moneda': self.moneda,
            'activo': self.activo,
            'fecha_creacion': self.fecha_creacion.isoformat() if self.fecha_creacion else None,
            'fecha_modificacion': self.fecha_modificacion.isoformat() if self.fecha_modificacion else None,
            'icono': self.get_tipo_icono(),
            'color': self.get_color_tipo(),
            'descripcion': self.descripcion,
            'numero_cuenta': self.numero_cuenta,
            'entidad_financiera': self.entidad_financiera
        }
        
        if incluir_estadisticas:
            datos['estadisticas'] = self.get_estadisticas()
        
        return datos
    
    # ==========================================
    # MÉTODOS ESTÁTICOS
    # ==========================================
    
    @staticmethod
    def get_cuentas_activas_usuario(usuario_id):
        """Obtiene todas las cuentas activas de un usuario"""
        return Cuenta.query.filter_by(
            usuario_id=usuario_id,
            activo=True
        ).order_by(Cuenta.nombre).all()
    
    @staticmethod
    def get_saldo_total_usuario(usuario_id, moneda=None):
        """Calcula el saldo total de todas las cuentas activas de un usuario"""
        from sqlalchemy import func
        
        query = db.session.query(func.sum(Cuenta.saldo_actual)).filter(
            Cuenta.usuario_id == usuario_id,
            Cuenta.activo == True
        )
        
        if moneda:
            query = query.filter(Cuenta.moneda == moneda)
        
        resultado = query.scalar()
        return Decimal(str(resultado)) if resultado else Decimal('0.00')
    
    @staticmethod
    def validar_nombre_unico(usuario_id, nombre, cuenta_id=None):
        """Valida que el nombre de la cuenta sea único para el usuario"""
        query = Cuenta.query.filter_by(
            usuario_id=usuario_id,
            nombre=nombre
        )
        
        if cuenta_id:
            query = query.filter(Cuenta.id != cuenta_id)
        
        return query.first() is None
    
    def __repr__(self):
        return f'<Cuenta {self.nombre} - {self.get_saldo_formateado()}>'


# ==========================================
# EVENT LISTENERS
# ==========================================

@event.listens_for(Cuenta, 'before_update')
def recibir_before_update(mapper, connection, target):
    """Actualiza fecha_modificacion antes de cada update"""
    target.fecha_modificacion = datetime.utcnow()


@event.listens_for(Cuenta, 'before_delete')
def prevenir_eliminacion_con_transacciones(mapper, connection, target):
    """Previene la eliminación de cuentas con transacciones"""
    puede_eliminar, mensaje = target.puede_eliminar()
    if not puede_eliminar:
        raise ValueError(mensaje)


@event.listens_for(Cuenta, 'after_insert')
def registrar_creacion_cuenta(mapper, connection, target):
    """Registra la creación de una nueva cuenta en el log"""
    logger.info(
        f"Nueva cuenta creada: {target.nombre} ({target.tipo}) "
        f"para usuario {target.usuario_id}"
    )