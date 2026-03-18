import psycopg2
from .db_connection import create_connection_voting_app

def static_data():
    conn = create_connection_voting_app()
    cursor = conn.cursor()

    departments = [
        ("Budowy Maszyn i Informatyki",),
        ("Nauk o zdrowiu",),
        ("Zarządzania i Transportu",),
        ("Humanistyczno‑Społeczny",),
        ("Inżynierii Materiałów, Budownictwa i Środowiska",),
    ]

    for (name,) in departments:
        cursor.execute("select id from departments where name = %s", (name,))

        exists = cursor.fetchone()
        if not exists:
            cursor.execute("insert into departments (name) values (%s)", (name,))
            print(f"Wydzial {name} dodano")

        else:
            print(f"Wydzial {name} juz isnieje w bazie")

    conn.commit()
    cursor.close()
    conn.close()
    print("Dodawanie wydzialow zostalo zakonczone")

if __name__ == "__main__":
    static_data()