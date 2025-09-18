from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

@dataclass
class Usuario:
    email: str
    username: str 
    password_hash: str
    nombre: str
    fecha_nacimiento: Optional[date] = None
    sexo: Optional[str] = None
    altura_cm: Optional[int] = None
    nivel_actividad: Optional[str] = None
    activo: bool = False
    fecha_creacion_usuario: Optional[datetime] = None
    id: Optional[int] = None

