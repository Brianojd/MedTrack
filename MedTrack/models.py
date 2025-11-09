from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Usuario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    username = db.Column(db.String(50))
    password_hash = db.Column(db.String(255), nullable=False)
    nombre = db.Column(db.String(200))
    fecha_nacimiento = db.Column(db.Date)
    sexo = db.Column(db.String(20))
    altura_cm = db.Column(db.SmallInteger)
    nivel_actividad = db.Column(db.String(16))
    activo = db.Column(db.Boolean, default=False)
    fecha_creacion_usuario = db.Column(db.DateTime, default=datetime.utcnow)

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
