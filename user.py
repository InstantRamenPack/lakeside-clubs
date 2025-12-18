from flask import session
try:
    from db import mysql
except ImportError:
    from public.RaymondZ.finalproject.db import mysql  # type: ignore

class User:
    def __init__(self, user_id = None, google_id = None, first_name = None, last_name = None, name = None, email = None, picture = None, authenticated = True, is_admin = False):
        self.user_id = user_id
        self.google_id = google_id
        self.first_name = first_name
        self.last_name = last_name
        self.name = name
        self.email = email
        self.picture = picture
        self.authenticated = authenticated
        self.is_admin = bool(is_admin)
    
    @staticmethod
    def get(user_id):
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM raymondz_users WHERE id = %s", (user_id,))
        user_data = cursor.fetchone()

        if user_data:
            return User(
                user_id = user_data['id'],
                google_id = user_data['google_id'],
                first_name = user_data['first_name'],
                last_name = user_data['last_name'],
                name = user_data['name'],
                email = user_data['email'],
                picture = user_data['picture'],
                is_admin = user_data['is_admin']
            )
        else:
            return None
        
    @staticmethod
    def retrieve():
        if "raymondz_user" in session:
            return User(
                user_id = session["raymondz_user"].get("user_id"),
                google_id = session["raymondz_user"].get("google_id"),
                first_name = session["raymondz_user"].get("first_name"),
                last_name = session["raymondz_user"].get("last_name"),
                name = session["raymondz_user"].get("name"),
                email = session["raymondz_user"].get("email"),
                picture = session["raymondz_user"].get("picture"),
                is_admin = session["raymondz_user"].get("is_admin", False)
            )  
        else:
            return None 
    
    def init(self):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO 
                raymondz_users
                (google_id, first_name, last_name, name, email, picture)
            VALUES
                (%s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
                id = LAST_INSERT_ID(id),
                google_id = %s,
                first_name = %s,
                last_name = %s,
                name = %s,
                picture = %s
        """, (
            self.google_id, self.first_name, self.last_name, self.name, self.email, self.picture, 
            self.google_id, self.first_name, self.last_name, self.name, self.picture
        ))
        mysql.connection.commit()
        self.user_id = cursor.lastrowid

        cursor.execute("""
            SELECT is_admin FROM raymondz_users WHERE id = %s
        """, (self.user_id,)) 
        self.is_admin = bool(cursor.fetchone().get("is_admin"))

        session["raymondz_user"] = {
            "user_id": self.user_id,
            "google_id": self.google_id,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "name": self.name,
            "email": self.email,
            "picture": self.picture,
            "is_admin": self.is_admin
        }
