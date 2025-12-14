import json
from functools import wraps

from flask import Flask, g, render_template, request

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

# https://realpython.com/primer-on-python-decorators/
def authenticate_leadership(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        club_id = request.values.get("club_id") or request.values.get("id")

        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT club_id FROM raymondz_club_members
            WHERE user_id = %s AND club_id = %s AND membership_type = 1
        """, (g.user.user_id, club_id))
        club = cursor.fetchone()
        if not club:
            return "Forbidden", 403

        return func(*args, **kwargs)
    return wrapper

import clubs
import meetings
import login

@app.route("/")
def index():
    cursor = mysql.connection.cursor()
    # https://www.mysqltutorial.org/mysql-basics/mysql-subquery/
    cursor.execute("""
        SELECT
            c.*, 
            m.membership_type,
            (
                SELECT 
                    JSON_ARRAYAGG(
                        JSON_OBJECT(
                            'id', t.id,
                            'name', t.name
                        )
                    )
                FROM
                    raymondz_club_tags ct
                LEFT JOIN
                    raymondz_tags t ON t.id = ct.tag_id
                WHERE
                    ct.club_id = c.id
            ) AS tags
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

    clubs = cursor.fetchall()
    for club in clubs:
        if club["tags"]:
            club["tags"] = json.loads(club["tags"])
        else:
            club["tags"] = []

    return render_template("index.html.j2", clubs = clubs)
