import psycopg2
from cryptography.fernet import Fernet
import os, json
from psycopg2 import pool

# def create_connection():
 
#     conn = psycopg2.connect(

#     dbname="postgres", user='postgres', password='1234', host='localhost', port= '5432'
    
#     )
    

#     return conn

# def create_connection_voting_app():
 
#     conn = psycopg2.connect(

#     dbname="voting_app", user='postgres', password='1234', host='localhost', port= '5432'
    
#     )
    

#     return conn
# def load_db_secrets(path="backend/database/db_secrets.enc"):

# ---------------------
# # 2 --------------------
# ---------------------

# _DB_SECRETS_CACHE = None

# def load_db_secrets(path="database/db_secrets.enc"):

#     global _DB_SECRETS_CACHE
    
#     if _DB_SECRETS_CACHE is not None:
        
#         return _DB_SECRETS_CACHE
    
#     print("deszyfrowanie danych do polaczenia pierwszy raz")
#     try:

#         key = os.environ["CONNECTION_KEY"].encode()
#         f = Fernet(key)
#         with open(path, "rb") as fh:
#             token = fh.read()
#         data = f.decrypt(token)

#         secrets = json.loads(data)

#         _DB_SECRETS_CACHE = secrets

#         return secrets
#     except Exception as e:
        
#         print(f"blad, nie dalo sie uzyskac danych do polaczenia: {e}")
#         raise

# def create_connection(name="default"):
#     s = load_db_secrets()
#     cfg = s[name]
#     return psycopg2.connect(
#         dbname=cfg["DB_NAME"],
#         user=cfg["DB_USER"],
#         password=cfg["DB_PASS"],
#         host=cfg.get("DB_HOST", "localhost"),
#         port=cfg.get("DB_PORT", "5432")
#     )

# def create_connection_voting_app():
#     # s = load_db_secrets()
#     # cfg = s[name]
#     # return psycopg2.connect(
#     #     dbname=cfg["DB_NAME"],
#     #     user=cfg["DB_USER"],
#     #     password=cfg["DB_PASS"],
#     #     host=cfg.get("DB_HOST", "localhost"),
#     #     port=cfg.get("DB_PORT", "5432")
#     # )
#     return create_connection("voting_app")

# ---------------------
# # 3 --------------------
# ---------------------

# Globalny cache na zdeszyfrowane sekrety bazy danych
_DB_SECRETS_CACHE = None
# Globalne zmienne na pule połączeń
_VOTING_APP_POOL = None
_DEFAULT_POOL = None

def load_db_secrets(path="database/db_secrets.enc"):

    global _DB_SECRETS_CACHE
    if _DB_SECRETS_CACHE is not None:
        return _DB_SECRETS_CACHE
    
    try:
        key = os.environ["CONNECTION_KEY"].encode()
        f = Fernet(key)
        
        with open(path, "rb") as fh:
            token = fh.read()
            
        data = f.decrypt(token)
        secrets = json.loads(data)
        
        _DB_SECRETS_CACHE = secrets
        return secrets
        
    except Exception as e:
        print(f"KRYTYCZNY BŁĄD ładowania lub deszyfrowania sekretów bazy danych: {e}")
        raise


def initialize_db_pools():
    
    global _VOTING_APP_POOL, _DEFAULT_POOL
    s = load_db_secrets()

    cfg_voting = s["voting_app"]
    _VOTING_APP_POOL = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=20, 
        dbname=cfg_voting["DB_NAME"],
        user=cfg_voting["DB_USER"],
        password=cfg_voting["DB_PASS"],
        host=cfg_voting.get("DB_HOST", "localhost"),
        port=cfg_voting.get("DB_PORT", "5432")
    )

    # Konfiguracja dla 'default'
    cfg_default = s["default"]
    _DEFAULT_POOL = pool.SimpleConnectionPool(
        minconn=1,
        maxconn=10,
        dbname=cfg_default["DB_NAME"],
        user=cfg_default["DB_USER"],
        password=cfg_default["DB_PASS"],
        host=cfg_default.get("DB_HOST", "localhost"),
        port=cfg_default.get("DB_PORT", "5432")
    )
    print("Pule połączeń z bazą danych zostały pomyślnie zainicjowane.")


def create_connection(name="default"):
    
    if name == "voting_app":
        if _VOTING_APP_POOL is None:
             raise Exception("Pula połączeń 'voting_app' nie została zainicjowana.")
        return _VOTING_APP_POOL.getconn()
    elif name == "default":
        if _DEFAULT_POOL is None:
             raise Exception("Pula połączeń 'default' nie została zainicjowana.")
        return _DEFAULT_POOL.getconn()
    else:
        raise ValueError(f"Nieznana nazwa bazy danych: {name}")

def release_connection(conn, name="default"):
    
    if name == "voting_app":
        _VOTING_APP_POOL.putconn(conn)
    elif name == "default":
        _DEFAULT_POOL.putconn(conn)

def create_connection_voting_app():
    return create_connection("voting_app")

def create_connection_default():
    return create_connection("default")

