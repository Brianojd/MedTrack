from flask import Blueprint, render_template
from data.models import db, MetricaSaludUsuario

metrics_bp = Blueprint("metrics", __name__, url_prefix="/metrics")

@metrics_bp.get("/")
def metrics_home():
    return render_template("metrics_home.html")
