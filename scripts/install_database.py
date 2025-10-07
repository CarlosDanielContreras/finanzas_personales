"""
Script de Instalación de Base de Datos
Aplicación de Finanzas Personales
Versión Local (MySQL)
"""

import mysql.connector
from mysql.connector import Error
import sys
import os

# Agregar el directorio raíz al path para importar los modelos
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class DatabaseInstaller:
    def __init__(self):
        self.host = "localhost"
        self.user = "root"
        self.password = ""  # Contraseña de tu MySQL en XAMPP (por defecto vacía)
        self.database_name = "finanzas_personales"
        self.connection = None
        
    def crear_conexion_inicial(self):
        """Conecta a MySQL sin especificar base de datos"""
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password
            )
            if self.connection.is_connected():
                print("✅ Conexión a MySQL exitosa")
                return True
        except Error as e:
            print(f"❌ Error al conectar a MySQL: {e}")
            print("\n💡 Soluciones:")
            print("   1. Asegúrate de que XAMPP esté corriendo")
            print("   2. Verifica que MySQL esté iniciado en el panel de XAMPP")
            print("   3. Si tienes contraseña en MySQL, edita este script y agrégala")
            return False
    
    def crear_base_datos(self):
        """Crea la base de datos si no existe"""
        try:
            cursor = self.connection.cursor()
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {self.database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
            print(f"✅ Base de datos '{self.database_name}' creada")
            cursor.close()
            
            # Reconectar con la base de datos específica
            self.connection.close()
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database_name
            )
            return True
        except Error as e:
            print(f"❌ Error al crear base de datos: {e}")
            return False
    
    def crear_tablas_con_sqlalchemy(self):
        """Crea las tablas usando SQLAlchemy"""
        try:
            print("📋 Creando tablas con SQLAlchemy...")
            
            from app import create_app, db
            
            app = create_app('development')
            
            with app.app_context():
                # Importar todos los modelos
                from app.models import (
                    Usuario, ConfiguracionUsuario, Categoria, Cuenta,
                    Transaccion, Presupuesto, MetaAhorro, AporteMeta,
                    ConsejoFinanciero, Sesion, LogActividad, EstadisticaApp
                )
                
                # Crear todas las tablas
                db.create_all()
                
                print("✅ Todas las tablas creadas exitosamente")
                return True
                
        except Exception as e:
            print(f"❌ Error al crear tablas: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def insertar_datos_iniciales(self):
        """Inserta categorías predefinidas y usuario admin"""
        try:
            print("📝 Insertando datos iniciales...")
            
            from app import create_app, db
            from app.models.categoria import Categoria
            from app.models.usuario import Usuario, ConfiguracionUsuario
            
            app = create_app('development')
            
            with app.app_context():
                # Verificar si ya hay categorías
                count = Categoria.query.count()
                
                if count == 0:
                    print("  ⏳ Insertando categorías predefinidas...")
                    
                    # Categorías de egresos
                    categorias_egresos = [
                        Categoria(nombre='Alimentación', tipo='egreso', color='#e74c3c', icono='fa-utensils'),
                        Categoria(nombre='Transporte', tipo='egreso', color='#3498db', icono='fa-car'),
                        Categoria(nombre='Vivienda', tipo='egreso', color='#9b59b6', icono='fa-home'),
                        Categoria(nombre='Servicios', tipo='egreso', color='#f39c12', icono='fa-bolt'),
                        Categoria(nombre='Salud', tipo='egreso', color='#1abc9c', icono='fa-heartbeat'),
                        Categoria(nombre='Educación', tipo='egreso', color='#2ecc71', icono='fa-graduation-cap'),
                        Categoria(nombre='Entretenimiento', tipo='egreso', color='#e67e22', icono='fa-gamepad'),
                        Categoria(nombre='Ropa', tipo='egreso', color='#95a5a6', icono='fa-tshirt'),
                        Categoria(nombre='Tecnología', tipo='egreso', color='#34495e', icono='fa-laptop'),
                        Categoria(nombre='Otros Gastos', tipo='egreso', color='#7f8c8d', icono='fa-ellipsis-h'),
                    ]
                    
                    # Categorías de ingresos
                    categorias_ingresos = [
                        Categoria(nombre='Salario', tipo='ingreso', color='#27ae60', icono='fa-money-bill-wave'),
                        Categoria(nombre='Freelance', tipo='ingreso', color='#16a085', icono='fa-briefcase'),
                        Categoria(nombre='Inversiones', tipo='ingreso', color='#2980b9', icono='fa-chart-line'),
                        Categoria(nombre='Bonos', tipo='ingreso', color='#8e44ad', icono='fa-gift'),
                        Categoria(nombre='Otros Ingresos', tipo='ingreso', color='#95a5a6', icono='fa-plus-circle'),
                    ]
                    
                    for cat in categorias_egresos + categorias_ingresos:
                        db.session.add(cat)
                    
                    db.session.commit()
                    print("  ✓ Categorías predefinidas insertadas")
                else:
                    print("  ℹ️ Categorías ya existen")
                
                # Verificar si ya existe usuario admin
                admin_count = Usuario.query.filter_by(rol='admin').count()
                
                if admin_count == 0:
                    print("  ⏳ Creando usuario administrador...")
                    
                    # Crear usuario administrador
                    admin = Usuario(
                        nombre_completo='Administrador',
                        email='admin@finanzas.com',
                        rol='admin',
                        moneda_preferida='COP'
                    )
                    admin.set_password('Admin123!')
                    
                    db.session.add(admin)
                    db.session.commit()
                    
                    # Crear configuración para el admin
                    config_admin = ConfiguracionUsuario(
                        usuario_id=admin.id,
                        notificaciones_email=True,
                        tema='claro',
                        idioma='es'
                    )
                    db.session.add(config_admin)
                    db.session.commit()
                    
                    print("  ✓ Usuario administrador creado")
                    print(f"     📧 Email: admin@finanzas.com")
                    print(f"     🔑 Contraseña: Admin123!")
                    print("     ⚠️  IMPORTANTE: Cambiar esta contraseña después del primer acceso")
                else:
                    print("  ℹ️ Usuario administrador ya existe")
                
                print("✅ Datos iniciales insertados correctamente")
                return True
                
        except Exception as e:
            print(f"❌ Error al insertar datos iniciales: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def verificar_instalacion(self):
        """Verifica que todas las tablas se hayan creado correctamente"""
        try:
            cursor = self.connection.cursor()
            cursor.execute("SHOW TABLES")
            tables = cursor.fetchall()
            cursor.close()
            
            print("\n📊 Tablas creadas en la base de datos:")
            for table in tables:
                print(f"   • {table[0]}")
            
            print(f"\n✅ Total de tablas: {len(tables)}")
            return True
            
        except Error as e:
            print(f"❌ Error al verificar instalación: {e}")
            return False
    
    def cerrar_conexion(self):
        """Cierra la conexión a la base de datos"""
        if self.connection and self.connection.is_connected():
            self.connection.close()
            print("\n🔌 Conexión cerrada")
    
    def instalar(self):
        """Ejecuta el proceso completo de instalación"""
        print("="*60)
        print("🚀 INSTALADOR DE BASE DE DATOS")
        print("   Aplicación de Finanzas Personales")
        print("="*60)
        print()
        
        # Paso 1: Conectar a MySQL
        print("📡 Paso 1: Conectando a MySQL...")
        if not self.crear_conexion_inicial():
            return False
        
        # Paso 2: Crear base de datos
        print("\n🗄️  Paso 2: Creando base de datos...")
        if not self.crear_base_datos():
            return False
        
        # Paso 3: Crear tablas con SQLAlchemy
        print("\n📋 Paso 3: Creando tablas...")
        if not self.crear_tablas_con_sqlalchemy():
            return False
        
        # Paso 4: Insertar datos iniciales
        print("\n📝 Paso 4: Insertando datos iniciales...")
        if not self.insertar_datos_iniciales():
            return False
        
        # Paso 5: Verificar instalación
        print("\n🔍 Paso 5: Verificando instalación...")
        if not self.verificar_instalacion():
            return False
        
        print("\n" + "="*60)
        print("✅ INSTALACIÓN COMPLETADA EXITOSAMENTE")
        print("="*60)
        print("\n📌 Próximos pasos:")
        print("   1. Ejecuta: python run.py")
        print("   2. Abre: http://localhost:5000")
        print("   3. Accede con: admin@finanzas.com / Admin123!")
        print("   4. ⚠️  Cambia la contraseña del administrador")
        print()
        
        return True


def main():
    """Función principal"""
    installer = DatabaseInstaller()
    
    try:
        print("⚙️  Configuración:")
        print(f"   📍 Host: {installer.host}")
        print(f"   👤 Usuario: {installer.user}")
        print(f"   🗄️  Base de datos: {installer.database_name}")
        print()
        
        respuesta = input("¿Continuar con la instalación? (s/n): ")
        
        if respuesta.lower() != 's':
            print("\n❌ Instalación cancelada")
            return
        
        print()
        
        # Ejecutar instalación
        if installer.instalar():
            print("🎉 ¡Base de datos lista para usar!")
        else:
            print("\n❌ La instalación falló. Revisa los errores anteriores.")
            print("\n💡 Consejos:")
            print("   - Verifica que XAMPP esté corriendo")
            print("   - Verifica que MySQL esté iniciado")
            print("   - Revisa que no tengas errores en los modelos")
    
    except KeyboardInterrupt:
        print("\n\n⚠️  Instalación cancelada por el usuario")
    
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        installer.cerrar_conexion()


if __name__ == "__main__":
    main()