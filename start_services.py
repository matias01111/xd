#!/usr/bin/env python3
"""
Script para iniciar todos los servicios del Sistema de Reservación UDP
"""
import subprocess
import sys
import time
import os
import signal

# Variable global para almacenar procesos
processes = []

def signal_handler(sig, frame):
    """Manejar señal de interrupción Ctrl+C"""
    print("\n\n🛑 Deteniendo servicios...")
    for service_name, process in processes:
        try:
            process.terminate()
            process.wait(timeout=3)
            print(f"✅ {service_name} detenido")
        except subprocess.TimeoutExpired:
            process.kill()
            print(f"✅ {service_name} forzado a detenerse")
        except Exception as e:
            print(f"❌ Error deteniendo {service_name}: {e}")
    
    print("\n👋 Sistema detenido correctamente")
    sys.exit(0)

def run_service(service_name, service_file, port):
    """Ejecutar un servicio"""
    try:
        print(f"Iniciando {service_name} en puerto {port}...")
        
        # Crear proceso sin capturar salida (se mostrará en consola)
        process = subprocess.Popen(
            [sys.executable, service_file],
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0
        )
        
        # Esperar para verificar que no falle inmediatamente
        time.sleep(1.5)
        
        if process.poll() is None:
            print(f"✅ {service_name} iniciado correctamente en puerto {port}")
            return process
        else:
            print(f"❌ Error iniciando {service_name} - proceso terminó")
            return None
            
    except Exception as e:
        print(f"❌ Error ejecutando {service_name}: {e}")
        return None

def main():
    """Función principal"""
    global processes
    
    # Registrar manejador de señales
    signal.signal(signal.SIGINT, signal_handler)
    if sys.platform == 'win32':
        signal.signal(signal.SIGBREAK, signal_handler)
    
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
    print("\n⏹️  Presiona Ctrl+C para detener todos los servicios")
    
    # Mantener el script ejecutándose y monitorear procesos
    try:
        while True:
            time.sleep(2)
            # Verificar si algún proceso ha terminado
            for service_name, process in processes:
                if process.poll() is not None:
                    print(f"⚠️  {service_name} se ha detenido inesperadamente")
    except KeyboardInterrupt:
        pass

if __name__ == "__main__":
    main()




