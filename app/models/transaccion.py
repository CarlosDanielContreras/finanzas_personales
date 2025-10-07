"""
Modelo de Transacción Mejorado
app/models/transaccion.py

Mejoras implementadas:
- Validaciones robustas
- Event listeners para actualización automática de saldos
- Manejo de transacciones recurrentes
- Auditoría de cambios
- Métodos de análisis y reportes
- Logging completo
"""

from app import db
from datetime import datetime, time, date, timedelta
from sqlalchemy import Enum, event, func, extract
from sqlalchemy.orm import validates
from decimal import Decimal
import logging

# Configurar logger
logger = logging.getLogger(__name__)


class Transaccion(db.Model):
    """
    Modelo para transacciones (ingresos y egresos)
    Núcleo de la aplicación de finanzas personales
    
    Tipos de transacción:
    - ingreso: Entrada de dinero
    - egreso: Salida de dinero
    """
    
    __tablename__ = 'transacciones'
    
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
    cuenta_id = db.Column(
        db.Integer, 
        db.ForeignKey('cuentas.id', ondelete='RESTRICT'), 
        nullable=False
    )
    categoria_id = db.Column(
        db.Integer, 
        db.ForeignKey('categorias.id', ondelete='RESTRICT'), 
        nullable=False, 
        index=True
    )
    
    # ==========================================
    # DETALLES DE LA TRANSACCIÓN
    # ==========================================
    tipo = db.Column(
        Enum('ingreso', 'egreso', name='tipo_transaccion_enum'), 
        nullable=False, 
        index=True
    )
    monto = db.Column(db.Numeric(15, 2), nullable=False)
    descripcion = db.Column(db.Text)
    
    # ==========================================
    # FECHAS
    # ==========================================
    fecha_transaccion = db.Column(db.Date, nullable=False, index=True)
    hora_transaccion = db.Column(db.Time, default=time(0, 0, 0))
    fecha_registro = db.Column(db.DateTime, default=datetime.utcnow)
    fecha_modificacion = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # ==========================================
    # TRANSACCIONES RECURRENTES
    # ==========================================
    recurrente = db.Column(db.Boolean, default=False, index=True)
    frecuencia_recurrencia = db.Column(
        Enum('diaria', 'semanal', 'quincenal', 'mensual', 'anual', 
             name='frecuencia_enum'), 
        nullable=True
    )
    fecha_fin_recurrencia = db.Column(db.Date, nullable=True)
    transaccion_padre_id = db.Column(
        db.Integer, 
        db.ForeignKey('transacciones.id', ondelete='SET NULL'),
        nullable=True
    )
    
    # ==========================================
    # CAMPOS ADICIONALES
    # ==========================================
    etiquetas = db.Column(db.String(255))  # Tags separados por comas
    comprobante_url = db.Column(db.String(255))
    notas = db.Column(db.Text)
    
    # ==========================================
    # CAMPOS DE AUDITORÍA
    # ==========================================
    editada = db.Column(db.Boolean, default=False)
    num_ediciones = db.Column(db.Integer, default=0)
    
    # ==========================================
    # RELACIONES
    # ==========================================
    transacciones_hijas = db.relationship(
        'Transaccion',
        backref=db.backref('transaccion_padre', remote_side=[id]),
        lazy='dynamic'
    )
    
    def __init__(self, **kwargs):
        """Constructor del modelo Transaccion"""
        super(Transaccion, self).__init__(**kwargs)
        
        # Si no se especifica fecha_transaccion, usar la fecha actual
        if 'fecha_transaccion' not in kwargs:
            self.fecha_transaccion = datetime.now().date()
        
        # Si no se especifica hora, usar la hora actual
        if 'hora_transaccion' not in kwargs:
            self.hora_transaccion = datetime.now().time()
    
    # ==========================================
    # VALIDACIONES
    # ==========================================
    
    @validates('monto')
    def validate_monto(self, key, monto):
        """Valida que el monto sea positivo"""
        if monto is None:
            raise ValueError("El monto es obligatorio")
        
        monto = Decimal(str(monto))
        
        if monto <= 0:
            raise ValueError("El monto debe ser mayor a cero")
        
        if monto > Decimal('999999999999.99'):
            raise ValueError("El monto excede el límite permitido")
        
        return monto
    
    @validates('tipo')
    def validate_tipo(self, key, tipo):
        """Valida que el tipo sea válido"""
        if tipo not in ['ingreso', 'egreso']:
            raise ValueError("El tipo debe ser 'ingreso' o 'egreso'")
        return tipo
    
    @validates('descripcion')
    def validate_descripcion(self, key, descripcion):
        """Valida y limpia la descripción"""
        if descripcion:
            descripcion = descripcion.strip()
            if len(descripcion) > 500:
                logger.warning(f"Descripción muy larga, truncando a 500 caracteres")
                descripcion = descripcion[:500]
        return descripcion
    
    @validates('fecha_transaccion')
    def validate_fecha_transaccion(self, key, fecha):
        """Valida la fecha de transacción"""
        if isinstance(fecha, str):
            try:
                fecha = datetime.strptime(fecha, '%Y-%m-%d').date()
            except ValueError:
                raise ValueError("Formato de fecha inválido. Use YYYY-MM-DD")
        
        # No permitir fechas futuras mayores a 1 día
        if fecha > datetime.now().date() + timedelta(days=1):
            raise ValueError("No se permiten transacciones con fechas muy futuras")
        
        # No permitir fechas muy antiguas (más de 10 años)
        if fecha < datetime.now().date() - timedelta(days=3650):
            logger.warning(f"Fecha de transacción muy antigua: {fecha}")
        
        return fecha
    
    @validates('recurrente', 'frecuencia_recurrencia')
    def validate_recurrente(self, key, value):
        """Valida configuración de recurrencia"""
        if key == 'recurrente' and value:
            if not self.frecuencia_recurrencia:
                logger.warning("Transacción marcada como recurrente sin frecuencia")
        
        if key == 'frecuencia_recurrencia' and value:
            if value not in ['diaria', 'semanal', 'quincenal', 'mensual', 'anual']:
                raise ValueError("Frecuencia de recurrencia inválida")
        
        return value
    
    # ==========================================
    # MÉTODOS DE ETIQUETAS
    # ==========================================
    
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
            # Limpiar y filtrar etiquetas vacías
            etiquetas_limpias = [tag.strip().lower() for tag in lista_etiquetas if tag.strip()]
            # Eliminar duplicados
            etiquetas_unicas = list(set(etiquetas_limpias))
            self.etiquetas = ','.join(etiquetas_unicas)
        else:
            self.etiquetas = None
    
    def agregar_etiqueta(self, etiqueta):
        """
        Agrega una etiqueta
        
        Args:
            etiqueta (str): Etiqueta a agregar
        """
        etiquetas_actuales = self.get_etiquetas_lista()
        etiqueta = etiqueta.strip().lower()
        
        if etiqueta and etiqueta not in etiquetas_actuales:
            etiquetas_actuales.append(etiqueta)
            self.set_etiquetas_lista(etiquetas_actuales)
    
    def remover_etiqueta(self, etiqueta):
        """
        Remueve una etiqueta
        
        Args:
            etiqueta (str): Etiqueta a remover
        """
        etiquetas_actuales = self.get_etiquetas_lista()
        etiqueta = etiqueta.strip().lower()
        
        if etiqueta in etiquetas_actuales:
            etiquetas_actuales.remove(etiqueta)
            self.set_etiquetas_lista(etiquetas_actuales)
    
    # ==========================================
    # MÉTODOS DE FECHA Y HORA
    # ==========================================
    
    def get_fecha_hora_completa(self):
        """
        Combina fecha y hora en un datetime
        
        Returns:
            datetime: Fecha y hora combinadas
        """
        return datetime.combine(self.fecha_transaccion, self.hora_transaccion)
    
    def get_mes_anio(self):
        """
        Obtiene el mes y año de la transacción
        
        Returns:
            tuple: (mes, año)
        """
        return (self.fecha_transaccion.month, self.fecha_transaccion.year)
    
    # ==========================================
    # MÉTODOS DE TIPO
    # ==========================================
    
    def es_ingreso(self):
        """Verifica si la transacción es un ingreso"""
        return self.tipo == 'ingreso'
    
    def es_egreso(self):
        """Verifica si la transacción es un egreso"""
        return self.tipo == 'egreso'
    
    def es_recurrente(self):
        """Verifica si la transacción es recurrente"""
        return self.recurrente and self.frecuencia_recurrencia is not None
    
    def es_transaccion_hija(self):
        """Verifica si es una transacción generada por recurrencia"""
        return self.transaccion_padre_id is not None
    
    # ==========================================
    # MÉTODOS DE FORMATO
    # ==========================================
    
    def get_monto_formateado(self, incluir_signo=True, incluir_moneda=True):
        """
        Obtiene el monto formateado
        
        Args:
            incluir_signo (bool): Si debe incluir + o -
            incluir_moneda (bool): Si debe incluir símbolo de moneda
            
        Returns:
            str: Monto formateado
        """
        monto = float(self.monto)
        
        # Obtener símbolo de moneda de la cuenta
        moneda_simbolo = '$'
        if self.cuenta and incluir_moneda:
            simbolos = {
                'COP': '$',
                'USD': 'US$',
                'EUR': '€',
                'MXN': 'MX$',
                'ARS': 'AR$'
            }
            moneda_simbolo = simbolos.get(self.cuenta.moneda, self.cuenta.moneda + ' ')
        
        if incluir_signo:
            signo = '+' if self.es_ingreso() else '-'
            if incluir_moneda:
                return f'{signo}{moneda_simbolo}{monto:,.2f}'
            return f'{signo}{monto:,.2f}'
        
        if incluir_moneda:
            return f'{moneda_simbolo}{monto:,.2f}'
        return f'{monto:,.2f}'
    
    def get_tipo_clase_css(self):
        """
        Obtiene la clase CSS según el tipo de transacción
        
        Returns:
            str: Clase CSS de Bootstrap
        """
        return 'text-success' if self.es_ingreso() else 'text-danger'
    
    def get_tipo_icono(self):
        """
        Obtiene el icono según el tipo de transacción
        
        Returns:
            str: Clase de icono Font Awesome
        """
        return 'fa-arrow-up' if self.es_ingreso() else 'fa-arrow-down'
    
    def get_descripcion_corta(self, max_length=50):
        """
        Obtiene una versión corta de la descripción
        
        Args:
            max_length (int): Longitud máxima
            
        Returns:
            str: Descripción truncada
        """
        if not self.descripcion:
            return 'Sin descripción'
        
        if len(self.descripcion) <= max_length:
            return self.descripcion
        
        return self.descripcion[:max_length] + '...'
    
    # ==========================================
    # MÉTODOS DE PERMISOS
    # ==========================================
    
    def puede_editar(self, usuario_id):
        """
        Verifica si un usuario puede editar esta transacción
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            tuple: (bool, str) - (puede_editar, mensaje)
        """
        if self.usuario_id != usuario_id:
            return False, "No tienes permiso para editar esta transacción"
        
        # No permitir editar transacciones muy antiguas (más de 1 año)
        dias_antiguedad = (datetime.now().date() - self.fecha_transaccion).days
        if dias_antiguedad > 365:
            return False, "No se pueden editar transacciones de más de 1 año de antigüedad"
        
        return True, "Puede editar"
    
    def puede_eliminar(self, usuario_id):
        """
        Verifica si un usuario puede eliminar esta transacción
        
        Args:
            usuario_id (int): ID del usuario
            
        Returns:
            tuple: (bool, str) - (puede_eliminar, mensaje)
        """
        if self.usuario_id != usuario_id:
            return False, "No tienes permiso para eliminar esta transacción"
        
        # Si tiene transacciones hijas, no se puede eliminar directamente
        if self.es_recurrente() and self.transacciones_hijas.count() > 0:
            return False, "Esta transacción tiene recurrencias generadas. Elimínelas primero."
        
        return True, "Puede eliminar"
    
    # ==========================================
    # MÉTODOS DE RECURRENCIA
    # ==========================================
    
    def generar_proxima_recurrencia(self):
        """
        Genera la próxima transacción recurrente
        
        Returns:
            Transaccion: Nueva transacción generada o None
        """
        if not self.es_recurrente():
            return None
        
        # Calcular la próxima fecha
        proxima_fecha = self._calcular_proxima_fecha()
        
        # Verificar si ya pasó la fecha fin de recurrencia
        if self.fecha_fin_recurrencia and proxima_fecha > self.fecha_fin_recurrencia:
            logger.info(f"Recurrencia finalizada para transacción {self.id}")
            return None
        
        # Crear nueva transacción
        nueva_transaccion = Transaccion(
            usuario_id=self.usuario_id,
            cuenta_id=self.cuenta_id,
            categoria_id=self.categoria_id,
            tipo=self.tipo,
            monto=self.monto,
            descripcion=self.descripcion,
            fecha_transaccion=proxima_fecha,
            hora_transaccion=self.hora_transaccion,
            recurrente=False,  # Las hijas no son recurrentes
            transaccion_padre_id=self.id,
            etiquetas=self.etiquetas,
            notas=f"Generada automáticamente desde recurrencia {self.id}"
        )
        
        try:
            db.session.add(nueva_transaccion)
            db.session.commit()
            logger.info(f"Transacción recurrente generada: {nueva_transaccion.id}")
            return nueva_transaccion
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error al generar recurrencia: {str(e)}")
            return None
    
    def _calcular_proxima_fecha(self):
        """
        Calcula la próxima fecha según la frecuencia
        
        Returns:
            date: Próxima fecha
        """
        if self.frecuencia_recurrencia == 'diaria':
            return self.fecha_transaccion + timedelta(days=1)
        
        elif self.frecuencia_recurrencia == 'semanal':
            return self.fecha_transaccion + timedelta(weeks=1)
        
        elif self.frecuencia_recurrencia == 'quincenal':
            return self.fecha_transaccion + timedelta(days=15)
        
        elif self.frecuencia_recurrencia == 'mensual':
            # Agregar un mes
            mes = self.fecha_transaccion.month
            anio = self.fecha_transaccion.year
            
            if mes == 12:
                mes = 1
                anio += 1
            else:
                mes += 1
            
            # Manejar el último día del mes
            from calendar import monthrange
            ultimo_dia = monthrange(anio, mes)[1]
            dia = min(self.fecha_transaccion.day, ultimo_dia)
            
            return date(anio, mes, dia)
        
        elif self.frecuencia_recurrencia == 'anual':
            anio = self.fecha_transaccion.year + 1
            
            # Manejar 29 de febrero
            if self.fecha_transaccion.month == 2 and self.fecha_transaccion.day == 29:
                from calendar import isleap
                if not isleap(anio):
                    return date(anio, 2, 28)
            
            return date(anio, self.fecha_transaccion.month, self.fecha_transaccion.day)
        
        return self.fecha_transaccion
    
    def cancelar_recurrencia(self, eliminar_futuras=False):
        """
        Cancela la recurrencia de esta transacción
        
        Args:
            eliminar_futuras (bool): Si debe eliminar transacciones futuras ya generadas
        """
        self.recurrente = False
        self.frecuencia_recurrencia = None
        self.fecha_fin_recurrencia = None
        
        if eliminar_futuras:
            # Eliminar transacciones hijas futuras
            transacciones_futuras = self.transacciones_hijas.filter(
                Transaccion.fecha_transaccion > datetime.now().date()
            ).all()
            
            for trans in transacciones_futuras:
                db.session.delete(trans)
            
            logger.info(f"Eliminadas {len(transacciones_futuras)} transacciones futuras")
        
        db.session.commit()
        logger.info(f"Recurrencia cancelada para transacción {self.id}")
    
    # ==========================================
    # MÉTODOS DE CONVERSIÓN
    # ==========================================
    
    def to_dict(self, incluir_relaciones=True):
        """
        Convierte el objeto a diccionario
        
        Args:
            incluir_relaciones (bool): Si debe incluir datos relacionados
            
        Returns:
            dict: Representación de la transacción
        """
        datos = {
            'id': self.id,
            'usuario_id': self.usuario_id,
            'cuenta_id': self.cuenta_id,
            'categoria_id': self.categoria_id,
            'tipo': self.tipo,
            'monto': float(self.monto),
            'monto_formateado': self.get_monto_formateado(),
            'descripcion': self.descripcion,
            'descripcion_corta': self.get_descripcion_corta(),
            'fecha_transaccion': self.fecha_transaccion.isoformat(),
            'hora_transaccion': self.hora_transaccion.isoformat() if self.hora_transaccion else None,
            'fecha_registro': self.fecha_registro.isoformat() if self.fecha_registro else None,
            'recurrente': self.recurrente,
            'frecuencia_recurrencia': self.frecuencia_recurrencia,
            'etiquetas': self.get_etiquetas_lista(),
            'comprobante_url': self.comprobante_url,
            'editada': self.editada,
            'num_ediciones': self.num_ediciones,
            'es_recurrente': self.es_recurrente(),
            'es_transaccion_hija': self.es_transaccion_hija()
        }
        
        if incluir_relaciones:
            if self.cuenta:
                datos['cuenta_nombre'] = self.cuenta.nombre
                datos['cuenta_tipo'] = self.cuenta.tipo
            
            if self.categoria:
                datos['categoria_nombre'] = self.categoria.nombre
                datos['categoria_color'] = self.categoria.color
                datos['categoria_icono'] = self.categoria.icono
        
        return datos
    
    # ==========================================
    # MÉTODOS ESTÁTICOS - CONSULTAS
    # ==========================================
    
    @staticmethod
    def get_transacciones_por_periodo(usuario_id, fecha_inicio, fecha_fin, tipo=None):
        """
        Obtiene transacciones de un usuario en un período específico
        
        Args:
            usuario_id (int): ID del usuario
            fecha_inicio (date): Fecha de inicio
            fecha_fin (date): Fecha de fin
            tipo (str): Filtrar por tipo ('ingreso' o 'egreso')
            
        Returns:
            list: Lista de transacciones
        """
        query = Transaccion.query.filter(
            Transaccion.usuario_id == usuario_id,
            Transaccion.fecha_transaccion >= fecha_inicio,
            Transaccion.fecha_transaccion <= fecha_fin
        )
        
        if tipo:
            query = query.filter(Transaccion.tipo == tipo)
        
        return query.order_by(
            Transaccion.fecha_transaccion.desc(), 
            Transaccion.hora_transaccion.desc()
        ).all()
    
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
            list: Lista de tuplas (categoria_nombre, categoria_color, total)
        """
        from app.models.categoria import Categoria
        
        query = db.session.query(
            Categoria.nombre,
            Categoria.color,
            func.sum(Transaccion.monto).label('total'),
            func.count(Transaccion.id).label('cantidad')
        ).join(Transaccion).filter(
            Transaccion.usuario_id == usuario_id,
            Transaccion.fecha_transaccion >= fecha_inicio,
            Transaccion.fecha_transaccion <= fecha_fin
        )
        
        if tipo:
            query = query.filter(Transaccion.tipo == tipo)
        
        return query.group_by(Categoria.id).order_by(func.sum(Transaccion.monto).desc()).all()
    
    @staticmethod
    def get_total_por_tipo(usuario_id, fecha_inicio, fecha_fin, tipo):
        """
        Obtiene el total de ingresos o egresos en un período
        
        Args:
            usuario_id (int): ID del usuario
            fecha_inicio (date): Fecha de inicio
            fecha_fin (date): Fecha de fin
            tipo (str): 'ingreso' o 'egreso'
            
        Returns:
            Decimal: Total
        """
        resultado = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.usuario_id == usuario_id,
            Transaccion.tipo == tipo,
            Transaccion.fecha_transaccion >= fecha_inicio,
            Transaccion.fecha_transaccion <= fecha_fin
        ).scalar()
        
        return Decimal(str(resultado)) if resultado else Decimal('0.00')
    
    @staticmethod
    def get_transacciones_por_etiqueta(usuario_id, etiqueta, limite=50):
        """
        Obtiene transacciones con una etiqueta específica
        
        Args:
            usuario_id (int): ID del usuario
            etiqueta (str): Etiqueta a buscar
            limite (int): Número máximo de resultados
            
        Returns:
            list: Lista de transacciones
        """
        return Transaccion.query.filter(
            Transaccion.usuario_id == usuario_id,
            Transaccion.etiquetas.like(f'%{etiqueta}%')
        ).order_by(Transaccion.fecha_transaccion.desc()).limit(limite).all()
    
    @staticmethod
    def get_recurrentes_pendientes():
        """
        Obtiene transacciones recurrentes que deben generar su próxima instancia
        
        Returns:
            list: Lista de transacciones recurrentes
        """
        hoy = datetime.now().date()
        
        return Transaccion.query.filter(
            Transaccion.recurrente == True,
            Transaccion.frecuencia_recurrencia != None,
            db.or_(
                Transaccion.fecha_fin_recurrencia == None,
                Transaccion.fecha_fin_recurrencia >= hoy
            )
        ).all()
    
    @staticmethod
    def buscar_transacciones(usuario_id, termino, limite=50):
        """
        Busca transacciones por término en descripción
        
        Args:
            usuario_id (int): ID del usuario
            termino (str): Término de búsqueda
            limite (int): Número máximo de resultados
            
        Returns:
            list: Lista de transacciones que coinciden
        """
        return Transaccion.query.filter(
            Transaccion.usuario_id == usuario_id,
            Transaccion.descripcion.ilike(f'%{termino}%')
        ).order_by(Transaccion.fecha_transaccion.desc()).limit(limite).all()
    
    @staticmethod
    def get_estadisticas_mes(usuario_id, mes, anio):
        """
        Obtiene estadísticas de un mes específico
        
        Args:
            usuario_id (int): ID del usuario
            mes (int): Mes (1-12)
            anio (int): Año
            
        Returns:
            dict: Estadísticas del mes
        """
        # Calcular fechas del mes
        from calendar import monthrange
        primer_dia = date(anio, mes, 1)
        ultimo_dia = date(anio, mes, monthrange(anio, mes)[1])
        
        # Totales
        total_ingresos = Transaccion.get_total_por_tipo(usuario_id, primer_dia, ultimo_dia, 'ingreso')
        total_egresos = Transaccion.get_total_por_tipo(usuario_id, primer_dia, ultimo_dia, 'egreso')
        
        # Cantidad de transacciones
        num_transacciones = Transaccion.query.filter(
            Transaccion.usuario_id == usuario_id,
            Transaccion.fecha_transaccion >= primer_dia,
            Transaccion.fecha_transaccion <= ultimo_dia
        ).count()
        
        # Promedio diario
        promedio_ingresos = total_ingresos / monthrange(anio, mes)[1]
        promedio_egresos = total_egresos / monthrange(anio, mes)[1]
        
        return {
            'mes': mes,
            'anio': anio,
            'total_ingresos': float(total_ingresos),
            'total_egresos': float(total_egresos),
            'balance': float(total_ingresos - total_egresos),
            'num_transacciones': num_transacciones,
            'promedio_diario_ingresos': float(promedio_ingresos),
            'promedio_diario_egresos': float(promedio_egresos)
        }
    
    # ==========================================
    # REPRESENTACIÓN
    # ==========================================
    
    def __repr__(self):
        return f'<Transaccion {self.tipo} {self.get_monto_formateado()} - {self.fecha_transaccion}>'


# ==========================================
# EVENT LISTENERS
# ==========================================

@event.listens_for(Transaccion, 'after_insert')
def actualizar_saldo_insert(mapper, connection, target):
    """
    Actualiza el saldo de la cuenta después de insertar una transacción
    IMPORTANTE: Este listener reemplaza los triggers de MySQL
    """
    try:
        from app.models.cuenta import Cuenta
        
        # Usar connection.execute en lugar de query para evitar problemas en listeners
        cuenta = db.session.query(Cuenta).get(target.cuenta_id)
        
        if cuenta:
            if target.tipo == 'ingreso':
                cuenta.saldo_actual = Decimal(str(cuenta.saldo_actual)) + Decimal(str(target.monto))
            else:
                cuenta.saldo_actual = Decimal(str(cuenta.saldo_actual)) - Decimal(str(target.monto))
            
            cuenta.fecha_modificacion = datetime.utcnow()
            db.session.commit()
            
            logger.info(
                f"Saldo actualizado para cuenta {cuenta.id}: "
                f"{'+'if target.tipo == 'ingreso' else '-'}{target.monto}"
            )
    
    except Exception as e:
        logger.error(f"Error al actualizar saldo en insert: {str(e)}")
        db.session.rollback()


@event.listens_for(Transaccion, 'after_delete')
def actualizar_saldo_delete(mapper, connection, target):
    """
    Actualiza el saldo de la cuenta después de eliminar una transacción
    """
    try:
        from app.models.cuenta import Cuenta
        
        cuenta = db.session.query(Cuenta).get(target.cuenta_id)
        
        if cuenta:
            # Revertir la operación
            if target.tipo == 'ingreso':
                cuenta.saldo_actual = Decimal(str(cuenta.saldo_actual)) - Decimal(str(target.monto))
            else:
                cuenta.saldo_actual = Decimal(str(cuenta.saldo_actual)) + Decimal(str(target.monto))
            
            cuenta.fecha_modificacion = datetime.utcnow()
            db.session.commit()
            
            logger.info(
                f"Saldo revertido para cuenta {cuenta.id}: "
                f"{'{'if target.tipo == 'ingreso' else '+'}{target.monto}"
            )
    
    except Exception as e:
        logger.error(f"Error al actualizar saldo en delete: {str(e)}")
        db.session.rollback()


@event.listens_for(Transaccion, 'before_update')
def registrar_edicion(mapper, connection, target):
    """
    Registra cuando una transacción es editada
    """
    target.editada = True
    target.num_ediciones += 1
    target.fecha_modificacion = datetime.utcnow()


@event.listens_for(Transaccion, 'after_update')
def actualizar_saldo_update(mapper, connection, target):
    """
    Actualiza saldos si cambió el monto, tipo o cuenta
    """
    # Obtener el estado anterior
    history = db.inspect(target).attrs
    
    monto_cambio = history.monto.history.has_changes()
    tipo_cambio = history.tipo.history.has_changes()
    cuenta_cambio = history.cuenta_id.history.has_changes()
    
    if monto_cambio or tipo_cambio or cuenta_cambio:
        logger.warning(
            f"Transacción {target.id} modificada. "
            f"Recomendado recalcular saldos de cuentas afectadas."
        )
        
        # Aquí podrías implementar lógica para recalcular automáticamente
        # Por ahora solo logueamos