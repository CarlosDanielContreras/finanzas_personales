"""
Script para Resetear Contraseña del Administrador
scripts/reset_admin_password.py

Uso:
    python scripts/reset_admin_password.py
"""

import sys
import os

# Agregar el directorio raíz al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models.usuario import Usuario

def reset_admin_password():
    """Resetea la contraseña del administrador"""
    
    print("=" * 60)
    print("🔐 RESETEAR CONTRASEÑA DEL ADMINISTRADOR")
    print("=" * 60)
    print()
    
    app = create_app('development')
    
    with app.app_context():
        # Buscar el usuario administrador
        admin = Usuario.query.filter_by(email='admin@finanzas.com').first()
        
        if not admin:
            print("❌ No se encontró el usuario administrador")
            print("   Email buscado: admin@finanzas.com")
            print()
            print("💡 Creando nuevo usuario administrador...")
            
            # Crear nuevo usuario admin
            admin = Usuario(
                nombre_completo='Administrador',
                email='admin@finanzas.com',
                rol='admin',
                moneda_preferida='COP',
                activo=True
            )
            admin.set_password('Admin123!')
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Usuario administrador creado exitosamente")
            print()
            print("📧 Email: admin@finanzas.com")
            print("🔑 Contraseña: Admin123!")
            print()
            return
        
        # Mostrar información del usuario
        print(f"✅ Usuario encontrado:")
        print(f"   ID: {admin.id}")
        print(f"   Nombre: {admin.nombre_completo}")
        print(f"   Email: {admin.email}")
        print(f"   Rol: {admin.rol}")
        print(f"   Activo: {admin.activo}")
        print()
        
        # Pedir nueva contraseña
        print("Ingresa la nueva contraseña (o presiona Enter para usar 'Admin123!'):")
        nueva_password = input("Contraseña: ").strip()
        
        if not nueva_password:
            nueva_password = 'Admin123!'
            print(f"Usando contraseña por defecto: {nueva_password}")
        
        # Cambiar la contraseña
        admin.set_password(nueva_password)
        admin.activo = True  # Asegurar que esté activo
        
        db.session.commit()
        
        print()
        print("=" * 60)
        print("✅ CONTRASEÑA ACTUALIZADA EXITOSAMENTE")
        print("=" * 60)
        print()
        print("Credenciales de acceso:")
        print(f"📧 Email: {admin.email}")
        print(f"🔑 Contraseña: {nueva_password}")
        print()
        print("⚠️  IMPORTANTE: Guarda esta contraseña en un lugar seguro")
        print()
        
        # Verificar que la contraseña funciona
        print("Verificando contraseña...")
        if admin.check_password(nueva_password):
            print("✅ Contraseña verificada correctamente")
        else:
            print("❌ Error al verificar contraseña")
        print()


def listar_usuarios():
    """Lista todos los usuarios del sistema"""
    
    app = create_app('development')
    
    with app.app_context():
        usuarios = Usuario.query.all()
        
        print()
        print("=" * 60)
        print("👥 USUARIOS EN EL SISTEMA")
        print("=" * 60)
        print()
        
        if not usuarios:
            print("❌ No hay usuarios en el sistema")
            print()
            return
        
        for usuario in usuarios:
            print(f"ID: {usuario.id}")
            print(f"Nombre: {usuario.nombre_completo}")
            print(f"Email: {usuario.email}")
            print(f"Rol: {usuario.rol}")
            print(f"Activo: {'✅' if usuario.activo else '❌'}")
            print(f"Fecha registro: {usuario.fecha_registro}")
            print("-" * 60)
        
        print()


def crear_usuario_prueba():
    """Crea un usuario de prueba"""
    
    app = create_app('development')
    
    with app.app_context():
        # Verificar si ya existe
        usuario_existe = Usuario.query.filter_by(email='usuario@test.com').first()
        
        if usuario_existe:
            print("❌ El usuario de prueba ya existe")
            print(f"   Email: usuario@test.com")
            print(f"   Contraseña: Test123!")
            return
        
        # Crear usuario de prueba
        usuario = Usuario(
            nombre_completo='Usuario Test',
            email='usuario@test.com',
            rol='usuario',
            moneda_preferida='COP',
            activo=True
        )
        usuario.set_password('Test123!')
        
        db.session.add(usuario)
        db.session.commit()
        
        print()
        print("✅ Usuario de prueba creado exitosamente")
        print()
        print("📧 Email: usuario@test.com")
        print("🔑 Contraseña: Test123!")
        print()


def menu_principal():
    """Muestra el menú principal"""
    
    while True:
        print()
        print("=" * 60)
        print("🔧 GESTIÓN DE USUARIOS - FINANZAS PERSONALES")
        print("=" * 60)
        print()
        print("1. Resetear contraseña del administrador")
        print("2. Listar todos los usuarios")
        print("3. Crear usuario de prueba")
        print("4. Salir")
        print()
        
        opcion = input("Selecciona una opción (1-4): ").strip()
        
        if opcion == '1':
            reset_admin_password()
        elif opcion == '2':
            listar_usuarios()
        elif opcion == '3':
            crear_usuario_prueba()
        elif opcion == '4':
            print()
            print("👋 ¡Hasta luego!")
            print()
            break
        else:
            print()
            print("❌ Opción inválida. Intenta de nuevo.")


if __name__ == "__main__":
    try:
        menu_principal()
    except KeyboardInterrupt:
        print()
        print()
        print("⚠️  Operación cancelada por el usuario")
        print()
    except Exception as e:
        print()
        print(f"❌ Error: {str(e)}")
        print()
        import traceback
        traceback.print_exc()