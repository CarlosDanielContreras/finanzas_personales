"""
Filtros personalizados para Jinja2
app/utils/filters.py
"""

from datetime import datetime, date
import locale

def register_filters(app):
    """
    Registra todos los filtros personalizados en la aplicación Flask
    
    Args:
        app: Instancia de la aplicación Flask
    """
    
    @app.template_filter('formato_moneda')
    def formato_moneda(valor, simbolo='$'):
        """
        Formatea un número como moneda
        
        Uso en template: {{ valor|formato_moneda }}
        """
        try:
            return f'{simbolo}{float(valor):,.2f}'
        except (ValueError, TypeError):
            return f'{simbolo}0.00'
    
    @app.template_filter('formato_numero')
    def formato_numero(valor):
        """
        Formatea un número con separadores de miles
        
        Uso en template: {{ valor|formato_numero }}
        """
        try:
            return f'{float(valor):,.2f}'
        except (ValueError, TypeError):
            return '0.00'
    
    @app.template_filter('formato_fecha')
    def formato_fecha(fecha, formato='%d/%m/%Y'):
        """
        Formatea una fecha
        
        Uso en template: {{ fecha|formato_fecha }}
        """
        if not fecha:
            return ''
        
        if isinstance(fecha, str):
            try:
                fecha = datetime.fromisoformat(fecha)
            except:
                return fecha
        
        if isinstance(fecha, datetime):
            return fecha.strftime(formato)
        elif isinstance(fecha, date):
            return fecha.strftime(formato)
        
        return str(fecha)
    
    @app.template_filter('formato_fecha_hora')
    def formato_fecha_hora(fecha_hora, formato='%d/%m/%Y %H:%M'):
        """
        Formatea una fecha y hora
        
        Uso en template: {{ fecha_hora|formato_fecha_hora }}
        """
        if not fecha_hora:
            return ''
        
        if isinstance(fecha_hora, str):
            try:
                fecha_hora = datetime.fromisoformat(fecha_hora)
            except:
                return fecha_hora
        
        if isinstance(fecha_hora, datetime):
            return fecha_hora.strftime(formato)
        
        return str(fecha_hora)
    
    @app.template_filter('fecha_relativa')
    def fecha_relativa(fecha):
        """
        Convierte una fecha a formato relativo (hace 2 días, etc.)
        
        Uso en template: {{ fecha|fecha_relativa }}
        """
        if not fecha:
            return ''
        
        if isinstance(fecha, str):
            try:
                fecha = datetime.fromisoformat(fecha)
            except:
                return fecha
        
        if isinstance(fecha, date) and not isinstance(fecha, datetime):
            fecha = datetime.combine(fecha, datetime.min.time())
        
        ahora = datetime.now()
        diferencia = ahora - fecha
        
        segundos = diferencia.total_seconds()
        
        if segundos < 60:
            return 'hace un momento'
        elif segundos < 3600:
            minutos = int(segundos / 60)
            return f'hace {minutos} minuto{"s" if minutos > 1 else ""}'
        elif segundos < 86400:
            horas = int(segundos / 3600)
            return f'hace {horas} hora{"s" if horas > 1 else ""}'
        elif segundos < 604800:
            dias = int(segundos / 86400)
            return f'hace {dias} día{"s" if dias > 1 else ""}'
        elif segundos < 2592000:
            semanas = int(segundos / 604800)
            return f'hace {semanas} semana{"s" if semanas > 1 else ""}'
        elif segundos < 31536000:
            meses = int(segundos / 2592000)
            return f'hace {meses} mes{"es" if meses > 1 else ""}'
        else:
            anos = int(segundos / 31536000)
            return f'hace {anos} año{"s" if anos > 1 else ""}'
    
    @app.template_filter('porcentaje')
    def formato_porcentaje(valor, decimales=1):
        """
        Formatea un número como porcentaje
        
        Uso en template: {{ valor|porcentaje }}
        """
        try:
            return f'{float(valor):.{decimales}f}%'
        except (ValueError, TypeError):
            return '0.0%'
    
    @app.template_filter('mes_nombre')
    def mes_nombre(numero_mes):
        """
        Convierte el número de mes a nombre
        
        Uso en template: {{ 1|mes_nombre }} -> Enero
        """
        meses = {
            1: 'Enero', 2: 'Febrero', 3: 'Marzo', 4: 'Abril',
            5: 'Mayo', 6: 'Junio', 7: 'Julio', 8: 'Agosto',
            9: 'Septiembre', 10: 'Octubre', 11: 'Noviembre', 12: 'Diciembre'
        }
        return meses.get(numero_mes, '')
    
    @app.template_filter('truncar')
    def truncar_texto(texto, longitud=50, sufijo='...'):
        """
        Trunca un texto a una longitud específica
        
        Uso en template: {{ texto|truncar(30) }}
        """
        if not texto:
            return ''
        
        texto = str(texto)
        if len(texto) <= longitud:
            return texto
        
        return texto[:longitud].rsplit(' ', 1)[0] + sufijo
    
    @app.template_filter('clase_tipo_transaccion')
    def clase_tipo_transaccion(tipo):
        """
        Retorna la clase CSS según el tipo de transacción
        
        Uso en template: {{ tipo|clase_tipo_transaccion }}
        """
        return 'text-success' if tipo == 'ingreso' else 'text-danger'
    
    @app.template_filter('icono_tipo_transaccion')
    def icono_tipo_transaccion(tipo):
        """
        Retorna el icono según el tipo de transacción
        
        Uso en template: {{ tipo|icono_tipo_transaccion }}
        """
        return 'fa-arrow-up' if tipo == 'ingreso' else 'fa-arrow-down'
    
    @app.template_filter('signo_monto')
    def signo_monto(tipo):
        """
        Retorna el signo según el tipo de transacción
        
        Uso en template: {{ tipo|signo_monto }}
        """
        return '+' if tipo == 'ingreso' else '-'
    
    @app.template_filter('initials')
    def obtener_iniciales(nombre):
        """
        Obtiene las iniciales de un nombre
        
        Uso en template: {{ nombre|initials }}
        """
        if not nombre:
            return ''
        
        palabras = nombre.strip().split()
        if len(palabras) == 0:
            return ''
        elif len(palabras) == 1:
            return palabras[0][0].upper()
        else:
            return (palabras[0][0] + palabras[-1][0]).upper()
    
    @app.template_filter('estado_badge')
    def estado_badge(estado):
        """
        Retorna la clase de badge según el estado
        
        Uso en template: {{ estado|estado_badge }}
        """
        clases = {
            'completada': 'badge-success',
            'en_tiempo': 'badge-info',
            'atrasada': 'badge-warning',
            'vencida': 'badge-danger',
            'excedido': 'badge-danger',
            'alerta': 'badge-warning',
            'normal': 'badge-success',
            'inactivo': 'badge-secondary'
        }
        return clases.get(estado, 'badge-secondary')