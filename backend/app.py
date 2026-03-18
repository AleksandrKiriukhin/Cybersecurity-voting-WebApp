from flask import Flask, request, render_template, jsonify, redirect, url_for, session, flash, g, make_response, has_request_context, abort
from flask_cors import CORS
from auth.register import dodaj_usera
from auth.login import login_user
from database.db_connection import create_connection_voting_app, initialize_db_pools, release_connection, load_db_secrets
import re
import time
from datetime import timedelta
from functools import wraps
import uuid
from datetime import datetime, timedelta, timezone
import os, json
from werkzeug.utils import secure_filename
from typing import Tuple
from encryption.paillier import generujKlucze, losoweR, szyfruj, deszsyfruj
from voting.vote_manager import dodajGlos
from datetime import date
import shutil
from cryptography.fernet import Fernet
from dotenv import load_dotenv
from utils.crypto_utils import encrypt_obj, decrypt_obj
from utils.recaptcha import verify_recaptcha
import locale
import bcrypt
from auth.limits import check_block, add_fail, reset
from flask_wtf import CSRFProtect
import secrets

TESTING_MODE = os.getenv('TESTING_MODE', 'False') == 'True'

load_dotenv()
locale.setlocale(locale.LC_TIME, "pl_PL.UTF-8")

app = Flask(__name__, template_folder='../frontend', static_folder='../frontend/static')
CORS (app, supports_credentials=True)

try:
    load_db_secrets() 
    initialize_db_pools()
except Exception as e:
    print(f"Błąd inicjalizacji baz danych: {e}")

def get_or_create_csrf_token():
    token = session.get('csrf_token')
    if not token:
        token = secrets.token_urlsafe(32)
        session['csrf_token'] = token
    return token

@app.context_processor
def inject_csrf_token():

    if TESTING_MODE:
        return {"csrf_token": ""}
    
    return {"csrf_token": get_or_create_csrf_token()}

from logging_config import init_logger, log_info
init_logger()

app.config.update(
    SESSION_COOKIE_SAMESITE=None,
    SESSION_COOKIE_SECURE=False
)



endpointy = [

    'start', 
    'register_page', 
    'register', 
    'login_page',
    'wydzialy',

    'static',


]

allowed_pics = {
    'png',
    'jpg',
    'jpeg',
}

max_mb_pic = 5

pics_folder='pics_candidates'

s = 'session_id'
logout_time = 15

app.secret_key = "jakis_tajny_klucz"  
app.permanent_session_lifetime = timedelta(minutes=logout_time)

csrf = CSRFProtect()

if TESTING_MODE:
    app.config['WTF_CSRF_ENABLED'] = False
    print("--- CSRF PROTECTION DISABLED (TESTING_MODE is True) ---")
else:
    app.config['WTF_CSRF_ENABLED'] = True
    print("--- CSRF PROTECTION ENABLED ---")



def admin_required(f):

    @wraps(f)

    def wrapper(*args, **kwargs):

        user = getattr(g, 'user', None)

        if not user or user.get('role') != 'admin':

            return ("Nie masz uprawnien!")
        
        return f(*args, **kwargs)
    
    return wrapper

@app.route('/departments')

def wydzialy():
    conn = create_connection_voting_app()
    cursor = conn.cursor()
    cursor.execute("select id, name from departments order by id;")
    wynik=cursor.fetchall()
    cursor.close()
    conn.close()

    wydzialy_lista = [{"id": row[0], "name":row[1]} for row in wynik]
    return jsonify(wydzialy_lista)

def check_pic(filename: str) -> bool:
    if not filename:
        return False
    
    if '.' not in filename:
        return False
    
    _, e = os.path.splitext(filename)
    e = e.lower().lstrip('.')

    if e in allowed_pics:
        log_info(f"Format zdjecia wgranego jest {e} i pasuje")
        return True
    else:
        log_info(f"Format zdjecia wgranego jest {e} i nie pasuje")
        return False

def check_pic_size (file_Storage, max_mb: int = max_mb_pic) -> Tuple[bool, float]:
    
    file_stream = file_Storage.stream
    file_stream.seek(0, os.SEEK_END)
    size_bytes = file_stream.tell()
    file_stream.seek(0)
    size_mb = size_bytes / (1024 * 1024)
    return (size_mb <= max_mb, size_mb)

@app.route('/start', methods=['GET'])
def start():    

    user = getattr(g, 'user', None)

    print(f'{user}')

    if user:
        
        logged_in = True
        return render_template('index.html', logged_in = logged_in)
    else:
        logged_in = False
        return render_template('index.html', logged_in = logged_in)

@app.route('/register', methods=['GET'])
def register_page():
    return render_template('login-reg-pages/register.html')

@app.route('/main-page')

def main_page():

    user = getattr(g, 'user', None)
    if not isinstance(user, dict):
        
        return redirect(url_for('login_page'))

    conn = create_connection_voting_app()
    cursor = conn.cursor()

    try:

        polecenie = """select e.id, e.department_id, e.name, e.start_date, e.end_date,
        d.name as department_name, d.id as department_id
        from elections e left join departments d on e.department_id = d.id
        order by e.start_date desc"""

        cursor.execute(polecenie)
        wynik = cursor.fetchall()

        logos = {
            1: 'bmii-blue.png',
            11: 'bmii-white.png',
            2:  'noz-blue.png',
            12: 'noz-white.png',
            3:  'zip-blue.png',
            13:  'zip-white.png',
            4: 'hs-blue.png',
            14: 'hs-white.png',
            5: 'imbs-blue.png',
            15: 'imbs-white.png'
        }

        circles = {
            1: 'live-circle.png',
            2: 'ended-circle.png',
            3: 'planned_circle.png'
        }

        today = datetime.today()

        elections = []

        for w in wynik:

            election_id = w[0]
            department_id = w[1]
            name = w[2]
            start_date = w[3]
            end_date = w[4]
            department_name = w[5]

            if start_date and end_date:
                if start_date <= today <= end_date:
                    status = 'W trakcie'
                    circle = circles.get(1)
                elif today < start_date:
                    status = 'Planowane'
                    circle = circles.get(3)
                else:
                    status = 'Zakończone'
                    circle = circles.get(2)
            else:
                status = 'W trakcie'

            if department_id == user.get("department_id"):
                logo = logos.get(department_id + 10) 
            else:
                logo = logos.get(department_id)

            election = {
                "id": election_id,
                "department_id": department_id,
                "name": name,
                "start_date": start_date,
                "end_date": end_date,
                "department_name": department_name,
                "logo": logo,
                "is_unlocked": (department_id is None) or (department_id == 0),
                "status": status,
                "circle": circle
            }

            election["is_unlocked"] = (w[1] is None) or (w[1] == 0) or (w[1] == user.get("department_id"))
            elections.append(election)

        elections.sort(key=lambda x: (not x["is_unlocked"], x["start_date"]), reverse=False)

        return render_template('user-pages/main-page.html', elections=elections)
    
    finally:
        cursor.close()
        conn.close()


@app.route('/create-voting')
@admin_required
def create_voting_page():
    return render_template('user-pages/create-voting-page.html')

@app.route('/api/delete_voting/<string:election_id>', methods=['DELETE'])
@admin_required
@csrf.exempt
def delete_voting(election_id):

    conn = create_connection_voting_app()
    cursor = conn.cursor()

    try:
        cursor.execute("SELECT id FROM elections WHERE id=%s", (election_id,))
        election = cursor.fetchone()
        if not election:
            return jsonify({'success': False, 'error': 'Głosowanie nie istnieje'}), 404

        cursor.execute("DELETE FROM elections WHERE id=%s", (election_id,))
        log_info(f"Glosowanie pod id {election_id} zostalo usuniete!")
        conn.commit()

    finally:
        try:
            cursor.close()
            conn.close()
        except:
            pass

    upload_folder = os.path.join(app.static_folder, 'uploads', f'el_{election_id}')

    try:

        if os.path.exists(upload_folder):

            shutil.rmtree(upload_folder)
            app.logger.info(f"Usunięto folder: {upload_folder}")
            log_info(f"Folder glosowania pod id {election_id} zostal usuniety!")

        else:

            app.logger.info(f"Folder do usunięcia nie istnieje: {upload_folder}")
            log_info(f"Folder glosowania pod id {election_id} nie istnieje!")
            
    except Exception as e:

        app.logger.exception(f"Nie udało się usunąć folderu {upload_folder}: {e}")

        log_info(f"Folder glosowania pod id {election_id} nie zostal usuniety, bo {e}!")
        
        return jsonify({'success': True, 'warning': f'Głosowanie usunięte z bazy, ale nie udało się usunąć plików: {str(e)}'}), 200

    return jsonify({'success': True}), 200

@app.route('/api/create_Voting', methods = ['POST'])
@admin_required
@csrf.exempt
def api_create_Voting():

    print("VOTING_MASTER_KEY exists?", bool(os.environ.get("VOTING_MASTER_KEY")))
    print("app.static_folder:", app.static_folder)

    name = request.form.get('name','').strip()
    department_id = request.form.get('department_id','').strip()
    start_date = request.form.get('start_date','').strip()
    end_date = request.form.get('end_date','').strip()
    max_votes = request.form.get('max_votes_per_person','').strip()
    candidates_json = request.form.get('candidates','').strip()

    if not name:
        return jsonify(
            {
                'success': False,
                'error':'Wprowadz nazwe glosowania'
            }
            ), 400
    if not department_id:
        return jsonify(
            {
                'success': False,
                'error':'Wybierz wydzial'
            }
            ), 400
    if not start_date:
        return jsonify(
            {
                'success': False,
                'error':'Wprowadz date poczatku'
            }
            ), 400
    if not end_date:
        return jsonify(
            {
                'success': False,
                'error':'Wprowadz date konca'
            }
            ), 400
    if not candidates_json:
        return jsonify(
            {
                'success': False,
                'error':' Dodaj kandydatow'
            }
            ), 400
    
    try:
        department_id_number = int(department_id)
    except ValueError:
        return jsonify(
            {
                'success': False,
                'error':'Blad z id wydzialu '
            }
            ), 400
    
    try:
        start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
    except ValueError:
        return jsonify(
            {
                'success': False,
                'error':'Data musi byc w formacie yyyy-mm-dd '
            }
            ), 400
    
    max_votes_ = None

    if max_votes:
        try:

            max_votes_ = int(max_votes)

            if max_votes_ <= 0:
                return jsonify(
                {
                    'success': False,
                    'error':'Ilosc glosow na osobe musi byc wieksza od 0 ! '
                }
                ), 400

        except ValueError:
                
            return jsonify(
            {
                'success': False,
                'error':'Ilosc glosow musi byc liczba calkowita '
            }
            ), 400
        
    try:

        kandydaci = json.loads(candidates_json)

        if not isinstance(kandydaci, list):
            raise ValueError("Nie ma listy kandydatow")
        
    except Exception:

        return jsonify(
        {
            'success': False,
            'error':'Blad json '
        }
        ), 400
    
    for i, c in enumerate(kandydaci):

        if not isinstance(c, dict):

            return jsonify(
            {
                'success': False,
                'error': f'KAndydat musi byc obiektem {i} '
            }
            ), 400
        
        if not c.get ('first_name') or not c.get ('last_name'):
            return jsonify(
            {
                'success': False,
                'error': f'Kandydat musi miec imie i nazwisko {i+1} '
            }
            ), 400

    try:

        keys = generujKlucze(bits=16)

        public_key = {
            'n':keys['n'],
            'g':keys['g'],
        }

        private_key = {
            'lambda':keys['lambda'],
            'mi':keys['mi'],
        }

        enc_priv = encrypt_obj(private_key)

        print(f"{enc_priv}")

    except Exception as e:
        return jsonify(
        {
            'success': False,
            'error': f'Blad generowania kluczy',
            'detail' : str(e)
        }
        ), 500
    

    conn = create_connection_voting_app()
    cur = conn.cursor()

    try:

        insert_sql = """insert into elections (name, department_id, start_date, end_date, max_votes_per_person, public_key, private_key, created_at)
        values (%s, %s, %s, %s, %s, %s, %s, NOW())
        returning id;"""

        cur.execute(insert_sql ,
        (
            name,
            department_id,
            start_date,
            end_date,
            max_votes_,
            json.dumps(public_key),
            json.dumps(enc_priv)
        ))     

        results = cur.fetchone()

        if not results:
            conn.rollback()
            log_info(f"Glosowanie {results[0]} nie zostalo utworzone! Wystapil blad!")
            return jsonify(
                {
                    'success': False,
                    'error': f'Blad tworzenie glosowania'
                }
            ), 500  

        id_glosowania = results[0]  
        log_info(f"Glosowanie {results[0]} zostalo utworzone!")

        static_folder = app.static_folder
        upload_roots = os.path.join(static_folder, 'uploads')
        os.makedirs(upload_roots, exist_ok=True)

        el_folder_name = f'el_{id_glosowania}'
        el_folder_path = os.path.join(upload_roots, el_folder_name)
        os.makedirs(el_folder_path, exist_ok=True)

        insert_candidat = """insert into candidates (election_id, first_name, last_name, photo_path, list_order)
        values (%s, %s, %s, %s, %s)"""

        for order_index, cand in enumerate(kandydaci, start=1):

            first_name = str(cand.get('first_name','')).strip()
            last_name = str(cand.get('last_name','')).strip()
            photo_field = str(cand.get('photo_field','')).strip()
            photo_path_db = None

            if photo_field and photo_field in request.files:
                file_storage = request.files[photo_field]
                if file_storage and file_storage.filename:  
                    if not check_pic(file_storage.filename):
                        conn.rollback()
                        return jsonify(
                            {
                                'success': False,
                                'error': f'Typ pliku nie jest poprawny dla kandydata nr {order_index}'
                            }
                        ), 400
        
                    ok_size, size_mb = check_pic_size(file_storage, max_mb_pic)
        
                    if not ok_size:
                        conn.rollback()
                        return jsonify(
                            {
                                'success': False,
                                'error': f'Plik zdjecia dla kandydata nr {order_index} jest za duzy - {size_mb:.2f} mb ! max {max_mb_pic} mb!'
                            }
                        ), 400
        
                    safe_name = secure_filename(file_storage.filename)
                    save_name = f"{order_index}_{safe_name}"
                    save_path = os.path.join(el_folder_path, save_name)

                    file_storage.save(save_path)
                    photo_path_db = os.path.join('uploads', el_folder_name, save_name)
                    photo_path_db = photo_path_db.replace('\\', '/')
            
            cand['photo_path'] = photo_path_db

            cur.execute(insert_candidat, (
                id_glosowania,
                first_name,
                last_name,
                photo_path_db,
                order_index
            ))
        
        conn.commit()

        try:
            
            create_voting_json(id_glosowania, kandydaci, json.dumps(public_key))
            log_info(f"Kandydaci glosowania o id = {id_glosowania} zostaly zapisane do json!")
        
        except Exception as e:

            log_info(f"Kandydaci glosowania o id = {id_glosowania} nie zostaly zapisane do json, bo {e}")
            
            return jsonify({

                'success': False,
                'error': 'Nie udało się utworzyć pliku JSON z kandydatami',
                'detail': str(e)
                
            }), 500

        return jsonify(
            {
                'success': True,
                'id_glosowania': id_glosowania
            }
        ), 201    
    
    except Exception as e:
        try:
            conn.rollback()
        except Exception:
            pass
        return jsonify(
            {
                'success': False,
                'error': 'Blad serwera',
                'detail' : str(e)
            }
        ), 500  
    
    finally:

        try:
            cur.close()
        except Exception:
            pass
        try:
            conn.close()
        except Exception:
            pass

@admin_required
def create_voting_json(election_id, kandydaci, public_key_db):

    folder_path = os.path.join(app.static_folder, 'uploads', f'el_{election_id}')
    os.makedirs(folder_path, exist_ok=True)

    public_key = json.loads(public_key_db)
    n = public_key['n']
    g_ = public_key['g'] 

    candidates_data = []

    for id, k in enumerate (kandydaci, start=1):
        r = losoweR(n)
        encr_zero = szyfruj(0,r,n,g_)

        candidates_data.append(
            {
                "candidate_id": k.get('id') or id,
                "first_name": k['first_name'],
                "last_name": k['last_name'],
                "photo_path": k.get('photo_path'),
                "votes": encr_zero,
                "department_id": k.get('department_id')
            }
        )
    
    json_path = os.path.join(folder_path, 'candidates.json')
    with open (json_path, 'w', encoding='utf-8') as f:
        json.dump(candidates_data, f, ensure_ascii=False, indent=2)

    return json_path

@app.route('/thanks')
def thank_you_page():
    return render_template('user-pages/thank-you-page.html')

@app.route('/user-info')
def user_overview_page():

    if not hasattr(g, 'user'):
        return redirect(url_for('login_page'))
    
    print(f"{g.user}")

    return render_template('user-pages/user-overview-page.html', user=g.user)

@app.route('/user-votings')
@admin_required
def user_votings_page():

    user = getattr(g, 'user', None)
    if not isinstance(user, dict):
        
        return redirect(url_for('login_page'))

    conn = create_connection_voting_app()
    cursor = conn.cursor()

    conn = create_connection_voting_app()
    cursor = conn.cursor()

    try:

        polecenie = """select e.id, e.department_id, e.name, e.start_date, e.end_date,
        d.name as department_name, d.id as department_id
        from elections e left join departments d on e.department_id = d.id
        order by e.start_date desc"""

        cursor.execute(polecenie)
        wynik = cursor.fetchall()

        logos = {
            1: 'bmii-blue.png',
            2:  'noz-blue.png',
            3:  'zip-blue.png',
            4: 'hs-blue.png',
            5: 'imbs-blue.png'
        }

        circles = {
            1: 'live-circle.png',
            2: 'ended-circle.png',
            3: 'planned_circle.png'
        }

        today = datetime.today()


        elections = []

        for w in wynik:

            election_id = w[0]
            department_id = w[1]
            name = w[2]
            start_date = w[3]
            end_date = w[4]
            department_name = w[5]

            if start_date and end_date:
                if start_date <= today <= end_date:
                    status = 'W trakcie'
                    circle = circles.get(1)
                elif today < start_date:
                    status = 'Planowane'
                    circle = circles.get(3)
                else:
                    status = 'Zakończone'
                    circle = circles.get(2)
            else:
                status = 'W trakcie'

            if department_id == user.get("department_id"):
                logo = logos.get(department_id + 10) 
            else:
                logo = logos.get(department_id)

            department_id = w[1]
            logo = logos.get(department_id)

            election = {
                "id": w[0],
                "department_id": w[1],
                "name": w[2],
                "start_date": w[3],
                "end_date": w[4],
                "department_name": w[5],
                "logo": logo,
                "status": status,
                "circle" : circle
            }

            elections.append(election)

        elections.sort(key=lambda x: (x["start_date"]), reverse=False)

        return render_template('user-pages/users-votings.html', elections=elections)
    
    finally:
        cursor.close()
        conn.close()

@app.route('/vote/<string:election_id>')
def voting_page(election_id):

    user = getattr(g, 'user', None)
    if not user:
        return redirect(url_for('login_page'))

    conn = create_connection_voting_app()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT start_date, end_date, department_id
        FROM elections
        WHERE id = %s
    """, (election_id,))
    election = cursor.fetchone()
    cursor.close()
    conn.close()

    if not election:
        abort(404)

    start_date, end_date, election_department_id = election
    user_department_id = user.get('department_id')
    is_admin = user.get('role') == 'admin'
    today = datetime.today()
    formatted_date = election[1].strftime("%d.%m.%Y.")
    

    if not is_admin:
        if user_department_id != election_department_id:
            return "Nie masz uprawnień do głosowania w tym wydziale", 403
        if today > end_date:
            return "Nie możesz głosować po zakończeniu wyborów", 403
    
    conn = create_connection_voting_app()
    cursor = conn.cursor()

    polecenie = """select e.id, e.name, e.department_id, d.name as department_name, e.max_votes_per_person, e.start_date, e.end_date
    from elections e left join departments d on e.department_id = d.id
    where e.id = %s"""

    try:
        
        cursor.execute (polecenie, (election_id,))
        wynik = cursor.fetchone()

        if not wynik:
            return "Nie ma takiego glosowania", 404
        
        election_data = {
            "id": wynik[0],
            "name": wynik[1],
            "department_id":wynik[2],
            "department_name":wynik[3], 
            "max_votes_per_person": wynik[4],
            "start_date": wynik[5],
            "end_date": wynik[6]
        }

        user = getattr(g, 'user', None)
        already_voted = False
        user_id = None

        if isinstance(user, dict) and user.get('email'):
            user_email = user['email']
            cursor.execute("SELECT id FROM users WHERE email = %s", (user_email,))
            row = cursor.fetchone()
            if row:
                user_id = row[0]
                print(f"user_id: {user_id}")

                cursor.execute("SELECT 1 FROM votes_casted WHERE user_id=%s AND election_id=%s", (user_id, election_id))
                if cursor.fetchone():
                    already_voted = True

                folder_path = os.path.join(app.static_folder, 'uploads', f'el_{election_id}')
                json_path = os.path.join(folder_path, 'candidates.json')

                if not os.path.exists(json_path):
                    return "nie ma kandydatow", 404
        
                with open (json_path, 'r', encoding='utf-8') as f:
                    candidates = json.load(f)

        logos = {
            1: 'bmii-blue.png',
            2:  'noz-blue.png',
            3:  'zip-blue.png',
            4: 'hs-blue.png',
            5: 'imbs-blue.png'
        }

        logo = logos.get(election_data["department_id"])
        

        return render_template (
            'user-pages/voting-page.html',
            election = election_data,
            candidates = candidates,
            logo =logo,
            already_voted=already_voted,
            now=datetime.now(),
            dataa = formatted_date
        )

    finally:
        cursor.close()
        conn.close()

@app.route('/api/submit_vote', methods=['POST']) 
@csrf.exempt
def submit_vote():

    print("START submit_vote")
    log_info(f"Uzytkownik zaczal oddanie glosu - sprawdzenie uprawnien...")

    user = getattr(g, 'user', None)
    if not user:
        return jsonify({'success': False, 'error': 'Brak autoryzacji'}), 401

    user_email = g.user['email']

    print("user email:", user_email)

    data = request.get_json() or {}
    election_id = data.get('election_id')

    print("election id:", election_id)

    selected_candidate_ids = data.get('selected_candidate_ids', [])
    print("selected_candidate_ids:", selected_candidate_ids)

    if not isinstance(selected_candidate_ids, list):
        return jsonify ({
            'success': False,
            'error': 'nipoprawne dane'
        }), 400

    conn = create_connection_voting_app()
    cur = conn.cursor()

    cur.execute("SELECT id FROM users WHERE email=%s", (user_email,))
    row = cur.fetchone()
    if not row:
        return jsonify({'success': False, 'error': 'użytkownik nie istnieje'}), 404

    user_id = row[0]

    try:

        sprawdz_usera = """select 1 from votes_casted where user_id=%s and election_id = %s"""
        cur.execute(sprawdz_usera, (user_id, election_id,)) 
        wynik = cur.fetchone()

        if wynik:

            return jsonify ({

                'success': False,
                'error': 'glos juz byl oddany przez Ciebie!'

            }), 403
        
        klucze_ilosc_glosow = """select max_votes_per_person, public_key from elections where id=%s for update"""
        cur.execute(klucze_ilosc_glosow, (election_id,))
        row = cur.fetchone()

        if not row:
            return jsonify ({

                'success': False,
                'error': 'nie ma takiego glosowania'

            }), 404
        
        max_votes, public_key_json = row

        print("pobrane dane:", row)

        if max_votes is not None and len(selected_candidate_ids) > max_votes:
            return jsonify ({

                'success': False,
                'error': f'nie mozesz wybraz wiecej niz {max_votes} kandydatow w tym glosowaniu!'

            }), 400
        
        public_key = public_key_json

        n = int(public_key['n'])
        g_ = int(public_key['g'])

        print("n=:", n)
        print("g_=:", g_)

        lock = """SELECT pg_advisory_lock(hashtext(%s))"""

        cur.execute(lock, (election_id,))
        conn.commit()

        static_folder = app.static_folder
        json_path = os.path.join(static_folder, 'uploads', f'el_{election_id}', 'candidates.json')
        
        with open(json_path, 'r', encoding='utf-8') as f:

            candidates = json.load(f)

        selected_candidate_ids = [int(x) for x in selected_candidate_ids]

        candidate_ids = []
        zaszyfrowane_glosy = {}

        for c in candidates:

            cid = c.get('candidate_id')
            print("cid = :", cid)

            if cid is None:

                raise ValueError("brak kandydata w pliku json")
            
            cid = int(cid)

            candidate_ids.append(cid)

            try:

                zaszyfrowane_glosy[cid] = int(c['votes'])

            except (ValueError, TypeError):

                return jsonify({
                    'success': False,
                    'error': f'Niepoprawny format głosu dla kandydata {cid}',
                    'detail': str(c['votes'])
                }), 500
        
        for voted_cid in selected_candidate_ids:

            print("cid in progress", voted_cid)
            
            if voted_cid not in candidate_ids:
                print("ERROR: voted_cid not in candidate_ids")
                raise ValueError (f"kandydat z id {voted_cid} nie istnieje w pliku json")
            
            print("selected_cid:", voted_cid, "candidate_ids:", candidate_ids, "zaszyfrowane_glosy:", zaszyfrowane_glosy)
            print("n:", n, "g_:", g_)
            print("przed dodaniem")
            
            try:

                dodajGlos(voted_cid, candidate_ids, zaszyfrowane_glosy, n, g_)

            except Exception as e:

                log_info(f"Glos uzytkownika NIE zostal dodany, bo {e}")

                print("Błąd w dodajGlos:", str(e))

                raise

            # dodajGlos(voted_cid, candidate_ids, zaszyfrowane_glosy, n, g_)

        for c in candidates:

            cid = int(c['candidate_id'])

            c['votes'] = int (zaszyfrowane_glosy[cid])

        tmp_path = json_path + '.tmp'

        with open (tmp_path, 'w', encoding='utf-8') as f:

            json.dump(candidates, f, ensure_ascii=False, indent=2)

        os.replace (tmp_path, json_path)

        zapisz_vote = """insert into votes_casted (user_id, election_id, voting_date) values (%s, %s, now())"""

        cur.execute(zapisz_vote, (user_id, election_id,))

        conn.commit()

        unlock = """select pg_advisory_unlock(hashtext(%s))"""

        cur.execute(unlock, (election_id,))
        conn.commit()

        log_info(f"Glos uzytkownika zostal dodany!")

        return jsonify ({
            'success': True,
            'message': 'glos zapisany i doliczony, dziekuje!'
        }), 200
    
    except Exception as e:

        try:
            conn.rollback()
        except:
            pass
        try:
            cur.execute(unlock, (election_id,))
            conn.commit()
        except:
            pass
        return jsonify ({
            'success': False,
            'error': 'error',
            'detail' : str(e)
        }), 500
    
    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass


@app.route('/results/<string:election_id>')
def results_for_election(election_id):

    user = getattr(g, 'user', None)
    if not user:
        return redirect(url_for('login_page'))

    
    conn = create_connection_voting_app()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT start_date, end_date, department_id
        FROM elections
        WHERE id = %s
    """, (election_id,))
    election = cursor.fetchone()
    cursor.close()
    conn.close()

    if not election:
        abort(404)

    start_date, end_date, election_department_id = election
    today = datetime.today()

    
    user_department_id = user.get('department_id')
    is_admin = user.get('role') == 'admin'

    if not is_admin:

        log_info(f"Ktos, kto nie jest adminem probowal uzyskac dostep do wynikow!")
    
        if today <= end_date:
            return "Nie możesz zobaczyć wyników przed zakończeniem wyborów", 403

        
        if user_department_id != election_department_id:
            return "Nie masz uprawnień do tego głosowania", 403
    
    conn = create_connection_voting_app()
    cur = conn.cursor()

    logos = {
            1: 'bmii-blue.png',
            2:  'noz-blue.png',
            3:  'zip-blue.png',
            4: 'hs-blue.png',
            5: 'imbs-blue.png'
        }

    try:
        get_keys = """select public_key, private_key, name, department_id from elections where id=%s"""
        cur.execute(get_keys, (election_id,))
        wynik = cur.fetchone()

        if not wynik:
            return "Nie ma takiego glosowania", 404
        
        print(f"pobrane dane o glosowaniu: {wynik}")
        
        public_key_db, private_key_db, election_name, dep_id = wynik

        if isinstance(public_key_db, str):
            public_key = json.loads(public_key_db)
        else:
            public_key = public_key_db or {}

        from utils.crypto_utils import decrypt_obj
        private_key = decrypt_obj(private_key_db)

        lmbda = private_key.get('lambda')
        mi = private_key.get('mi')

        get_dep = """select name from departments where id = %s"""

        cur.execute(get_dep, (dep_id,))
        dep_wynik = cur.fetchone()

        print(f"dep name: {dep_wynik[0]}")

        department_name = dep_wynik[0] if dep_wynik else "brak"

        logo = logos.get (dep_id)

        if isinstance(public_key_db, str):
            public_key = json.loads(public_key_db) if public_key_db.strip() else {}
        else:
            public_key = public_key_db or {}

        if isinstance(private_key, str):
            private_key = json.loads(private_key) if private_key.strip() else {}
        else:
            private_key = private_key or {}

        lmbda = private_key.get('lambda')
        mi = private_key.get("mi")

        if lmbda is None or mi is None or 'n' not in public_key:
            return jsonify({
                'success' : False,
                'error' : 'Brak kluczy'
            }), 500
        
        n = int(public_key['n'])

        json_path = os.path.join(app.static_folder, 'uploads', f'el_{election_id}', 'candidates.json')

        if not os.path.exists(json_path):
            log_info(f"Deszyfrowanie glosow nie powiodlo sie, bo nie udalo sie znalezc sciezki do json kandydatow!")
            return "nie udalo sie znalezc sciezki do kandydatow json", 404
        
        with open(json_path, 'r', encoding='utf-8') as f:
            candidates_raw = json.load(f)

        candidates = []
        total_plain_votes = 0

        for c in candidates_raw:
            cid = c.get('candidate_id')
            imie = c.get('first_name')
            nazwisko = c.get('last_name')
            photo = c.get('photo_path')

            enc_votes = c.get('votes')
            try:
                enc_votes_int = int(enc_votes)
            except Exception:

                print(f"nie udalo sie przekonwertowac glosu dla {cid}: {enc_votes}")
                enc_votes_int = 0

            try:
                plain = deszsyfruj(enc_votes_int, int(lmbda), int(mi), int(n))
            except Exception as e:
                print (f"blad deszyfrowania dla {cid}: {e}")
                return jsonify ({
                    'success' : False,
                    'error': 'blad deszyfrowania',
                    'detail' : str(e)
                }), 500
        
            plain_int = int(plain)
        
            total_plain_votes += plain_int

            candidates.append ({
                'candidate_id' : cid,
                'first_name' : imie,
                'last_name': nazwisko,
                'photo_path': photo,
                'votes' : plain_int,
            })
    
        candidates.sort (key=lambda x: x['votes'], reverse=True)

        results_folder = os.path.join(app.static_folder, 'uploads', f'el_{election_id}')
        os.makedirs(results_folder, exist_ok=True)
        results_json_path = os.path.join(results_folder, 'results.json')

        try:

            with open(results_json_path, 'w', encoding='utf-8') as rf:

                json.dump({

                    'election_id': election_id,
                    'election_name': election_name,
                    'total_votes': total_plain_votes,
                    'candidates': candidates

                }, rf, ensure_ascii=False, indent=2)

            print("Zapisano wyniki do:", results_json_path)
            log_info(f"Wyniki glosowania sa zapisane w pliku!")

        except Exception as e:

            print("Nie udalo sie zapisac results.json:", e)

        return render_template (
            'user-pages/voting-results.html',
            election = {
                'id' : election_id,
                'name' : election_name,
                'department_id' : dep_id,
                'department_name': department_name
            },
            logo = logo,
            candidates = candidates,
            total_votes = total_plain_votes
        )

    finally:
        try:
            cur.close()
            conn.close()
        except:
            pass


EMAIL_WZOR = re.compile(r'^s\d{5}@student\.ubb\.edu\.pl$')
HASLO_WZOR = re.compile(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[^A-Za-z0-9]).{8,}$')

def do_login(user):
    
    session.permanent = True                
    session['user'] = user                  
    
    session['expires_at'] = (datetime.now() + timedelta(minutes=logout_time)).timestamp()

    log_info(f"Uzytkownik {user} zalogowal sie")
    
    return redirect(url_for('main_page'))

@app.route('/register', methods=['POST'])
def register():

    token = request.form.get('g-recaptcha-response', '')
    if not token:
        log_info(f"Brak recaptcha podczas rejestracji")
        return jsonify({'success': False, 'error': 'Brak recaptcha'}), 400

    resp = verify_recaptcha(token, remoteip=request.remote_addr)

    if not resp.get('success'):
        log_info(f"Niepowodzenie przy sprawdzeniu przez reCaptcha (rejestracja)")
        return jsonify({'success': False, 'error': 'Nieudana walidacja reCAPTCHA'}), 400

    first_name = request.form.get('first_name', '').strip()
    last_name = request.form.get('last_name', '').strip()
    email = request.form.get('email', '').strip()
    password = request.form.get('password', '').strip()
    department_id_raw = request.form.get('department_id', '').strip()
    
    if not first_name or not last_name or not email or not password:
        return jsonify(
            {
                'success': False, 
                'error': 'Wszystkie pola muszą być wypełnione!'
            }
            ), 400
    
    if not EMAIL_WZOR.match(email):
        return jsonify(
            {
                'success': False, 
                'error': 'Email musi być w formacie s*****@student.ubb.edu.pl'
            }
            ), 400
    
    if not HASLO_WZOR.match(password):
        return jsonify(
            {
                'success': False, 
                'error': 'Hasło musi mieć min 8 znaków, 1 dużą literę, 1 małą literę, 1 znak specjalny'
            }
            ), 400

    if not department_id_raw:
        return jsonify(
            {
                'success': False, 
                'error': 'Wybierz wydział!'
            }
            ), 400
    try:
        department_id = int(department_id_raw)
    except ValueError:
        return jsonify(
            {
                'success': False, 
                'error': 'Niepoprawne ID wydziału!'
            }
            ), 400

    # pusty_wydzial = request.form.get('department_id', '').strip()
    # if not pusty_wydzial:
    #     return render_template('login-reg-pages/register.html', error="Wybierz wydzial", form=request.form)
    
    # try:
    #     department_id = int(pusty_wydzial)
    # except ValueError:
    #     return render_template('login-reg-pages/register.html', error="Niepoprawne id wydzialu", form=request.form)

    # department_id = int(request.form['department_id'])

    user = dodaj_usera(first_name, last_name, email, password, department_id)

    if isinstance(user, dict):
        user_obj = user
    elif user is True:
        user_obj = login_user(email, password)
        if not user_obj:
            log_info(f"Uzytkownik z mailem {email} zarejestrowal sie, ale nie zostal zalogowany")
            return jsonify({'success': False, 'error': 'Utworzono konto, ale nie można się zalogować automatycznie.'}), 500
    else:
        log_info(f"Nieudana proba rejestracji z mailem {email}")
        return jsonify({'success': False, 'error': 'Rejestracja nie powiodła się'}), 400

    log_info(f"Uzytkownik z mailem {email} zarejestrowal sie!")
    log_info(f"Uzytkownik z mailem {email} zostal zalogowany!")
    session.permanent = True
    session['user'] = user_obj
    session['expires_at'] = (datetime.now() + timedelta(minutes=logout_time)).timestamp()

    return jsonify({'success': True, 'redirect': url_for('main_page')}), 200

    # if user:
        
    #     session.permanent = True
    #     session['user'] = user
    #     session['expires_at'] = (datetime.now() + timedelta(minutes=logout_time)).timestamp()

    #     return jsonify(
    #         {'success': True, 
    #          'redirect': url_for('main_page')
    #         })
    
    # else:
    #     return jsonify(
    #         {'success': False, 
    #          'error': '...'
    #         }), 400

    # if user:

    #     return redirect(url_for('main_page'))
    
    # else:

    #     # return render_template('login-reg-pages/register.html', error = "Cos poszlo nie tak! Sprobuj jeszcze raz!")
    #     return False

@app.before_request
def load_from_session():
    endpoint = request.endpoint
    user = session.get('user')

    public = {'start','login_page','register_page','register','wydzialy','static'}

    if endpoint in {'login_page','register_page','login','register'}:
        email = None
        if isinstance(user, dict):
            email = user.get('email')
        if email:
            log_info(f"Uzytkownik z mailem {email} wylogowal sie")
        # else:
        #     log_info("Uzytkownik anonimowy wylogowal sie")

        session.pop('user', None)
        session.pop('expires_at', None)
        return None

    expires_ts = session.get('expires_at')
    if user and expires_ts:
        now_ts = datetime.now().timestamp()
        if now_ts > expires_ts:
            email = user.get('email') if isinstance(user, dict) else None
            if email:
                log_info(f"Uzytkownik z mailem {email} wylogowal sie (sesja wygasla)")
            else:
                log_info("Uzytkownik anonimowy wylogowal sie (sesja wygasla)")

            session.pop('user', None)
            session.pop('expires_at', None)
            if request.path.startswith('/api/'):
                return jsonify({'success': False, 'error': 'Sesja wygasła'}), 401
            else:
                return redirect(url_for('login_page'))

    if endpoint not in public and not session.get('user'):
        if request.path.startswith('/api/'):
            return jsonify({'success': False, 'error': 'Brak autoryzacji'}), 401
        return redirect(url_for('login_page'))

    g.user = session.get('user')

    # endpoint = request.endpoint
    # print("Endpoint:", endpoint)  # debug
    # if endpoint is None:
    #     return
    
    # if endpoint in endpointy:
    #     print("Skipping session check for:", endpoint)
    #     return
    
    # session_id = request.cookies.get(s)
    # if not session_id:
    #     return redirect(url_for('login_page'))
    
    # conn = create_connection_voting_app()

    # try:

    #     cursor = conn.cursor()
    #     cursor.execute("SELECT s.session_id, s.first_name, s.last_name, s.email, s.department_id, d.id, d.name, expires_at FROM sessions s left join departments d on s.department_id = d.id WHERE s.session_id=%s", (session_id,))

    #     wynik = cursor.fetchone()

    #     if not wynik or (wynik[7] and wynik[7] < datetime.now()):

    #         cursor = conn.cursor()

    #         cursor.execute("DELETE FROM sessions WHERE session_id=%s", (session_id,))

    #         conn.commit()
    #         cursor.close()
    #         conn.close()

    #         resp = make_response(redirect(url_for('login_page')))

    #         resp.delete_cookie(s)

    #         return resp
    
    #     g.user = {
    #         "session_id": wynik[0],
    #         "first_name": wynik[1],
    #         "last_name": wynik[2],
    #         "email": wynik[3],
    #         "department_id": wynik[4],
    #         "department_name": wynik[6],
    #     }

    # finally:
    #     cursor.close()
    #     conn.close()

    # endpoint = request.endpoint
    # print(f"[BEFORE REQUEST] Endpoint: {endpoint}, g.user before setting: {getattr(g, 'user', None)}")

    # # jeśli endpoint nie wymaga logowania (np. start, login, register, static), g.user zostaje None
    # if endpoint in endpointy or endpoint is None:
    #     g.user = None
    # else:
    #     g.user = session.get('user')
    #     print(f"[BEFORE REQUEST] g.user after setting: {g.user}")

    # # API request bez użytkownika → 401
    # if request.path.startswith('/api/') and g.user is None and endpoint not in endpointy:
    #     print("[BEFORE REQUEST] API request without auth!")
    #     return jsonify({'success': False, 'error': 'Brak autoryzacji'}), 401

    # # Non-API request bez użytkownika → przekierowanie do loginu
    # if not request.path.startswith('/api/') and g.user is None and endpoint not in endpointy:
    #     print("[BEFORE REQUEST] Non-API request without auth, redirecting...")
    #     return redirect(url_for('login_page'))
    

@app.route('/login', methods=['GET', 'POST'])
def login_page():

    if request.method == 'POST':

        if not TESTING_MODE:

            token = request.form.get('g-recaptcha-response', '')
            if not token:
                log_info(f"Brak recaptcha podczas logowania")
                return jsonify({'success': False, 'error': 'Brak recaptcha'}), 400

            resp = verify_recaptcha(token, remoteip=request.remote_addr)

            if not resp.get('success'):
                log_info(f"Niepowodzenie przy sprawdzeniu przez reCaptcha (logowanie)")
                return jsonify({'success': False, 'error': 'Nieudana walidacja reCAPTCHA'}), 400

        email = request.form.get('email', '').strip()
        password = request.form.get('password', '').strip()

        if not email or not password:
            return jsonify({'success': False, 'error': 'Wszystkie pola muszą być wypełnione!'}), 400

        is_blocked, left = check_block(email)

        if is_blocked:

            return jsonify({

                'success': False,

                'error': f'Za dużo błędnych prób logowania. Spróbuj ponownie za {left} sekund.'

            }), 429

        user = login_user(email, password)  

        if user:

            reset(email)

            session['user'] = user
            session.permanent = True
            log_info(f"Uzytkownik z mailem {email} zalogowal sie")
            return jsonify({'success': True, 'redirect': url_for('main_page')})
        else:
            add_fail(email)
            log_info(f"Niudana proba logowania uzytkownika z mailem {email} !")
            return jsonify({'success': False, 'error': 'Niepoprawny email lub hasło.'}), 401
    else:
        return render_template('login-reg-pages/login.html')


    # session_id = request.cookies.get(s)
    
    # if session_id:

    #     conn = create_connection_voting_app()
    #     cursor = conn.cursor()
    #     cursor.execute("DELETE FROM sessions WHERE session_id=%s", (session_id,))
    #     conn.commit()
    #     cursor.close()
    #     conn.close()

    # resp = make_response(render_template('login-reg-pages/login.html'))

    # resp.delete_cookie(s)
    
    # if request.method == 'POST':
        
    #     email = request.form.get('email', '').strip()
    #     password = request.form.get('password', '').strip()

    #     if not email or not password:
    #         return jsonify(
    #             {
    #                 'success': False, 
    #                 'error': 'Wszystkie pola muszą być wypełnione!'
    #             }
    #         ), 400

    #     user = login_user(email, password)
    #     if not user:
    #         return jsonify(
    #             {
    #                 'success': False, 
    #                 'error': 'Niepoprawny email lub hasło.'
    #             }
    #         ), 401
        
    #     session_id = str(uuid.uuid4())
    #     expires_at = datetime.now() + timedelta(minutes=logout_time)

    #     conn = create_connection_voting_app()
    #     cursor = conn.cursor()
    #     cursor.execute(
    #         "INSERT INTO sessions (session_id, first_name, last_name, email, department_id, expires_at) "
    #         "VALUES (%s, %s, %s, %s, %s, %s)",
    #         (session_id, user['first_name'], user['last_name'], user['email'], user['department_id'], expires_at)
    #     )
    #     conn.commit()
    #     cursor.close()
    #     conn.close()

    #     # ustaw cookie i zwróć sukces
    #     resp = make_response(jsonify(
    #         {
    #             'success': True, 
    #             'redirect': url_for('main_page')
    #         }))
        
    #     resp.set_cookie(s, session_id, httponly=True)
    #     return resp
        
        # if not email or not password:
            
        #     return jsonify({'success': False, 'error': 'Wszystkie pola muszą być wypełnione!'}), 400

        # user = login_user(email, password)

        # if user:
        #     return jsonify({'success': True, 'redirect': url_for('main_page')})
        # else:
        #     return jsonify({'success': False, 'error': 'Niepoprawny email lub hasło.'}), 401

    # return render_template('login-reg-pages/login.html')

@app.route('/logout')

def logout():

    # session_id = request.cookies.get(s)
    
    # if session_id:

    #     conn = create_connection_voting_app()
    #     cursor = conn.cursor()
    #     cursor.execute("DELETE FROM sessions WHERE session_id=%s", (session_id,))
    #     conn.commit()
    #     cursor.close()
    #     conn.close()

    # resp = make_response(redirect(url_for('start')))

    # resp.delete_cookie(s)

    # return resp

    session.pop('user', None)
    log_info(f"Uzytkownik wylogowal sie")
    return redirect(url_for('start'))

@app.route('/api/change_password', methods=['POST'])
@csrf.exempt
def change_password():
    
    user = getattr(g, 'user', None)
    if not user:
        return jsonify({'success': False, 'error': 'Wymagane zalogowanie.'}), 401
    
    data = request.get_json()
    old_password = data.get('old_password')
    new_password = data.get('new_password')
    user_email = user.get('email')

    if not all([old_password, new_password]):
        return jsonify({'success': False, 'error': 'Wypełnij wszystkie pola.'}), 400

    if len(new_password) < 8:
        return jsonify({'success': False, 'error': 'Hasło musi mieć co najmniej 8 znaków, 1 specjalny i 1 liczbe', 'field': 'new_password'}), 400

    conn = None
    cur = None

    try:
        conn = create_connection_voting_app()
        cur = conn.cursor()

        cur.execute("SELECT password FROM users WHERE email = %s", (user_email,))
        user_data = cur.fetchone()

        if not user_data:
            return jsonify({'success': False, 'error': 'Użytkownik nie istnieje.'}), 404

        hashed_password = user_data[0]
        
        if isinstance(hashed_password, str):
            hashed_password = hashed_password.encode('utf-8')

        if not bcrypt.checkpw(old_password.encode('utf-8'), hashed_password):
            log_info(f"Uzytkownik z mailem {user_email} wprowadzil nieprawidlowe haslo przy zmianie hasla")
            return jsonify({'success': False, 'error': 'Nieprawidłowe aktualne hasło.', 'field': 'old_password'}), 401
        
        if old_password == new_password:
            return jsonify({'success': False, 'error': 'Nowe hasło musi być inne niż aktualne', 'field': 'new_password'}), 400

        new_hashed_password = bcrypt.hashpw(new_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

        update_query = "UPDATE users SET password = %s WHERE email = %s"
        cur.execute(update_query, (new_hashed_password, user_email))
        conn.commit()

        log_info(f"Uzytkownik z mailem {user_email} zmienil haslo!")
        return jsonify({'success': True, 'message': 'Hasło pomyślnie zmienione!'}), 200

    except Exception as e:
        if conn:
            conn.rollback()
        print(f"Błąd zmiany hasła: {e}")
        return jsonify({'success': False, 'error': 'błąd serwera.'}), 500
    
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

@app.after_request
def add_no_cache_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

if __name__ == '__main__':
    app.run(debug=True)