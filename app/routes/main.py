"""
Rutas Principales
app/routes/main.py
"""

from flask import Blueprint, render_template, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.transaccion import Transaccion
from app.models.cuenta import Cuenta
from app.models.presupuesto import Presupuesto
from app.models.meta_ahorro import MetaAhorro
from app.models.otros import ConsejoFinanciero
from datetime import datetime, timedelta
from sqlalchemy import func, extract

bp = Blueprint('main', __name__)

@bp.route('/')
def index():
    """Página de inicio"""
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """Dashboard principal del usuario"""
    
    # Obtener estadísticas del usuario
    estadisticas = current_user.get_estadisticas_resumen()
    
    # Obtener cuentas activas
    cuentas = Cuenta.query.filter_by(
        usuario_id=current_user.id,
        activo=True
    ).all()
    
    # Obtener transacciones recientes (últimas 10)
    transacciones_recientes = Transaccion.query.filter_by(
        usuario_id=current_user.id
    ).order_by(
        Transaccion.fecha_transaccion.desc(),
        Transaccion.hora_transaccion.desc()
    ).limit(10).all()
    
    # Obtener presupuestos activos
    presupuestos_activos = Presupuesto.get_presupuestos_activos(current_user.id)
    presupuestos_en_alerta = [p for p in presupuestos_activos if p.esta_en_alerta()]
    
    # Obtener metas activas
    metas_activas = MetaAhorro.query.filter_by(
        usuario_id=current_user.id,
        completada=False
    ).order_by(MetaAhorro.fecha_objetivo).limit(5).all()
    
    # Obtener consejos no vistos
    consejos = ConsejoFinanciero.get_consejos_no_vistos(current_user.id)[:3]
    
    # Gastos por categoría del mes actual
    mes_actual = datetime.now().month
    anio_actual = datetime.now().year
    
    gastos_por_categoria = Transaccion.get_resumen_por_categoria(
        usuario_id=current_user.id,
        fecha_inicio=datetime(anio_actual, mes_actual, 1).date(),
        fecha_fin=datetime.now().date(),
        tipo='egreso'
    )
    
    # Preparar datos para gráfico de gastos
    categorias_labels = [cat[0] for cat in gastos_por_categoria]
    categorias_montos = [float(cat[2]) for cat in gastos_por_categoria]
    categorias_colores = [cat[1] for cat in gastos_por_categoria]
    
    # Tendencia de los últimos 6 meses
    tendencia_meses = []
    tendencia_ingresos = []
    tendencia_egresos = []
    
    for i in range(5, -1, -1):
        fecha_mes = datetime.now() - timedelta(days=30*i)
        mes = fecha_mes.month
        anio = fecha_mes.year
        
        # Ingresos del mes
        ingresos = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.usuario_id == current_user.id,
            Transaccion.tipo == 'ingreso',
            extract('month', Transaccion.fecha_transaccion) == mes,
            extract('year', Transaccion.fecha_transaccion) == anio
        ).scalar() or 0
        
        # Egresos del mes
        egresos = db.session.query(func.sum(Transaccion.monto)).filter(
            Transaccion.usuario_id == current_user.id,
            Transaccion.tipo == 'egreso',
            extract('month', Transaccion.fecha_transaccion) == mes,
            extract('year', Transaccion.fecha_transaccion) == anio
        ).scalar() or 0
        
        tendencia_meses.append(fecha_mes.strftime('%b'))
        tendencia_ingresos.append(float(ingresos))
        tendencia_egresos.append(float(egresos))
    
    return render_template('dashboard/index.html',
                         estadisticas=estadisticas,
                         cuentas=cuentas,
                         transacciones_recientes=transacciones_recientes,
                         presupuestos_activos=presupuestos_activos,
                         presupuestos_en_alerta=presupuestos_en_alerta,
                         metas_activas=metas_activas,
                         consejos=consejos,
                         categorias_labels=categorias_labels,
                         categorias_montos=categorias_montos,
                         categorias_colores=categorias_colores,
                         tendencia_meses=tendencia_meses,
                         tendencia_ingresos=tendencia_ingresos,
                         tendencia_egresos=tendencia_egresos)


@bp.route('/ayuda')
@login_required
def ayuda():
    """Página de ayuda"""
    return render_template('main/ayuda.html')


@bp.route('/acerca')
def acerca():
    """Página acerca de"""
    return render_template('main/acerca.html')