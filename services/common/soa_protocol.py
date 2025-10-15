"""
Protocolo de comunicación SOA para el Sistema de Reservación UDP
Formato: NNNNNSSSSSDATOS
"""
import json
import socket
from typing import Dict, Any

class SOAProtocol:
    """Clase para manejar el protocolo SOA del sistema"""
    
    def __init__(self, bus_host: str = "localhost", bus_port: int = 5000):
        self.bus_host = bus_host
        self.bus_port = bus_port
    
    def format_message(self, service_code: str, data: Dict[str, Any]) -> str:
        """
        Formatear mensaje según protocolo SOA
        Formato: NNNNNSSSSSDATOS
        """
        json_data = json.dumps(data, ensure_ascii=False)
        service_code = service_code.ljust(5)[:5]  # Asegurar 5 caracteres
        message = service_code + json_data
        message_length = len(message)
        length_str = str(message_length).zfill(5)  # 5 dígitos con ceros a la izquierda
        
        return length_str + message
    
    def parse_message(self, message: str) -> tuple:
        """
        Parsear mensaje recibido
        Retorna: (service_code, data)
        """
        if len(message) < 10:  # Mínimo 5 (longitud) + 5 (servicio)
            raise ValueError("Mensaje muy corto")
        
        length_str = message[:5]
        service_code = message[5:10]
        data_str = message[10:]
        
        try:
            data = json.loads(data_str)
            return service_code.strip(), data
        except json.JSONDecodeError:
            raise ValueError("Error al decodificar JSON")
    
    def send_to_bus(self, message: str) -> str:
        """
        Enviar mensaje al bus de servicios
        """
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.bus_host, self.bus_port))
                s.sendall(message.encode('utf-8'))
                
                # Recibir respuesta
                response = s.recv(4096).decode('utf-8')
                return response
        except Exception as e:
            return f"Error: {str(e)}"
    
    def send_request(self, service_code: str, data: Dict[str, Any]) -> str:
        """
        Enviar petición a un servicio específico
        """
        message = self.format_message(service_code, data)
        return self.send_to_bus(message)

