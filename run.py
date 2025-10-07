"""
Archivo principal para ejecutar la aplicación Flask
run.py
"""

import os
from app import create_app, db

# Crear la aplicación con la configuración deseada
# Usa la variable de entorno FLASK_ENV o 'development' por defecto
config_name = os.getenv('FLASK_ENV', 'development')
app = create_app(config_name)

@app.cli.command()
def init_db():
    """Inicializa la base de datos (crear todas las tablas)"""
    db.create_all()
    print("✅ Base de datos inicializada correctamente")

@app.cli.command()
def drop_db():
    """Elimina todas las tablas de la base de datos"""
    if input("¿Estás seguro? Esto eliminará todos los datos (s/n): ").lower() == 's':
        db.drop_all()
        print("✅ Base de datos eliminada")
    else:
        print("❌ Operación cancelada")

@app.cli.command()
def seed_db():
    """Llena la base de datos con datos de prueba"""
    from app.models.usuario import Usuario
    from app.models.categoria import Categoria
    from app.models.cuenta import Cuenta
    from datetime import datetime
    
    # Verificar si ya hay datos
    if Usuario.query.first():
        print("⚠️ La base de datos ya contiene datos")
        return
    
    # Crear usuario de prueba
    usuario_test = Usuario(
        nombre_completo="Usuario Test",
        email="usuario@test.com",
        rol="usuario",
        moneda_preferida="COP"
    )
    usuario_test.set_password("Test123!")
    db.session.add(usuario_test)
    db.session.commit()
    
    # Crear cuenta de prueba
    cuenta_test = Cuenta(
        usuario_id=usuario_test.id,
        nombre="Efectivo",
        tipo="efectivo",
        saldo_inicial=100000.00,
        saldo_actual=100000.00
    )
    db.session.add(cuenta_test)
    db.session.commit()
    
    print("✅ Datos de prueba insertados:")
    print(f"   Email: usuario@test.com")
    print(f"   Contraseña: Test123!")

@app.shell_context_processor
def make_shell_context():
    """Crea un contexto para el shell interactivo de Flask"""
    from app.models.usuario import Usuario
    from app.models.categoria import Categoria
    from app.models.cuenta import Cuenta
    from app.models.transaccion import Transaccion
    from app.models.presupuesto import Presupuesto
    from app.models.meta_ahorro import MetaAhorro
    
    return {
        'db': db,
        'Usuario': Usuario,
        'Categoria': Categoria,
        'Cuenta': Cuenta,
        'Transaccion': Transaccion,
        'Presupuesto': Presupuesto,
        'MetaAhorro': MetaAhorro
    }

if __name__ == '__main__':
    # Ejecutar la aplicación
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=True
    )