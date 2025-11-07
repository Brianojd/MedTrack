from flask import Flask, render_template
from config import Config
from models import db
from routes import meds_bp, metrics_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    with app.app_context():
        db.create_all()  # crea medtrack.db la primera vez

    app.register_blueprint(meds_bp)
    app.register_blueprint(metrics_bp)

    @app.get("/")
    def home():
        return render_template("index.html", page_title="MedTrack", items=[])

    return app

if __name__ == "__main__":
    create_app().run(debug=True)
