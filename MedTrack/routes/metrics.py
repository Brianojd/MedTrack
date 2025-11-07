from flask import render_template, request
from . import metrics_bp

@metrics_bp.get("/")
def list_metrics():
    return render_template("index.html", page_title="Métricas de Salud", items=[])
