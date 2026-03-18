from app import app 
import ssl
from main import init_db, static_data
import os

init_db()
static_data()

context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
context.load_cert_chain(certfile="certificates/server.crt", keyfile="certificates/server.key")

if os.getenv("TESTING") == "true":
    app.config['WTF_CSRF_ENABLED'] = False

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, ssl_context=context)
