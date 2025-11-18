from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from enum import Enum
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class MedicamentoNombreEnum(Enum):
    IBUPROFENO   = "Ibuprofeno"
    PARACETAMOL  = "Paracetamol"
    AMOXICILINA  = "Amoxicilina"
    AZITROMICINA = "Azitromicina"
    CIPROFLOXACINO = "Ciprofloxacino"
    DICLOFENAC   = "Diclofenac"
    NAPROXENO    = "Naproxeno"
    OMEPRAZOL    = "Omeprazol"
    LORATADINA   = "Loratadina"
    METFORMINA   = "Metformina"

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(50))
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(200))

    # Campos del formulario inicial
    fecha_nacimiento = db.Column(db.Date)
    sexo = db.Column(db.String(20))
    altura_cm = db.Column(db.SmallInteger)
    nivel_actividad = db.Column(db.String(16))

    # ⭐ ACÁ ESTÁ EL PROBLEMA ⭐
    form_completado = db.Column(db.Boolean, default=False)

    # Otros existentes
    activo = db.Column(db.Boolean, default=False)
    fecha_creacion_usuario = db.Column(db.DateTime, default=datetime.utcnow)

    # Métodos para manejar contraseñas
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class MedicacionUsuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    nombre_medicamento = db.Column(db.String(200), nullable=False)
    forma = db.Column(db.String(20))
    concentracion = db.Column(db.Numeric(10,2))
    unidad = db.Column(db.String(8))
    dosis = db.Column(db.Numeric(10,2))
    desde = db.Column(db.Date, nullable=False)
    hasta = db.Column(db.Date)
    hora = db.Column(db.Time, nullable=False)
    instrucciones = db.Column(db.String(500))

class MetricaMedicacionUsuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    medicacion_usuario_id = db.Column(db.Integer, db.ForeignKey('medicacion_usuario.id'), nullable=False, index=True)
    programada_para = db.Column(db.DateTime, nullable=False, index=True)
    estado = db.Column(db.String(10), nullable=False)  # Tomado/Tarde/Omitido

class MetricaSaludUsuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey('usuario.id'), nullable=False, index=True)
    tipo = db.Column(db.String(16), nullable=False)    # Peso, PAS, PAD, FC, Glucemia
    valor = db.Column(db.Numeric(10,2), nullable=False)
    fecha = db.Column(db.DateTime, default=datetime.utcnow, index=True)
