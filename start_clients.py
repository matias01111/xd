#!/usr/bin/env python3
"""
Script para iniciar los clientes web del Sistema de Reservación UDP
"""
import subprocess
import sys
import time
import os
from threading import Thread

def run_client(client_name, client_dir, port):
    """Ejecutar un cliente en un hilo separado"""
    try:
        print(f"Iniciando {client_name} en puerto {port}...")
        
        # Obtener ruta absoluta del directorio del cliente
        abs_client_dir = os.path.abspath(client_dir)
        
        # Verificar si existen las dependencias
        node_modules_path = os.path.join(abs_client_dir, "node_modules")
        if not os.path.exists(node_modules_path):
            print(f"Instalando dependencias para {client_name}...")
            subprocess.run(["npm", "install"], cwd=abs_client_dir, check=True)
        
        # Iniciar el cliente sin cambiar el directorio actual
        server_path = os.path.join(abs_client_dir, "server.js")
        process = subprocess.Popen([
            "node", server_path
        ], cwd=abs_client_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar un poco para que el cliente se inicie
        time.sleep(2)
        
        if process.poll() is None:
            print(f"✅ {client_name} iniciado correctamente en puerto {port}")
        else:
            stdout, stderr = process.communicate()
            print(f"❌ Error iniciando {client_name}")
            if stderr:
                print(f"   Error: {stderr.decode('utf-8', errors='ignore')[:200]}")
            
        return process
    except Exception as e:
        print(f"❌ Error ejecutando {client_name}: {e}")
        return None

def main():
    """Función principal"""
    print("🌐 Iniciando Clientes Web del Sistema de Reservación UDP...")
    print("=" * 60)
    
    # Lista de clientes a iniciar
    clients = [
        ("Cliente Web Estudiantes", "clients/student_client", 3000),
        ("Cliente Web Administradores", "clients/admin_client", 3001),
    ]
    
    processes = []
    
    try:
        # Verificar que Node.js esté instalado
        try:
            subprocess.run(["node", "--version"], check=True, capture_output=True)
            print("✅ Node.js detectado")
        except:
            print("❌ Node.js no está instalado. Por favor instala Node.js primero.")
            return
        
        # Iniciar todos los clientes
        for client_name, client_dir, port in clients:
            if os.path.exists(client_dir):
                process = run_client(client_name, client_dir, port)
                if process:
                    processes.append((client_name, process))
            else:
                print(f"⚠️  Directorio no encontrado: {client_dir}")
        
        print("\n" + "=" * 60)
        print("🎉 Todos los clientes han sido iniciados!")
        print("\n🌐 Clientes Web disponibles:")
        print("   • Cliente Estudiantes: http://localhost:3000")
        print("   • Cliente Administradores: http://localhost:3001")
        print("\n📝 Credenciales de prueba:")
        print("   • Usuario: 12345678-9 (estudiante)")
        print("   • Administrador: admin@udp.cl (administrador)")
        print("\n⏹️  Presiona Ctrl+C para detener todos los clientes")
        
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo clientes...")
        for client_name, process in processes:
            try:
                process.terminate()
                print(f"✅ {client_name} detenido")
            except:
                print(f"❌ Error deteniendo {client_name}")
        
        print("\n👋 Clientes detenidos correctamente")

if __name__ == "__main__":
    main()




