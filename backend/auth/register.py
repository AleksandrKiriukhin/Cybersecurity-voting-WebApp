import bcrypt
from database.db_connection import create_connection_voting_app, release_connection


def haszowanie(password):
    salt = bcrypt.gensalt()
    haszowany = bcrypt.hashpw(password.encode('utf-8'), salt)
    return haszowany.decode('utf-8')

def dodaj_usera(first_name, last_name, email, password, department_id, role='student'):
    conn = create_connection_voting_app()
    cursor = conn.cursor()

    try:
        cursor.execute("select id from users where email = %s;", (email,))

        if cursor.fetchone():

            cursor.close()
            # conn.close()
            # release_connection(conn, "voting_app")

            print(f"Uzytkownik z poczta {email} juz istnieje w bazie")

            return False
        
        haszowane_haslo = haszowanie(password)
        cursor.execute ("insert into users (first_name, last_name, email, password, department_id, role) values (%s, %s, %s, %s, %s, %s);",
                        (first_name, last_name, email, haszowane_haslo, department_id, role))
        
        conn.commit()
        cursor.close()
        # conn.close()
        print(f"UZytkownik {first_name} {last_name}, {email} zostal dodany")
        return True
    
    finally:

        release_connection(conn, "voting_app")
        
    

def logowanie(conn, email, password):
    conn = create_connection_voting_app()
    cursor = conn.cursor()

    cursor.execute("select password from users where email = %s;", (email,))
    wynik = cursor.fetchone()

    if not wynik:
        cursor.close()
        conn.close()
        print(f"Uzytkownika z mailem {email} nie ma w bazie")
        return False
    haszowane_haslo = wynik[0]
    conn.close()

    if bcrypt.checkpw(password.encode('utf-8'), haszowane_haslo.encode('utf-8')):
        print("haslo pasuje")
        return True
    else:
        print("haslo nie pasuje")
        return False