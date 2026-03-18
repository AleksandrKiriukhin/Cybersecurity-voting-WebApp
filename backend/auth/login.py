from database.db_connection import create_connection_voting_app, release_connection
import bcrypt

def login_user(email, password):
    conn = create_connection_voting_app()

    try:
        cursor = conn.cursor()


        cursor.execute("select u.id, u.first_name, u.last_name, u.email, u.password, u.department_id, d.name as department_name, u.role from users u left join departments d on u.department_id = d.id where email=%s", (email,))
        user = cursor.fetchone()

        cursor.close()

        if not user:
            return None
    
        haszowane_haslo = user[4]

        if isinstance(haszowane_haslo,str):
            haszowane_haslo = haszowane_haslo.encode('utf-8')

        if bcrypt.checkpw(password.encode('utf-8'), haszowane_haslo):
            return {
                "session_id": user[0],
                "first_name": user[1],
                "last_name": user[2],
                "email": user[3],
                "department_id": user[5],
                "department_name": user[6],
                "role": user[7]
            }
        return None

        
        # conn.close()
    finally:
        release_connection(conn, "voting_app")

    # if user:
    #     haszowane_haslo = user[4].encode('utf-8')
    #     if bcrypt.checkpw(password.encode('utf-8'), haszowane_haslo):
    #         session_id = str(uuid.uuid4())
    #         response.set_cookie("session_id", session_id)

    #         conn = create_connection_voting_app()
    #         cursor = conn.cursor()

    #         cursor.execute ("insert into sessions (session_id, first_name, last_name, email, department_id) values (%s, %s, %s, %s, %s);",
    #                 (session_id, user[1], user[2], email, user[5]))

    #         conn.commit()
    #         cursor.close()
    #         conn.close()

    #         return {"id":user[0], "first_name":user[1]}
        
    #     return None

    # if not user:
    #     return None
    
    # haszowane_haslo = user[4]

    # if isinstance(haszowane_haslo,str):
    #     haszowane_haslo = haszowane_haslo.encode('utf-8')

    # if bcrypt.checkpw(password.encode('utf-8'), haszowane_haslo):
    #     return {
    #         "session_id": user[0],
    #         "first_name": user[1],
    #         "last_name": user[2],
    #         "email": user[3],
    #         "department_id": user[5],
    #         "department_name": user[6],
    #         "role": user[7]
    #     }
    # return None