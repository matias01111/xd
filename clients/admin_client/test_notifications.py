import requests
import json
from datetime import datetime, timedelta

# Test 1: Create a booking (should trigger notification)
print("=== TEST 1: Crear Reserva (Trigger Notificación) ===")
booking_data = {
    "id_usuario": 2,
    "id_espacio": 1,
    "fecha_inicio": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT10:00:00"),
    "fecha_fin": (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%dT12:00:00"),
    "motivo": "Reunión de equipo - TEST NOTIFICACION",
    "recurrente": False
}

response = requests.post("http://localhost:5005/bookings/create", json=booking_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

if response.status_code == 200:
    booking_id = response.json().get('id_reserva')
    print(f"\n✅ Reserva creada con ID: {booking_id}")
    
    # Test 2: Check notification history
    print("\n=== TEST 2: Verificar Historial de Notificaciones ===")
    notif_response = requests.get("http://localhost:5008/notifications/history")
    print(f"Status: {notif_response.status_code}")
    notificaciones = notif_response.json()
    print(f"Total notificaciones: {len(notificaciones)}")
    if notificaciones:
        print("Última notificación:")
        print(json.dumps(notificaciones[0], indent=2, ensure_ascii=False))
else:
    print(f"❌ Error al crear reserva")
