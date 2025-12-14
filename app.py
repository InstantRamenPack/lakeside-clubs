from flask import Flask, g, render_template

import db
from db import mysql
from user import User

app = Flask(__name__)
app.config.from_pyfile('config.py')
db.init(app)

@app.before_request
def load_user():
    g.user = User.retrieve()
    if not g.user:
        g.user = User(authenticated = False)

import clubs
import meetings
import login

@app.route("/")
def index():
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT
            c.*, 
            m.membership_type
        FROM
            raymondz_clubs c
        LEFT JOIN
            raymondz_club_members m
        ON
            m.club_id = c.id
        AND
            m.user_id = %s
        ORDER BY
            m.membership_type DESC,
            c.id
    """, (g.user.user_id,))

    return render_template("index.html.j2", clubs = cursor.fetchall())