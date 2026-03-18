import pytest
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from app import app
from database.db_connection import create_connection_voting_app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  
    app.config['RECAPTCHA_TESTING'] = True
    with app.test_client() as client:
        yield client


def verify_recaptcha(token, remoteip=None):

    if app.config.get("RECAPTCHA_TESTING"):
        return {"success": True}
    
def user_exists(email: str) -> bool:
    
    conn = create_connection_voting_app()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email=%s", (email,))
    found = cur.fetchone() is not None

    cur.close()
    conn.close()

    return found

def delete_user(email: str):
    
    conn = create_connection_voting_app()
    
    cur = conn.cursor()
    cur.execute("DELETE FROM users WHERE email=%s", (email,))

    conn.commit()
    cur.close()
    conn.close()

def test_rejestracja_integracyjny(client):

    test_email = "s12345@student.ubb.edu.pl"

    delete_user(test_email)

    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': test_email,
        'password': '12345678Aa@',
        'department_id': '1',
        'g-recaptcha-response': 'dummy'
    }

    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert response.get_json().get("success") is True

    assert user_exists(test_email) is True

    delete_user(test_email)

def test_rejestracja_integracyjny_hash_test(client):

    test_email = "s12345@student.ubb.edu.pl"
    test_password = '12345678Aa@'

    delete_user(test_email)

    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': test_email,
        'password': test_password,
        'department_id': '1',
        'g-recaptcha-response': 'dummy'
    }

    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert response.get_json().get("success") is True

    assert user_exists(test_email) is True

    conn = create_connection_voting_app()
    cur = conn.cursor()
    cur.execute("SELECT password FROM users WHERE email=%s", (test_email,))
    row = cur.fetchone()

    assert row is not None, "Użytkownik powinien istnieć w bazie"
    stored_hash = row[0]

    assert test_password not in stored_hash, "Hasło NIE może być w bazie jawnym tekstem!"

    assert stored_hash.startswith("$2"), "Hash powinien być w formacie bcrypt ($2b$...)"

    delete_user(test_email) 

def test_rejestracja_integracyjny_niepoprawny_mail(client):

    test_email = "ss12345@student.ubb.edu.pl"

    delete_user(test_email)

    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': test_email,
        'password': '12345678Aa@',
        'department_id': '1',
        'g-recaptcha-response': 'dummy'
    }

    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert response.get_json().get("success") is True

    assert user_exists(test_email) is True

    delete_user(test_email)

def test_rejestracja_integracyjny_niepoprawne_haslo(client):

    test_email = "s12345@student.ubb.edu.pl"

    delete_user(test_email)

    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': test_email,
        'password': '12345678',
        'department_id': '1',
        'g-recaptcha-response': 'dummy'
    }

    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert response.get_json().get("success") is True

    assert user_exists(test_email) is True

    delete_user(test_email)

def test_login_block_after_5_attempts(client):

    test_email = "s12345@student.ubb.edu.pl"
    test_password_wrong = "12345678"
    test_password_correct = "12345678Aa@"

    delete_user(test_email)

    data = {
        'first_name': 'Test',
        'last_name': 'User',
        'email': test_email,
        'password': test_password_correct,
        'department_id': '1',
        'g-recaptcha-response': 'dummy'
    }

    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert response.get_json().get("success") is True

    for i in range(6):
        response = client.post('/login', data={
            'email': test_email,
            'password': test_password_wrong,
            'g-recaptcha-response': 'dummy'
        })
        
        if i < 5:
            assert response.status_code == 401
            assert response.get_json()['success'] is False
        else:
            
            assert response.status_code == 429
            json_data = response.get_json()
            assert json_data['success'] is False
            assert 'Za dużo błędnych prób' in json_data['error']

def test_non_admin_cannot_access_create_voting(client):
    test_email = "s12346@student.ubb.edu.pl"
    test_password = "12345678Aa@"

    delete_user(test_email)

    data = {
        'first_name': 'Normal',
        'last_name': 'User',
        'email': test_email,
        'password': test_password,
        'department_id': '1',
        'g-recaptcha-response': 'dummy'
    }
    response = client.post('/register', data=data)
    assert response.status_code == 200
    assert response.get_json().get("success") is True

    response = client.post('/login', data={
        'email': test_email,
        'password': test_password,
        'g-recaptcha-response': 'dummy'
    })
    assert response.status_code == 200
    assert response.get_json().get("success") is True

    response = client.get('/create-voting')
    
    assert b"Nie masz uprawnien!" in response.data