from flask import render_template, request, redirect, url_for
from . import meds_bp
from models import db, MedicacionUsuario
from datetime import datetime

@meds_bp.get("/")
def list_meds():
    meds = MedicacionUsuario.query.all()
    return render_template("meds_list.html", page_title="Medicaciones", meds=meds)

@meds_bp.get("/crear")
def crear_med_form():
    return render_template("meds_form.html", page_title="Nueva Medicación")

@meds_bp.post("/crear")
def crear_med():
    nombre = request.form.get("nombre")
    dosis = request.form.get("dosis")
    unidad = request.form.get("unidad")
    desde = request.form.get("desde")
    hasta = request.form.get("hasta")
    hora = request.form.get("hora")
    instrucciones = request.form.get("instrucciones")

    med = MedicacionUsuario(
        usuario_id=1,  # por ahora, fijo
        nombre_medicamento=nombre,
        dosis=dosis,
        unidad=unidad,
        desde=datetime.strptime(desde, "%Y-%m-%d"),
        hasta=datetime.strptime(hasta, "%Y-%m-%d") if hasta else None,
        hora=datetime.strptime(hora, "%H:%M").time(),
        instrucciones=instrucciones
    )
    db.session.add(med)
    db.session.commit()
    return redirect(url_for("meds.list_meds"))
