from flask import Flask, render_template
from config import Config
from models import db, Usuario, MedicacionUsuario, MetricaSaludUsuario
from routes import meds_bp, metrics_bp
from datetime import datetime, timedelta

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(meds_bp)
    app.register_blueprint(metrics_bp)

    @app.get("/")
    def home():
     
        usuario = Usuario.query.get(1)
        if not usuario:
           
            return render_template("index.html",
                                   page_title="MedTrack",
                                   usuario=Usuario(username="usuario"),
                                   imc=None, clasificacion_imc=None,
                                   agua_litros=None,
                                   meds_hoy_grouped={})

       
        peso_row = (MetricaSaludUsuario.query
                    .filter_by(usuario_id=usuario.id, tipo='Peso')
                    .order_by(MetricaSaludUsuario.fecha.desc())
                    .first())
        peso_kg = float(peso_row.valor) if peso_row else None

       
        imc = None
        clasificacion = None
        if peso_kg and usuario.altura_cm:
            altura_m = usuario.altura_cm / 100.0
            imc = peso_kg / (altura_m ** 2)
            if imc < 18.5:
                clasificacion = "Bajo peso"
            elif imc < 25:
                clasificacion = "Normal"
            elif imc < 30:
                clasificacion = "Sobrepeso"
            else:
                clasificacion = "Obesidad"

       
        agua_litros = (peso_kg * 0.035) if peso_kg else None

       
        now = datetime.now()
        end = now + timedelta(days=1)

        items = []
        meds = MedicacionUsuario.query.filter_by(usuario_id=usuario.id).all()
        for m in meds:
           
            if m.desde and m.desde > end.date():
                continue
            if m.hasta and m.hasta < now.date():
                continue

            
            dt_hoy = datetime.combine(now.date(), m.hora)
            if now <= dt_hoy <= end:
                items.append({
                    "nombre": m.nombre_medicamento,
                    "dosis": float(m.dosis) if m.dosis is not None else None,
                    "unidad": m.unidad,
                    "instrucciones": m.instrucciones,
                    "programada_para": dt_hoy
                })

            
            dt_maniana = datetime.combine(end.date(), m.hora)
            if now <= dt_maniana <= end:
                items.append({
                    "nombre": m.nombre_medicamento,
                    "dosis": float(m.dosis) if m.dosis is not None else None,
                    "unidad": m.unidad,
                    "instrucciones": m.instrucciones,
                    "programada_para": dt_maniana
                })

       
        meds_hoy_grouped = {}
        for it in sorted(items, key=lambda x: (x["nombre"], x["programada_para"])):
            meds_hoy_grouped.setdefault(it["nombre"], []).append(it)

        return render_template("index.html",
                               page_title="MedTrack",
                               usuario=usuario,
                               imc=imc,
                               clasificacion_imc=clasificacion,
                               agua_litros=agua_litros,
                               meds_hoy_grouped=meds_hoy_grouped)

    return app

if __name__ == "__main__":
    create_app().run(debug=True)
