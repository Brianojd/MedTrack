
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from datetime import datetime, timedelta
from decimal import Decimal, InvalidOperation
from data.models import db, MedicacionUsuario, MetricaMedicacionUsuario, MedicamentoNombreEnum


from sqlalchemy import func 
meds_bp = Blueprint("meds", __name__, url_prefix="/meds")


def get_logged_user_id():
    return session.get("user_id")


@meds_bp.get("/")
def list_meds():
    user_id = get_logged_user_id()
    if not user_id:
        flash("Tenés que iniciar sesión para ver tus medicaciones.", "danger")
        return redirect(url_for("login"))

    meds = (
        MedicacionUsuario.query.filter_by(usuario_id=user_id)
        .order_by(MedicacionUsuario.desde.desc())
        .all()
    )

    medicamentos_enum = list(MedicamentoNombreEnum)

    return render_template(
        "meds_list.html",
        page_title="Medicaciones",
        meds=meds,
        medicamentos_enum=medicamentos_enum,
    )


@meds_bp.post("/crear")
def crear_med():
    user_id = get_logged_user_id()
    if not user_id:
        flash("Tenés que iniciar sesión para cargar medicaciones.", "danger")
        return redirect(url_for("login"))

    # --------- SOLO SELECT ---------
    final_name = request.form.get("nombre_predefinido")

    if not final_name:
        flash("Debés seleccionar un medicamento.", "danger")
        return redirect(url_for("meds.list_meds"))

    # --------- Otros campos ---------
    dosis_str = request.form.get("dosis")
    unidad = (request.form.get("unidad") or "").strip()
    desde_str = request.form.get("desde")
    hasta_str = request.form.get("hasta")
    hora_str = request.form.get("hora")
    instrucciones = request.form.get("instrucciones") or None

    if not desde_str or not hora_str:
        flash("Los campos 'Desde' y 'Hora diaria' son obligatorios.", "danger")
        return redirect(url_for("meds.list_meds"))

        # Dosis
    try:
        dosis_val = Decimal(dosis_str) if dosis_str else None
    except (InvalidOperation, TypeError):
        dosis_val = None

    # Fechas
    try:
        desde = datetime.strptime(desde_str, "%Y-%m-%d").date()
    except ValueError:
        flash("La fecha 'Desde' no es válida (YYYY-MM-DD).", "danger")
        return redirect(url_for("meds.list_meds"))

    hasta = None
    if hasta_str:
        try:
            hasta = datetime.strptime(hasta_str, "%Y-%m-%d").date()
        except ValueError:
            flash("La fecha 'Hasta' no es válida (YYYY-MM-DD).", "danger")
            return redirect(url_for("meds.list_meds"))

    # Hora
    try:
        hora_val = datetime.strptime(hora_str, "%H:%M").time()
    except ValueError:
        flash("La hora no es válida (HH:MM).", "danger")
        return redirect(url_for("meds.list_meds"))

    fecha_fin = hasta or desde

    # --------- Crear medicación ---------
    med = MedicacionUsuario(
        usuario_id=user_id,
        nombre_medicamento=final_name,
        forma=None,
        concentracion=None,
        unidad=unidad,
        dosis=dosis_val,
        desde=desde,
        hasta=hasta,
        hora=hora_val,
        instrucciones=instrucciones,
    )
    db.session.add(med)
    db.session.flush()

    # --------- Crear métricas programadas ---------
    fecha_actual = desde

    while fecha_actual <= fecha_fin:
        programada_para = datetime.combine(fecha_actual, hora_val)
        metrica = MetricaMedicacionUsuario(
            medicacion_usuario_id=med.id,
            programada_para=programada_para,
            estado="Programado",
        )
        db.session.add(metrica)
        fecha_actual += timedelta(days=1)

    try:
        db.session.commit()
        flash("Medicacion creada y tomas programadas correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al guardar la medicación: {e}", "danger")

    return redirect(url_for("meds.list_meds"))



from sqlalchemy import func  # agregá esto arriba del archivo si todavía no está
# ...
# from models import db, MedicacionUsuario, MetricaMedicacionUsuario, MedicamentoNombreEnum
# from sqlalchemy import func


@meds_bp.get("/hoy")
def meds_hoy():
    """
    Lista las medicaciones del usuario que corresponden a HOY.

    Reglas:
    - Considera solo métricas de HOY (programada_para con fecha == hoy).
    - Si la hora programada ya pasó hace más de 20 minutos y sigue en 'Programado',
      se marca como 'Omitido'.
    - Se listan solo las métricas de hoy, en estado 'Programado',
      con hora desde ahora hasta fin del día.
    """

    user_id = get_logged_user_id()
    if not user_id:
        flash("Tenés que iniciar sesión para ver tus medicaciones de hoy.", "danger")
        return redirect(url_for("login"))

    now = datetime.now()
    today = now.date()
    # Fin del día de hoy: 23:59:59
    end_of_day = datetime.combine(today, datetime(23, 59, 59))
    
    omitido_threshold = now - timedelta(minutes=20)

    # ---------- 1) Marcar como Omitido las métricas de HOY ya vencidas (>20 min pasadas) ----------
    vencidas = (
        db.session.query(MetricaMedicacionUsuario)
        .join(MedicacionUsuario, MetricaMedicacionUsuario.medicacion_usuario_id == MedicacionUsuario.id)
        .filter(
            MedicacionUsuario.usuario_id == user_id,
            func.date(MetricaMedicacionUsuario.programada_para) == today,
            MetricaMedicacionUsuario.estado == "Programado",
            MetricaMedicacionUsuario.programada_para < omitido_threshold,
        )
        .all()
    )

    for met in vencidas:
        met.estado = "Omitido"

    if vencidas:
        db.session.commit()

    # ---------- 2) Traer todas las métricas de HOY, estado 'Programado', entre now y fin del día ----------
    pendientes_hoy = (
        db.session.query(MetricaMedicacionUsuario, MedicacionUsuario)
        .join(MedicacionUsuario, MetricaMedicacionUsuario.medicacion_usuario_id == MedicacionUsuario.id)
        .filter(
            MedicacionUsuario.usuario_id == user_id,
            func.date(MetricaMedicacionUsuario.programada_para) == today,
            MetricaMedicacionUsuario.estado == "Programado",
            MetricaMedicacionUsuario.programada_para >= now,
            MetricaMedicacionUsuario.programada_para <= end_of_day,
        )
        .order_by(MetricaMedicacionUsuario.programada_para.asc())
        .all()
    )

    meds_hoy = []
    for met, med in pendientes_hoy:
        meds_hoy.append({
            "metrica_id": met.id,
            "nombre_medicamento": med.nombre_medicamento,
            "dosis": float(med.dosis) if med.dosis is not None else None,
            "unidad": med.unidad,
            "programada_para": met.programada_para,
            "instrucciones": med.instrucciones,
        })

    return render_template(
        "meds_hoy.html",
        page_title="Medicaciones de hoy",
        meds_hoy=meds_hoy,
    )

@meds_bp.post("/marcar-tomado")
def marcar_tomado():
    """
    Marca una toma de medicación como 'Tomado' en MetricaMedicacionUsuario.
    Identificamos la métrica por:
      - medicacion_usuario_id (med_id)
      - programada_para (fecha/hora exacta)
    """

    user_id = get_logged_user_id()
    if not user_id:
        flash("Tenés que iniciar sesión para registrar tomas.", "danger")
        return redirect(url_for("login"))

    
    med_id = request.form.get("med_id", type=int)
    prog_str = request.form.get("programada_para")

    if not med_id or not prog_str:
        flash("Datos incompletos para registrar la toma.", "danger")
        return redirect(request.referrer or url_for("home"))

    try:
        programada_para = datetime.fromisoformat(prog_str)
    except Exception:
        flash("No se pudo interpretar la fecha y hora de la toma.", "danger")
        return redirect(request.referrer or url_for("home"))

  
    metrica = (
        MetricaMedicacionUsuario.query
        .join(MedicacionUsuario, MetricaMedicacionUsuario.medicacion_usuario_id == MedicacionUsuario.id)
        .filter(
            MedicacionUsuario.usuario_id == user_id,
            MetricaMedicacionUsuario.medicacion_usuario_id == med_id,
            MetricaMedicacionUsuario.programada_para == programada_para,
        )
        .first()
    )

    if not metrica:
        flash("No se encontró la toma a actualizar.", "danger")
        return redirect(request.referrer or url_for("home"))

    now = datetime.now()

 
    if now <= programada_para + timedelta(minutes=20):
        metrica.estado = "Tomado"
    else:
        metrica.estado = "Tarde"

    try:
        db.session.commit()
        flash(f"Toma de {metrica.programada_para.strftime('%H:%M')} registrada correctamente.", "success")
    except Exception as e:
        db.session.rollback()
        flash(f"Error al actualizar la toma: {e}", "danger")

    return redirect(request.referrer or url_for("home"))

@meds_bp.post("/borrar/<int:med_id>")
def borrar_med(med_id):
    user_id = get_logged_user_id()
    if not user_id:
        flash("Tenés que iniciar sesión.", "danger")
        return redirect(url_for("login"))

    # Buscar la medicación
    med = MedicacionUsuario.query.filter_by(id=med_id, usuario_id=user_id).first()

    if not med:
        flash("La medicación no existe o no te pertenece.", "danger")
        return redirect(url_for("meds.list_meds"))

    # Borrar las métricas asociadas
    MetricaMedicacionUsuario.query.filter_by(medicacion_usuario_id=med.id).delete()

    # Borrar la medicación
    db.session.delete(med)
    db.session.commit()

    flash("Medicacion eliminada correctamente.", "success")
    return redirect(url_for("meds.list_meds"))


@meds_bp.get("/historial")
def historial_meds():
    """
    Muestra todas las medicaciones del usuario y todas sus tomas
    (MetricaMedicacionUsuario) con su estado.
    """

    user_id = get_logged_user_id()
    if not user_id:
        flash("Tenés que iniciar sesión para ver tu historial de medicaciones.", "danger")
        return redirect(url_for("login"))

    
    meds = (
        MedicacionUsuario.query
        .filter_by(usuario_id=user_id)
        .order_by(MedicacionUsuario.nombre_medicamento.asc())
        .all()
    )

    
    historial = []

    for med in meds:
        metricas = (
            MetricaMedicacionUsuario.query
            .filter_by(medicacion_usuario_id=med.id)
            .order_by(MetricaMedicacionUsuario.programada_para.desc())
            .all()
        )

        historial.append({
            "med": med,
            "metricas": metricas,
        })

    return render_template(
        "meds_historial.html",
        page_title="Historial de medicaciones",
        historial=historial,
    )
@meds_bp.get("/resumen")
def resumen_meds():
    """
    Muestra un resumen en gráfico de torta del estado de las tomas
    (Tomado, Tarde, Omitido, Sin estado) para el usuario actual.
    """
    user_id = get_logged_user_id()
    if not user_id:
        flash("Tenés que iniciar sesión para ver el resumen de medicaciones.", "danger")
        return redirect(url_for("login"))

   
    metricas = (
        db.session.query(MetricaMedicacionUsuario, MedicacionUsuario)
        .join(
            MedicacionUsuario,
            MetricaMedicacionUsuario.medicacion_usuario_id == MedicacionUsuario.id
        )
        .filter(MedicacionUsuario.usuario_id == user_id)
        .order_by(MetricaMedicacionUsuario.programada_para.desc())
        .all()
    )

   

    tomado_count = 0
    tarde_count = 0
    omitido_count = 0
    sin_estado_count = 0  # NULL, '', 'Programado', etc.

    for met, med in metricas:
        estado = met.estado  # puede ser None, 'Programado', 'Tomado', 'Tarde', 'Omitido', etc.

        if estado is None:
            sin_estado_count += 1
        elif isinstance(estado, str):
            est = estado.strip()
            if est == "" or est == "Programado":
                sin_estado_count += 1
            elif est == "Tomado":
                tomado_count += 1
            elif est == "Tarde":
                tarde_count += 1
            elif est == "Omitido":
                omitido_count += 1
            else:
                sin_estado_count += 1
        else:
           
            sin_estado_count += 1

    return render_template(
        "meds_resumen.html",
        page_title="Resumen de medicaciones",
        tomado_count=tomado_count,
        tarde_count=tarde_count,
        omitido_count=omitido_count,
        sin_estado_count=sin_estado_count,
    )
@meds_bp.get("/resumen/data")
def resumen_data():
    """
    Devuelve los datos del resumen de medicaciones en formato JSON,
    para que el componente pueda cargarlos mediante fetch().
    """

    user_id = get_logged_user_id()
    if not user_id:
        return {"error": "no-login"}, 401

    metricas = (
        db.session.query(MetricaMedicacionUsuario, MedicacionUsuario)
        .join(
            MedicacionUsuario,
            MetricaMedicacionUsuario.medicacion_usuario_id == MedicacionUsuario.id
        )
        .filter(MedicacionUsuario.usuario_id == user_id)
        .all()
    )

    tomado = 0
    tarde = 0
    omitido = 0
    sin_estado = 0

    for met, _ in metricas:
        estado = (met.estado or "").strip()

        if estado == "Tomado":
            tomado += 1
        elif estado == "Tarde":
            tarde += 1
        elif estado == "Omitido":
            omitido += 1
        elif estado == "" or estado == "Programado" or estado is None:
            sin_estado += 1
        else:
            sin_estado += 1

    return {
        "tomado": tomado,
        "tarde": tarde,
        "omitido": omitido,
        "sin_estado": sin_estado,
    }

