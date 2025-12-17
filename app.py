import json
from functools import wraps

from flask import Flask, g, render_template, request

import db
from db import mysql
from user import User
import algorithm

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
        if not g.user.authenticated:
            return "Forbidden", 403
        if g.user.is_admin:
            return func(*args, **kwargs)

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
                    COUNT(*)
                FROM 
                    raymondz_club_members cm2
                WHERE 
                    cm2.club_id = c.id
            ) AS size,
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
            size DESC
    """, (g.user.user_id,))

    club_rows = cursor.fetchall()
    # club is dict with club ids as keys and club dicts as values
    clubs = {}
    lead_order = []
    joined_order = []
    other_order = []

    for club in club_rows:
        if club["tags"]:
            club["tags"] = json.loads(club["tags"])
        else:
            club["tags"] = []
            
        club_id = club["id"]
        club["club_id"] = club_id
        clubs[club_id] = club

        if club["membership_type"] == 1:
            lead_order.append(club_id)
        elif club["membership_type"] == 0:
            joined_order.append(club_id)
        else:
            other_order.append(club_id)

    if g.user.authenticated:
        other_order = [
            club_id for club_id in algorithm.recommend_club_ids(g.user.user_id)
            if club_id in other_order
        ]

    return render_template(
        "index.html.j2", 
        clubs = clubs, 
        lead_order = lead_order, 
        joined_order = joined_order, 
        other_order = other_order
    )
