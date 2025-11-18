from flask import Blueprint

meds_bp = Blueprint("meds", __name__, url_prefix="/meds")
metrics_bp = Blueprint("metrics", __name__, url_prefix="/metrics")

from . import meds, metrics 
