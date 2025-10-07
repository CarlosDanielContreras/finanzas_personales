"""
Inicialización del paquete de modelos
app/models/__init__.py
"""

from app.models.usuario import Usuario, ConfiguracionUsuario
from app.models.categoria import Categoria
from app.models.cuenta import Cuenta
from app.models.transaccion import Transaccion
from app.models.presupuesto import Presupuesto
from app.models.meta_ahorro import MetaAhorro, AporteMeta
from app.models.otros import ConsejoFinanciero, Sesion, LogActividad, EstadisticaApp

__all__ = [
    'Usuario',
    'ConfiguracionUsuario',
    'Categoria',
    'Cuenta',
    'Transaccion',
    'Presupuesto',
    'MetaAhorro',
    'AporteMeta',
    'ConsejoFinanciero',
    'Sesion',
    'LogActividad',
    'EstadisticaApp'
]