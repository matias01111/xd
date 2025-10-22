#!/usr/bin/env python3
"""
Script para configurar la base de datos del Sistema de Reservación UDP
"""
import psycopg2
import os
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

def setup_database():
    """Configurar base de datos PostgreSQL"""
    try:
        print("🗄️  Configurando base de datos PostgreSQL...")
        
        # Configuración de conexión
        db_config = {
            'host': 'localhost',
            'port': 5432,
            'user': 'postgres',
            'password': 'xd'  # Cambiar por tu contraseña
        }
        
        # Conectar a PostgreSQL
        print("Conectando a PostgreSQL...")
        conn = psycopg2.connect(**db_config)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Crear base de datos si no existe
        print("Creando base de datos 'reservas_udp'...")
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'reservas_udp'")
        exists = cursor.fetchone()
        
        if not exists:
            cursor.execute("CREATE DATABASE reservas_udp")
            print("✅ Base de datos creada exitosamente")
        else:
            print("ℹ️  La base de datos ya existe")
        
        # Cerrar conexión inicial
        cursor.close()
        conn.close()
        
        # Conectar a la nueva base de datos
        db_config['database'] = 'reservas_udp'
        conn = psycopg2.connect(**db_config)
        cursor = conn.cursor()
        
        # Ejecutar script de inicialización
        print("Ejecutando script de inicialización...")
        
        # Verificar si las tablas ya existen
        cursor.execute("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = cursor.fetchone()[0]
        
        if table_count == 0:
            try:
                with open('database/init.sql', 'r', encoding='utf-8') as f:
                    sql_script = f.read()
            except UnicodeDecodeError:
                with open('database/init.sql', 'r', encoding='latin-1') as f:
                    sql_script = f.read()
            
            # Eliminar comandos psql que no se pueden ejecutar con psycopg2
            sql_lines = sql_script.split('\n')
            clean_lines = []
            for line in sql_lines:
                # Omitir líneas con comandos psql como \c, CREATE DATABASE, etc.
                if not line.strip().startswith('\\') and not 'CREATE DATABASE' in line.upper():
                    clean_lines.append(line)
            sql_script = '\n'.join(clean_lines)
        
            # Ejecutar el script
            cursor.execute(sql_script)
            conn.commit()
            print("✅ Tablas creadas exitosamente")
        else:
            print("ℹ️  Las tablas ya existen, omitiendo creación")
        
        print("✅ Base de datos configurada exitosamente")
        
        # Verificar tablas creadas
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        tables = cursor.fetchall()
        
        print("\n📋 Tablas creadas:")
        for table in tables:
            print(f"   • {table[0]}")
        
        # Insertar datos de prueba
        print("\n📝 Insertando datos de prueba...")
        
        # Verificar si ya hay datos
        cursor.execute("SELECT COUNT(*) FROM usuarios")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            # Insertar usuario administrador de prueba
            cursor.execute("""
                INSERT INTO usuarios (rut, correo_institucional, nombre, tipo_usuario) 
                VALUES ('12345678-9', 'admin@udp.cl', 'Administrador Sistema', 'administrador')
                ON CONFLICT (rut) DO NOTHING
            """)
            
            # Insertar usuario estudiante de prueba
            cursor.execute("""
                INSERT INTO usuarios (rut, correo_institucional, nombre, tipo_usuario) 
                VALUES ('87654321-0', 'estudiante@udp.cl', 'Estudiante Prueba', 'estudiante')
                ON CONFLICT (rut) DO NOTHING
            """)
            
            conn.commit()
            print("✅ Usuarios de prueba creados")
        else:
            print("ℹ️  Los datos de prueba ya existen")
        
        cursor.close()
        conn.close()
        
        print("\n🎉 Base de datos configurada correctamente!")
        print("\n📋 Credenciales de prueba:")
        print("   • Administrador: 12345678-9 / admin@udp.cl")
        print("   • Estudiante: 87654321-0 / estudiante@udp.cl")
        
    except psycopg2.Error as e:
        print(f"❌ Error de base de datos: {e}")
        print("\n💡 Asegúrate de que:")
        print("   1. PostgreSQL esté instalado y ejecutándose")
        print("   2. La contraseña sea correcta")
        print("   3. El usuario 'postgres' tenga permisos para crear bases de datos")
        
    except FileNotFoundError:
        print("❌ No se encontró el archivo database/init.sql")
        
    except Exception as e:
        import traceback
        print(f"❌ Error inesperado: {e}")
        print("\nTraceback completo:")
        traceback.print_exc()

if __name__ == "__main__":
    setup_database()




