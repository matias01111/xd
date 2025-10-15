#!/usr/bin/env python3
"""
Script para iniciar todos los servicios del Sistema de Reservación UDP
"""
import subprocess
import sys
import time
import os
from threading import Thread

def run_service(service_name, service_file, port):
    """Ejecutar un servicio en un hilo separado"""
    try:
        print(f"Iniciando {service_name} en puerto {port}...")
        process = subprocess.Popen([
            sys.executable, service_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Esperar un poco para que el servicio se inicie
        time.sleep(2)
        
        if process.poll() is None:
            print(f"✅ {service_name} iniciado correctamente en puerto {port}")
        else:
            print(f"❌ Error iniciando {service_name}")
            
        return process
    except Exception as e:
        print(f"❌ Error ejecutando {service_name}: {e}")
        return None

def main():
    """Función principal"""
    print("🚀 Iniciando Sistema de Reservación UDP...")
    print("=" * 50)
    
    # Lista de servicios a iniciar
    services = [
        ("Bus de Servicios", "services/service_bus.py", 5000),
        ("Servicio de Autenticación", "services/auth_service.py", 5001),
        ("Servicio de Usuarios", "services/user_service.py", 5002),
        ("Servicio de Espacios", "services/space_service.py", 5003),
        ("Servicio de Disponibilidad", "services/availability_service.py", 5004),
        ("Servicio de Reservas", "services/booking_service.py", 5005),
        ("Servicio de Incidencias", "services/incident_service.py", 5006),
        ("Servicio de Administración", "services/admin_service.py", 5007),
        ("Servicio de Notificaciones", "services/notification_service.py", 5008),
        ("Servicio de Reportes", "services/report_service.py", 5009),
    ]
    
    processes = []
    
    try:
        # Iniciar todos los servicios
        for service_name, service_file, port in services:
            if os.path.exists(service_file):
                process = run_service(service_name, service_file, port)
                if process:
                    processes.append((service_name, process))
            else:
                print(f"⚠️  Archivo no encontrado: {service_file}")
        
        print("\n" + "=" * 50)
        print("🎉 Todos los servicios han sido iniciados!")
        print("\n📋 Servicios disponibles:")
        print("   • Bus de Servicios: http://localhost:5000")
        print("   • Autenticación: http://localhost:5001")
        print("   • Usuarios: http://localhost:5002")
        print("   • Espacios: http://localhost:5003")
        print("   • Disponibilidad: http://localhost:5004")
        print("   • Reservas: http://localhost:5005")
        print("   • Incidencias: http://localhost:5006")
        print("   • Administración: http://localhost:5007")
        print("   • Notificaciones: http://localhost:5008")
        print("   • Reportes: http://localhost:5009")
        print("\n🌐 Clientes Web:")
        print("   • Cliente Estudiantes: http://localhost:3000")
        print("   • Cliente Administradores: http://localhost:3001")
        print("\n⏹️  Presiona Ctrl+C para detener todos los servicios")
        
        # Mantener el script ejecutándose
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Deteniendo servicios...")
        for service_name, process in processes:
            try:
                process.terminate()
                print(f"✅ {service_name} detenido")
            except:
                print(f"❌ Error deteniendo {service_name}")
        
        print("\n👋 Sistema detenido correctamente")

if __name__ == "__main__":
    main()




