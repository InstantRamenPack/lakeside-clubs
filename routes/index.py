import json

from flask import g, render_template

import algorithm
from app import app
from db import mysql


@app.route("/")
def index():
    cursor = mysql.connection.cursor()
    # https://www.mysqltutorial.org/mysql-basics/mysql-subquery/
    cursor.execute("""
        SELECT
            c.*, 
            m.is_leader AS is_leader,
            m.user_id IS NOT NULL AS is_member,
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

        if club["is_leader"]:
            lead_order.append(club_id)
        elif club["is_member"]:
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
