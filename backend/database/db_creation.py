from .db_connection import create_connection
from .db_connection import create_connection_voting_app

def init_db():

    conn = create_connection()
    conn.autocommit = True
    cursor = conn.cursor()

    cursor.execute("select 1 from pg_database where datname = 'voting_app';")
    exists = cursor.fetchone()

    if not exists:
        cursor.execute("create database voting_app;")
        print("Baza danych utworzona")
    else:
        print("Baza danych voting_app juz istnieje")

    cursor.close()
    conn.close()

    conn1 = create_connection_voting_app()
    cursor1 = conn1.cursor()

    def sprawdz_tabele(name):
        cursor1.execute ("select exists (select from information_schema.tables where table_schema = 'public' and table_name = %s);",
                         (name.lower(),))
        return cursor1.fetchone()[0]

    tabels = {

            "Departments": """create table if not exists Departments (
                id serial primary key,
                name varchar(100) not null
            ); """,

            "Sessions": """create table if not exists Sessions (
                id serial primary key,
                session_id varchar(100) not null,
                first_name varchar(100) not null,
                last_name varchar(100) not null,
                email varchar(100) unique not null,
                department_id integer references Departments(id) on delete set null,
                expires_at TIMESTAMP
            ); """,

            "Users": """create table if not exists Users (
                id serial primary key,
                first_name varchar(100) not null,
                last_name varchar(100) not null,
                email varchar(100) unique not null,
                password varchar(100) not null,
                department_id integer references Departments(id) on delete set null,
                role varchar(20) default 'student',
                signup_date timestamp default now()
            ); """,

            "Elections": """create table if not exists Elections (
                id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                name varchar(100) not null,
                department_id integer references Departments(id) on delete cascade,
                start_date timestamp not null,
                end_date timestamp not null,
                max_votes_per_person integer not null,
                public_key JSONB not null,
                private_key JSONB not null,
                created_at timestamp default now()
            ); """,

            "Candidates": """create table if not exists Candidates (
                id serial primary key,
                first_name varchar(100) not null,
                last_name varchar(100) not null,
                election_id UUID references Elections(id) on delete cascade,
                photo_path text,
                list_order integer
            ); """,

            "Ballots": """create table if not exists Ballots (
                id serial primary key,
                election_id UUID references Elections(id) on delete cascade,
                encrypted_votes_list JSONB not null,
                voted_date timestamp default now()
            ); """,

            "Votes_casted": """create table if not exists Votes_casted (
                id serial primary key,
                user_id integer references Users(id) on delete cascade,
                election_id UUID references Elections(id) on delete cascade,
                voting_date timestamp default now(),
                UNIQUE (user_id, election_id)
            ); """,

            "Results": """create table if not exists Results (
                id serial primary key,
                election_id UUID references Elections(id) on delete cascade,
                user_id integer references Users(id) on delete cascade,
                votes integer not null,
                date_of_count timestamp default now()
            ); """,

    }

    for name, sql in tabels.items():
        if sprawdz_tabele(name):
            print(f"Tabela {name} juz isnieje")
        else:
            cursor1.execute(sql)
            print(f"Tabela {name} utworzona")

# """create table if not exists Departments (
#     id serial primary key,
#     name varchar(100) not null
# )
# create table if not exists Users (
#     id serial primary key,
#     first_name varchar(100) not null,
#     last_name varchar(100) not null,
#     email varchar(100) unique not null,
#     password varchar(100) not null,
#     department_id integer references Departments(id) on delete set null,
#     role varchar(20) default 'student',
#     signup_date timestamp default now()
# )
# create table if not exists Elections (
#     id serial primary key,
#     name varchar(100) not null,
#     department_id integer references Departments(id) on delete cascade,
#     start_date timestamp not null,
#     end_date timestamp not null,
#     public_key JSONB not null,
 #     private_key JSONB not null
# )
# create table if not exists Candidates (
#     id serial primary key,
#     first_name varchar(100) not null,
#     last_name varchar(100) not null,
#     election_id integer references Elections(id) on delete cascade,
#     photo_path text,
#     list_order integer
# )
 # create table if not exists Ballots (
#     id serial primary key,
#     election_id integer references Elections(id) on delete cascade,
#     encrypted_votes_list JSONB not null,
#     voted_date timestamp default now()
# )
# create table if not exists Votes_casted (
#     id serial primary key,
#     user_id integer references Users(id) on delete cascade,
#     election_id integer references Elections(id) on delete cascade,
#     voting_date timestamp default now(),
#     UNIQUE (user_id, election_id)
# );

# """

    conn1.commit()
    cursor1.close()
    conn1.close()
    print("Tabele zostaly utworzone")

if __name__ == "__main__":
    init_db()