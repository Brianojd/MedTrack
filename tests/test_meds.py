import pytest
from app import create_app
from models import db, Usuario




@pytest.fixture
def app():

    app = create_app()
    app.config.update(
        TESTING=True,                         
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",  
    )

    with app.app_context():
       
        db.drop_all()
        db.create_all()

    
        usuario = Usuario(
            nombre="Usuario Test",
            email="test@example.com",
            form_completado=True,  
        )
        usuario.set_password("1234")
        db.session.add(usuario)
        db.session.commit()

    return app


@pytest.fixture
def client(app):
 
    return app.test_client()




def test_meds_redirige_a_login_si_no_hay_sesion(client):
 
   
    response = client.get("/meds/", follow_redirects=False)

    
    assert response.status_code == 302         
    assert "/login" in response.headers["Location"]


def test_meds_muestra_listado_si_hay_usuario_logueado(client):
    
 
   
    with client.session_transaction() as sess:
        sess["user_id"] = 1   

    
    response = client.get("/meds/")

    
    assert response.status_code == 200
    
    assert b"Medicaciones" in response.data
