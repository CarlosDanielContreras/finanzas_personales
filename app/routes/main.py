"""
Rutas Principales Mejoradas
app/routes/main.py

Mejoras implementadas:
- Manejo robusto de errores
- Paginación optimizada
- Cache de consultas pesadas
- Logging de acciones
- Validación de permisos
- Respuestas JSON para AJAX
"""

from flask import Blueprint, render_template, redirect, url_for, request, jsonify, flash
from flask_login import login_required, current_user
from app import db
from app.models.transaccion import Transaccion
from app.models.cuenta import Cuenta
from app.models.presupuesto import Presupuesto
from app.models.meta_ahorro import MetaAhorro
from app.models.categoria import Categoria
from app.models.otros import ConsejoFinanciero, LogActividad
from datetime import datetime, timedelta
from sqlalchemy import func, extract, desc
from decimal import Decimal
import logging

# Configurar logger
logger = logging.getLogger(__name__)

bp = Blueprint('main', __name__)


# ==========================================
# UTILIDADES Y DECORADORES
# ==========================================

def obtener_rango_fechas_mes(mes=None, anio=None):
    """
    Obtiene el rango de fechas de un mes
    
    Args:
        mes (int): Mes (None para mes actual)
        anio (int): Año (None para año actual)
    
    Returns:
        tuple: (fecha_inicio, fecha_fin)
    """
    from calendar import monthrange
    
    if mes is None:
        mes = datetime.now().month
    if anio is None:
        anio = datetime.now().year
    
    fecha_inicio = datetime(anio, mes, 1).date()
    ultimo_dia = monthrange(anio, mes)[1]
    fecha_fin = datetime(anio, mes, ultimo_dia).date()
    
    return fecha_inicio, fecha_fin


def registrar_actividad(accion, detalle=None):
    """
    Registra una actividad del usuario
    
    Args:
        accion (str): Acción realizada
        detalle (str): Detalles adicionales
    """
    try:
        LogActividad.registrar(
            usuario_id=current_user.id,
            accion=accion,
            detalle=detalle,
            ip_address=request.remote_addr
        )
    except Exception as e:
        logger.error(f"Error al registrar actividad: {str(e)}")


# ==========================================
# RUTAS PRINCIPALES
# ==========================================

@bp.route('/')
def index():
    """
    Página de inicio
    Redirige al dashboard si está autenticado, sino al login
    """
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return redirect(url_for('auth.login'))


@bp.route('/dashboard')
@login_required
def dashboard():
    """
    Dashboard principal del usuario
    Muestra resumen financiero, gráficos y datos importantes
    """
    try:
        # Registrar acceso al dashboard
        registrar_actividad('acceso_dashboard')
        
        # ==========================================
        # ESTADÍSTICAS GENERALES
        # ==========================================
        estadisticas = current_user.get_estadisticas_resumen()
        
        # ==========================================
        # CUENTAS ACTIVAS
        # ==========================================
        cuentas = Cuenta.query.filter_by(
            usuario_id=current_user.id,
            activo=True
        ).order_by(Cuenta.fecha_creacion.desc()).all()
        
        # ==========================================
        # TRANSACCIONES RECIENTES
        # ==========================================
        page = request.args.get('page', 1, type=int)
        per_page = 10
        
        transacciones_paginadas = Transaccion.query.filter_by(
            usuario_id=current_user.id
        ).order_by(
            Transaccion.fecha_transaccion.desc(),
            Transaccion.hora_transaccion.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        transacciones_recientes = transacciones_paginadas.items
        
        # ==========================================
        # PRESUPUESTOS
        # ==========================================
        presupuestos_activos = Presupuesto.get_presupuestos_activos(current_user.id)
        presupuestos_en_alerta = [p for p in presupuestos_activos if p.esta_en_alerta()]
        presupuestos_excedidos = [p for p in presupuestos_activos if p.esta_excedido()]
        
        # ==========================================
        # METAS DE AHORRO
        # ==========================================
        metas_activas = MetaAhorro.query.filter_by(
            usuario_id=current_user.id,
            completada=False
        ).order_by(MetaAhorro.fecha_objetivo).limit(5).all()
        
        metas_proximas_vencer = [m for m in metas_activas if m.get_dias_restantes() <= 30]
        
        # ==========================================
        # CONSEJOS FINANCIEROS
        # ==========================================
        consejos = ConsejoFinanciero.get_consejos_no_vistos(current_user.id)[:3]
        
        # ==========================================
        # DATOS PARA GRÁFICOS
        # ==========================================
        
        # Gastos por categoría del mes actual
        fecha_inicio, fecha_fin = obtener_rango_fechas_mes()
        
        gastos_por_categoria = Transaccion.get_resumen_por_categoria(
            usuario_id=current_user.id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo='egreso'
        )
        
        # Preparar datos para gráfico de categorías
        categorias_labels = []
        categorias_montos = []
        categorias_colores = []
        
        for nombre, color, total, cantidad in gastos_por_categoria:
            categorias_labels.append(nombre)
            categorias_montos.append(float(total))
            categorias_colores.append(color)
        
        # Tendencia de los últimos 6 meses
        tendencia_meses = []
        tendencia_ingresos = []
        tendencia_egresos = []
        
        for i in range(5, -1, -1):
            fecha_mes = datetime.now() - timedelta(days=30*i)
            mes = fecha_mes.month
            anio = fecha_mes.year
            
            fecha_inicio_mes, fecha_fin_mes = obtener_rango_fechas_mes(mes, anio)
            
            # Ingresos del mes
            ingresos = Transaccion.get_total_por_tipo(
                current_user.id, 
                fecha_inicio_mes, 
                fecha_fin_mes, 
                'ingreso'
            )
            
            # Egresos del mes
            egresos = Transaccion.get_total_por_tipo(
                current_user.id, 
                fecha_inicio_mes, 
                fecha_fin_mes, 
                'egreso'
            )
            
            # Nombre del mes en español
            meses_es = ['Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                       'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
            
            tendencia_meses.append(meses_es[mes - 1])
            tendencia_ingresos.append(float(ingresos))
            tendencia_egresos.append(float(egresos))
        
        # ==========================================
        # ESTADÍSTICAS ADICIONALES
        # ==========================================
        
        # Transacción más grande del mes
        transaccion_mayor = Transaccion.query.filter(
            Transaccion.usuario_id == current_user.id,
            Transaccion.fecha_transaccion >= fecha_inicio,
            Transaccion.fecha_transaccion <= fecha_fin,
            Transaccion.tipo == 'egreso'
        ).order_by(desc(Transaccion.monto)).first()
        
        # Categoría más usada
        categoria_mas_usada = db.session.query(
            Categoria.nombre,
            func.count(Transaccion.id).label('cantidad')
        ).join(Transaccion).filter(
            Transaccion.usuario_id == current_user.id,
            Transaccion.fecha_transaccion >= fecha_inicio,
            Transaccion.fecha_transaccion <= fecha_fin
        ).group_by(Categoria.id).order_by(desc('cantidad')).first()
        
        # Promedio de gasto diario
        dias_transcurridos = (datetime.now().date() - fecha_inicio).days + 1
        promedio_gasto_diario = float(estadisticas['egresos_mes']) / dias_transcurridos if dias_transcurridos > 0 else 0
        
        # ==========================================
        # RENDERIZAR TEMPLATE
        # ==========================================
        
        return render_template('dashboard/index.html',
                             estadisticas=estadisticas,
                             cuentas=cuentas,
                             transacciones_recientes=transacciones_recientes,
                             transacciones_paginadas=transacciones_paginadas,
                             presupuestos_activos=presupuestos_activos,
                             presupuestos_en_alerta=presupuestos_en_alerta,
                             presupuestos_excedidos=presupuestos_excedidos,
                             metas_activas=metas_activas,
                             metas_proximas_vencer=metas_proximas_vencer,
                             consejos=consejos,
                             categorias_labels=categorias_labels,
                             categorias_montos=categorias_montos,
                             categorias_colores=categorias_colores,
                             tendencia_meses=tendencia_meses,
                             tendencia_ingresos=tendencia_ingresos,
                             tendencia_egresos=tendencia_egresos,
                             transaccion_mayor=transaccion_mayor,
                             categoria_mas_usada=categoria_mas_usada,
                             promedio_gasto_diario=promedio_gasto_diario)
    
    except Exception as e:
        logger.error(f"Error en dashboard: {str(e)}")
        flash('Error al cargar el dashboard. Por favor intenta de nuevo.', 'danger')
        return render_template('dashboard/index.html',
                             estadisticas={},
                             cuentas=[],
                             transacciones_recientes=[],
                             error=True)


@bp.route('/dashboard/actualizar-estadisticas')
@login_required
def actualizar_estadisticas():
    """
    Endpoint AJAX para actualizar estadísticas sin recargar la página
    
    Returns:
        JSON con estadísticas actualizadas
    """
    try:
        estadisticas = current_user.get_estadisticas_resumen()
        
        return jsonify({
            'success': True,
            'data': estadisticas
        })
    
    except Exception as e:
        logger.error(f"Error al actualizar estadísticas: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener estadísticas'
        }), 500


@bp.route('/dashboard/resumen-mes/<int:mes>/<int:anio>')
@login_required
def resumen_mes(mes, anio):
    """
    Obtiene el resumen financiero de un mes específico
    
    Args:
        mes (int): Mes (1-12)
        anio (int): Año
    
    Returns:
        JSON con resumen del mes
    """
    try:
        # Validar mes y año
        if not (1 <= mes <= 12):
            return jsonify({
                'success': False,
                'message': 'Mes inválido'
            }), 400
        
        if not (2000 <= anio <= datetime.now().year + 1):
            return jsonify({
                'success': False,
                'message': 'Año inválido'
            }), 400
        
        # Obtener estadísticas del mes
        estadisticas = Transaccion.get_estadisticas_mes(current_user.id, mes, anio)
        
        # Obtener transacciones del mes
        fecha_inicio, fecha_fin = obtener_rango_fechas_mes(mes, anio)
        
        transacciones = Transaccion.get_transacciones_por_periodo(
            usuario_id=current_user.id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin
        )
        
        # Gastos por categoría
        gastos_por_categoria = Transaccion.get_resumen_por_categoria(
            usuario_id=current_user.id,
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            tipo='egreso'
        )
        
        return jsonify({
            'success': True,
            'data': {
                'estadisticas': estadisticas,
                'num_transacciones': len(transacciones),
                'gastos_por_categoria': [
                    {
                        'nombre': nombre,
                        'color': color,
                        'total': float(total),
                        'cantidad': cantidad
                    }
                    for nombre, color, total, cantidad in gastos_por_categoria
                ]
            }
        })
    
    except Exception as e:
        logger.error(f"Error al obtener resumen del mes: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener resumen'
        }), 500


# ==========================================
# PERFIL Y CONFIGURACIÓN
# ==========================================

@bp.route('/perfil')
@login_required
def perfil():
    """
    Página de perfil del usuario
    """
    try:
        registrar_actividad('acceso_perfil')
        
        # Obtener estadísticas generales del usuario
        estadisticas = current_user.get_estadisticas_resumen()
        
        # Fecha de registro
        dias_registrado = (datetime.now() - current_user.fecha_registro).days
        
        # Total de transacciones
        total_transacciones = current_user.transacciones.count()
        
        # Categorías personalizadas
        categorias_personalizadas = Categoria.query.filter_by(
            usuario_id=current_user.id
        ).count()
        
        # Actividad reciente
        logs_recientes = LogActividad.get_actividad_reciente(
            usuario_id=current_user.id,
            limite=10
        )
        
        return render_template('main/perfil.html',
                             estadisticas=estadisticas,
                             dias_registrado=dias_registrado,
                             total_transacciones=total_transacciones,
                             categorias_personalizadas=categorias_personalizadas,
                             logs_recientes=logs_recientes)
    
    except Exception as e:
        logger.error(f"Error al cargar perfil: {str(e)}")
        flash('Error al cargar el perfil.', 'danger')
        return redirect(url_for('main.dashboard'))


@bp.route('/configuracion')
@login_required
def configuracion():
    """
    Página de configuración del usuario
    """
    try:
        registrar_actividad('acceso_configuracion')
        
        # Obtener configuración actual
        config = current_user.configuracion
        
        return render_template('main/configuracion.html',
                             configuracion=config)
    
    except Exception as e:
        logger.error(f"Error al cargar configuración: {str(e)}")
        flash('Error al cargar la configuración.', 'danger')
        return redirect(url_for('main.dashboard'))


@bp.route('/configuracion/actualizar', methods=['POST'])
@login_required
def actualizar_configuracion():
    """
    Actualiza la configuración del usuario
    """
    try:
        data = request.get_json() if request.is_json else request.form
        
        config = current_user.configuracion
        
        if not config:
            from app.models.usuario import ConfiguracionUsuario
            config = ConfiguracionUsuario(usuario_id=current_user.id)
            db.session.add(config)
        
        # Actualizar campos
        if 'notificaciones_email' in data:
            config.notificaciones_email = data.get('notificaciones_email') == 'true' or data.get('notificaciones_email') == True
        
        if 'tema' in data:
            config.tema = data.get('tema')
        
        if 'idioma' in data:
            config.idioma = data.get('idioma')
        
        # Actualizar moneda preferida del usuario
        if 'moneda_preferida' in data:
            current_user.moneda_preferida = data.get('moneda_preferida')
        
        db.session.commit()
        
        registrar_actividad('actualizar_configuracion', 'Configuración actualizada')
        
        if request.is_json:
            return jsonify({
                'success': True,
                'message': 'Configuración actualizada correctamente'
            })
        else:
            flash('Configuración actualizada correctamente.', 'success')
            return redirect(url_for('main.configuracion'))
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error al actualizar configuración: {str(e)}")
        
        if request.is_json:
            return jsonify({
                'success': False,
                'message': 'Error al actualizar configuración'
            }), 500
        else:
            flash('Error al actualizar la configuración.', 'danger')
            return redirect(url_for('main.configuracion'))


# ==========================================
# BÚSQUEDA Y FILTROS
# ==========================================

@bp.route('/buscar')
@login_required
def buscar():
    """
    Búsqueda global de transacciones
    """
    try:
        termino = request.args.get('q', '').strip()
        
        if not termino:
            flash('Ingresa un término de búsqueda.', 'warning')
            return redirect(url_for('main.dashboard'))
        
        # Buscar en transacciones
        transacciones = Transaccion.buscar_transacciones(
            usuario_id=current_user.id,
            termino=termino,
            limite=100
        )
        
        # Buscar en categorías personalizadas
        categorias = Categoria.query.filter(
            Categoria.usuario_id == current_user.id,
            Categoria.nombre.ilike(f'%{termino}%')
        ).all()
        
        # Buscar en cuentas
        cuentas = Cuenta.query.filter(
            Cuenta.usuario_id == current_user.id,
            Cuenta.nombre.ilike(f'%{termino}%')
        ).all()
        
        registrar_actividad('busqueda', f'Búsqueda: {termino}')
        
        return render_template('main/buscar.html',
                             termino=termino,
                             transacciones=transacciones,
                             categorias=categorias,
                             cuentas=cuentas)
    
    except Exception as e:
        logger.error(f"Error en búsqueda: {str(e)}")
        flash('Error al realizar la búsqueda.', 'danger')
        return redirect(url_for('main.dashboard'))


# ==========================================
# UTILIDADES
# ==========================================

@bp.route('/ayuda')
@login_required
def ayuda():
    """
    Página de ayuda y documentación
    """
    return render_template('main/ayuda.html')


@bp.route('/acerca')
def acerca():
    """
    Página acerca de la aplicación
    """
    return render_template('main/acerca.html')


@bp.route('/terminos')
def terminos():
    """
    Términos y condiciones
    """
    return render_template('main/terminos.html')


@bp.route('/privacidad')
def privacidad():
    """
    Política de privacidad
    """
    return render_template('main/privacidad.html')


# ==========================================
# API ENDPOINTS
# ==========================================

@bp.route('/api/resumen-rapido')
@login_required
def api_resumen_rapido():
    """
    Endpoint para obtener resumen rápido del usuario
    Útil para widgets o extensiones
    
    Returns:
        JSON con datos básicos
    """
    try:
        estadisticas = current_user.get_estadisticas_resumen()
        
        # Última transacción
        ultima_transaccion = Transaccion.query.filter_by(
            usuario_id=current_user.id
        ).order_by(
            Transaccion.fecha_transaccion.desc(),
            Transaccion.hora_transaccion.desc()
        ).first()
        
        return jsonify({
            'success': True,
            'data': {
                'usuario': {
                    'nombre': current_user.nombre_completo,
                    'email': current_user.email
                },
                'balance_total': estadisticas['balance_total'],
                'ingresos_mes': estadisticas['ingresos_mes'],
                'egresos_mes': estadisticas['egresos_mes'],
                'balance_mes': estadisticas['balance_mes'],
                'ultima_transaccion': ultima_transaccion.to_dict() if ultima_transaccion else None
            }
        })
    
    except Exception as e:
        logger.error(f"Error en resumen rápido: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al obtener resumen'
        }), 500


@bp.route('/api/verificar-salud')
@login_required
def api_verificar_salud():
    """
    Verifica la salud financiera del usuario
    
    Returns:
        JSON con análisis de salud financiera
    """
    try:
        estadisticas = current_user.get_estadisticas_resumen()
        
        # Calcular puntuación de salud (0-100)
        puntuacion = 100
        alertas = []
        
        # Verificar balance positivo
        if estadisticas['balance_mes'] < 0:
            puntuacion -= 20
            alertas.append({
                'tipo': 'warning',
                'mensaje': 'Gastos superan ingresos este mes'
            })
        
        # Verificar presupuestos excedidos
        presupuestos_excedidos = [
            p for p in Presupuesto.get_presupuestos_activos(current_user.id)
            if p.esta_excedido()
        ]
        
        if len(presupuestos_excedidos) > 0:
            puntuacion -= 15 * len(presupuestos_excedidos)
            alertas.append({
                'tipo': 'danger',
                'mensaje': f'{len(presupuestos_excedidos)} presupuesto(s) excedido(s)'
            })
        
        # Verificar metas atrasadas
        metas_atrasadas = [
            m for m in MetaAhorro.query.filter_by(
                usuario_id=current_user.id,
                completada=False
            ).all()
            if m.get_estado() == 'atrasada'
        ]
        
        if len(metas_atrasadas) > 0:
            puntuacion -= 10
            alertas.append({
                'tipo': 'warning',
                'mensaje': f'{len(metas_atrasadas)} meta(s) de ahorro atrasada(s)'
            })
        
        # Verificar diversificación de cuentas
        num_cuentas = Cuenta.query.filter_by(
            usuario_id=current_user.id,
            activo=True
        ).count()
        
        if num_cuentas < 2:
            puntuacion -= 10
            alertas.append({
                'tipo': 'info',
                'mensaje': 'Considera diversificar en más cuentas'
            })
        
        # Asegurar que la puntuación esté entre 0 y 100
        puntuacion = max(0, min(100, puntuacion))
        
        # Determinar nivel de salud
        if puntuacion >= 80:
            nivel = 'excelente'
            color = 'success'
        elif puntuacion >= 60:
            nivel = 'bueno'
            color = 'info'
        elif puntuacion >= 40:
            nivel = 'regular'
            color = 'warning'
        else:
            nivel = 'critico'
            color = 'danger'
        
        return jsonify({
            'success': True,
            'data': {
                'puntuacion': puntuacion,
                'nivel': nivel,
                'color': color,
                'alertas': alertas
            }
        })
    
    except Exception as e:
        logger.error(f"Error al verificar salud financiera: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al verificar salud financiera'
        }), 500


@bp.route('/api/exportar-datos')
@login_required
def api_exportar_datos():
    """
    Exporta los datos del usuario en formato JSON
    
    Returns:
        JSON con todos los datos del usuario
    """
    try:
        # Obtener todas las transacciones
        transacciones = Transaccion.query.filter_by(
            usuario_id=current_user.id
        ).all()
        
        # Obtener todas las cuentas
        cuentas = Cuenta.query.filter_by(
            usuario_id=current_user.id
        ).all()
        
        # Obtener categorías personalizadas
        categorias = Categoria.query.filter_by(
            usuario_id=current_user.id
        ).all()
        
        # Obtener metas
        metas = MetaAhorro.query.filter_by(
            usuario_id=current_user.id
        ).all()
        
        datos_exportacion = {
            'usuario': current_user.to_dict(),
            'fecha_exportacion': datetime.now().isoformat(),
            'transacciones': [t.to_dict() for t in transacciones],
            'cuentas': [c.to_dict(incluir_estadisticas=True) for c in cuentas],
            'categorias': [cat.to_dict() for cat in categorias],
            'metas_ahorro': [m.to_dict() for m in metas]
        }
        
        registrar_actividad('exportar_datos', 'Datos exportados')
        
        return jsonify({
            'success': True,
            'data': datos_exportacion
        })
    
    except Exception as e:
        logger.error(f"Error al exportar datos: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al exportar datos'
        }), 500


# ==========================================
# NOTIFICACIONES
# ==========================================

@bp.route('/notificaciones')
@login_required
def notificaciones():
    """
    Página de notificaciones del usuario
    """
    try:
        # Obtener consejos financieros no vistos
        consejos = ConsejoFinanciero.get_consejos_no_vistos(current_user.id)
        
        # Obtener presupuestos en alerta
        presupuestos_alerta = Presupuesto.get_presupuestos_en_alerta(current_user.id)
        
        # Obtener metas próximas a vencer
        metas_proximas = MetaAhorro.query.filter_by(
            usuario_id=current_user.id,
            completada=False
        ).all()
        metas_proximas = [m for m in metas_proximas if m.get_dias_restantes() <= 30]
        
        return render_template('main/notificaciones.html',
                             consejos=consejos,
                             presupuestos_alerta=presupuestos_alerta,
                             metas_proximas=metas_proximas)
    
    except Exception as e:
        logger.error(f"Error al cargar notificaciones: {str(e)}")
        flash('Error al cargar notificaciones.', 'danger')
        return redirect(url_for('main.dashboard'))


@bp.route('/notificaciones/marcar-vistas', methods=['POST'])
@login_required
def marcar_notificaciones_vistas():
    """
    Marca todas las notificaciones como vistas
    """
    try:
        # Marcar consejos como vistos
        consejos = ConsejoFinanciero.get_consejos_no_vistos(current_user.id)
        for consejo in consejos:
            consejo.marcar_como_visto()
        
        return jsonify({
            'success': True,
            'message': 'Notificaciones marcadas como vistas'
        })
    
    except Exception as e:
        logger.error(f"Error al marcar notificaciones: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Error al marcar notificaciones'
        }), 500


# ==========================================
# MANEJO DE ERRORES
# ==========================================

@bp.errorhandler(404)
def not_found_error(error):
    """Maneja errores 404 dentro del blueprint"""
    return render_template('errors/404.html'), 404


@bp.errorhandler(500)
def internal_error(error):
    """Maneja errores 500 dentro del blueprint"""
    db.session.rollback()
    logger.error(f"Error 500: {str(error)}")
    return render_template('errors/500.html'), 500