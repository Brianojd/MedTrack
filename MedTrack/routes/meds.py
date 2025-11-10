from flask import render_template, request, redirect, url_for
from . import meds_bp
from models import db, MedicacionUsuario, MedicamentoNombreEnum
from datetime import datetime
from decimal import Decimal, InvalidOperation

@meds_bp.get("/")
def list_meds():
    meds = MedicacionUsuario.query.order_by(MedicacionUsuario.desde.desc()).all()
    # Pasamos la lista del enum para el <select> del modal
    return render_template(
        "meds_list.html",
        page_title="Medicaciones",
        meds=meds,
        medicamentos_enum=list(MedicamentoNombreEnum)
    )

@meds_bp.get("/crear")
def crear_med_form():
    return render_template(
        "meds_form.html",
        page_title="Nueva Medicación"
    )

@meds_bp.post("/crear")
def crear_med():
    nombre_predef = request.form.get("nombre_predefinido") or ""
    nombre = request.form.get("nombre") or ""
    # Si seleccionó una opción del enum, priorizamos esa
    final_name = nombre_predef.strip() or nombre.strip()

    dosis = request.form.get("dosis")
    unidad = request.form.get("unidad")
    desde = request.form.get("desde")
    hasta = request.form.get("hasta")
    hora = request.form.get("hora")
    instrucciones = request.form.get("instrucciones")

    # Parseos seguros
    try:
        dosis_val = Decimal(dosis) if dosis else None
    except (InvalidOperation, TypeError):
        dosis_val = None

    med = MedicacionUsuario(
        usuario_id=1,  # por ahora, fijo
        nombre_medicamento=final_name or "(Sin nombre)",
        dosis=dosis_val,
        unidad=unidad,
        desde=datetime.strptime(desde, "%Y-%m-%d").date() if desde else datetime.utcnow().date(),
        hasta=datetime.strptime(hasta, "%Y-%m-%d").date() if hasta else None,
        hora=datetime.strptime(hora, "%H:%M").time() if hora else datetime.utcnow().time(),
        instrucciones=instrucciones
    )
    db.session.add(med)
    db.session.commit()
    return redirect(url_for("meds.list_meds"))
