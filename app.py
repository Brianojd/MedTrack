from flask import Flask, render_template, request, redirect, url_for, flash, session
from config import Config
from models import db, Usuario, MedicacionUsuario, MetricaSaludUsuario
from routes import meds_bp, metrics_bp
from datetime import datetime, timedelta


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    app.secret_key = "ojco"

    db.init_app(app)
    with app.app_context():
        db.create_all()

    app.register_blueprint(meds_bp)
    app.register_blueprint(metrics_bp)

    # ---------------------------- HELPERS ----------------------------
    def get_logged_user():
        user_id = session.get("user_id")
        if not user_id:
            return None
        return Usuario.query.get(user_id)

    # ---------------------------- ROOT REDIRECT ----------------------------
    @app.route("/")
    def root():
        """Siempre enviar al login o home según sesión."""
        if "user_id" not in session:
            return redirect(url_for("login"))
        return redirect(url_for("home"))

    # ---------------------------- REGISTER ----------------------------
    @app.route("/register", methods=["GET", "POST"])
    def register():
        if request.method == "POST":
            nombre = request.form["nombre"]
            email = request.form["email"]
            password = request.form["password"]

            if Usuario.query.filter_by(email=email).first():
                flash("Ese email ya está registrado.", "danger")
                return redirect(url_for("register"))

            nuevo = Usuario(
                nombre=nombre,
                email=email,
                form_completado=False  # 🔥 FIX IMPORTANTE
            )
            nuevo.set_password(password)

            db.session.add(nuevo)
            db.session.commit()

            flash("Registro exitoso. Ahora iniciá sesión.", "success")
            return redirect(url_for("login"))

        return render_template("register.html")

    # ---------------------------- LOGIN ----------------------------
    @app.route("/login", methods=["GET", "POST"])
    def login():
        if request.method == "POST":
            email = request.form["email"]
            password = request.form["password"]

            usuario = Usuario.query.filter_by(email=email).first()

            if usuario and usuario.check_password(password):
                session["user_id"] = usuario.id

                if not usuario.form_completado:
                    return redirect(url_for("form_inicial"))

                return redirect(url_for("home"))

            flash("Email o contraseña incorrectos.", "danger")
            return redirect(url_for("login"))

        return render_template("login.html")

    # ---------------------------- FORM INICIAL ----------------------------
    @app.route("/form-inicial", methods=["GET", "POST"])
    def form_inicial():
        usuario = get_logged_user()
        if not usuario:
            return redirect(url_for("login"))

        if request.method == "POST":
            usuario.fecha_nacimiento = datetime.strptime(request.form["fecha_nacimiento"], "%Y-%m-%d")
            usuario.sexo = request.form["sexo"]
            usuario.altura_cm = int(request.form["altura_cm"])
            usuario.nivel_actividad = request.form["nivel_actividad"]
            usuario.form_completado = True

            db.session.commit()
            return redirect(url_for("home"))

        return render_template("form_inicial.html")

    # ---------------------------- LOGOUT ----------------------------
    @app.route("/logout")
    def logout():
        session.clear()
        return redirect(url_for("login"))

    # ---------------------------- HOME ----------------------------
    @app.route("/home")
    def home():
        usuario = get_logged_user()
        if not usuario:
            return redirect(url_for("login"))

        if not usuario.form_completado:
            return redirect(url_for("form_inicial"))

        # IMC
        peso_row = MetricaSaludUsuario.query.filter_by(usuario_id=usuario.id, tipo='Peso') \
            .order_by(MetricaSaludUsuario.fecha.desc()).first()
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
                    "dosis": float(m.dosis) if m.dosis else None,
                    "unidad": m.unidad,
                    "instrucciones": m.instrucciones,
                    "programada_para": dt_hoy
                })

        meds_hoy_grouped = {}
        for it in sorted(items, key=lambda x: (x["nombre"], x["programada_para"])):
            meds_hoy_grouped.setdefault(it["nombre"], []).append(it)

        return render_template(
            "index.html",
            page_title="MedTrack",
            usuario=usuario,
            imc=imc,
            clasificacion_imc=clasificacion,
            agua_litros=agua_litros,
            meds_hoy_grouped=meds_hoy_grouped
        )

    return app


if __name__ == "__main__":
    create_app().run(debug=True)
