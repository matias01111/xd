"""
Servicio de Autenticación (AUTH) - Sistema de Reservación UDP
Puerto: 5001
"""
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
import uvicorn

from database.db_config import get_db, init_db
from database.models import Usuario
from services.common.auth_utils import verify_password, get_password_hash, create_access_token, verify_token
from services.common.soa_protocol import SOAProtocol
from datetime import timedelta

app = FastAPI(title="Servicio de Autenticación - AUTH")

# Inicializar base de datos
init_db()

# Modelos Pydantic
class LoginRequest(BaseModel):
    rut: str
    password: str

class TokenResponse(BaseModel):
    token: str
    ok: bool
    user_info: Optional[dict] = None

class RefreshRequest(BaseModel):
    refresh_token: str

class LogoutRequest(BaseModel):
    token: str

@app.post("/auth/login")
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    """Iniciar sesión de usuario"""
    try:
        # Buscar usuario por RUT
        user = db.query(Usuario).filter(
            Usuario.rut == request.rut,
            Usuario.activo == True
        ).first()
        
        if not user:
            raise HTTPException(status_code=401, detail="Credenciales inválidas")
        
        # En un sistema real, aquí verificarías la contraseña
        # Para este ejemplo, asumimos que la contraseña es válida si el usuario existe
        # En producción deberías tener un campo password_hash en la tabla usuarios
        
        # Crear token de acceso
        token_data = {
            "sub": str(user.id_usuario),
            "rut": user.rut,
            "tipo_usuario": user.tipo_usuario,
            "nombre": user.nombre
        }
        
        access_token = create_access_token(token_data)
        
        user_info = {
            "id": user.id_usuario,
            "rut": user.rut,
            "nombre": user.nombre,
            "tipo_usuario": user.tipo_usuario,
            "correo": user.correo_institucional
        }
        
        return TokenResponse(
            token=access_token,
            ok=True,
            user_info=user_info
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/refresh")
async def refresh_token(request: RefreshRequest):
    """Renovar token de acceso"""
    try:
        # Verificar token actual
        payload = verify_token(request.refresh_token)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido")
        
        # Crear nuevo token
        new_token_data = {
            "sub": payload.get("sub"),
            "rut": payload.get("rut"),
            "tipo_usuario": payload.get("tipo_usuario"),
            "nombre": payload.get("nombre")
        }
        
        new_token = create_access_token(new_token_data)
        
        return TokenResponse(
            token=new_token,
            ok=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/auth/logout")
async def logout(request: LogoutRequest):
    """Cerrar sesión"""
    try:
        # En un sistema real, aquí invalidarías el token en una lista negra
        # Para este ejemplo, simplemente confirmamos el logout
        
        return {"logout": True}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/auth/verify/{token}")
async def verify_user_token(token: str):
    """Verificar token de usuario"""
    try:
        payload = verify_token(token)
        if not payload:
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
        
        return {
            "valid": True,
            "user_info": {
                "id": payload.get("sub"),
                "rut": payload.get("rut"),
                "tipo_usuario": payload.get("tipo_usuario"),
                "nombre": payload.get("nombre")
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para el protocolo SOA
@app.post("/soa/message")
async def handle_soa_message(message: str):
    """Manejar mensajes del protocolo SOA"""
    try:
        protocol = SOAProtocol()
        service_code, data = protocol.parse_message(message)
        
        if service_code.strip() == "auth":
            # Procesar comando de autenticación
            if "rut" in data and "pass" in data:
                # Login
                login_req = LoginRequest(rut=data["rut"], password=data["pass"])
                db = next(get_db())
                result = await login(login_req, db)
                
                if result.ok:
                    response_data = {
                        "token": result.token,
                        "ok": True
                    }
                else:
                    response_data = {"error": "Credenciales inválidas"}
            
            elif "refresh" in data:
                # Refresh token
                refresh_req = RefreshRequest(refresh_token=data["refresh"])
                result = await refresh_token(refresh_req)
                response_data = {
                    "token": result.token,
                    "ok": result.ok
                }
            
            elif "logout" in data:
                # Logout
                logout_req = LogoutRequest(token=data["logout"])
                result = await logout(logout_req)
                response_data = result
            
            else:
                response_data = {"error": "Comando no reconocido"}
        
        else:
            response_data = {"error": "Servicio no reconocido"}
        
        # Formatear respuesta según protocolo SOA
        return protocol.format_message("auth", response_data)
        
    except Exception as e:
        return SOAProtocol().format_message("auth", {"error": str(e)})

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=5001)

