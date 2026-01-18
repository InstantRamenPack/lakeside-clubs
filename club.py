import json

from flask import g

from db import mysql
from meeting import Meeting

class Club:
    def __init__(self, club_id, name = None, description = None, location = None, time = None, is_salt_group = False):
        self.club_id = club_id
        self.name = name
        self.description = description
        self.location = location
        self.time = time
        self.is_salt_group = bool(is_salt_group)

    @staticmethod
    def get(club_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM clubs WHERE club_id = %s
        """, (club_id,))
        club = cursor.fetchone()
        if not club:
            return None
        return Club.from_dict(club)
    
    @staticmethod
    def from_dict(club):
        return Club(
            club_id = club.get("club_id"),
            name = club.get("name"),
            description = club.get("description"),
            location = club.get("location"),
            time = club.get("time"),
            is_salt_group = club.get("is_salt_group", False)
        )

    @staticmethod
    def is_leader(club_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT club_id FROM club_members
            WHERE user_id = %s AND club_id = %s AND is_leader = 1
        """, (g.user.user_id, club_id))
        return bool(cursor.fetchone())

    @staticmethod
    def list_details(club_ids):
        if not club_ids:
            return []
        user_id = g.user.user_id
        placeholders = ", ".join(["%s"] * len(club_ids))
        cursor = mysql.connection.cursor()
        cursor.execute(f"""
            SELECT
                c.*,
                m.is_leader AS is_leader,
                m.user_id IS NOT NULL AS is_member,
                (
                    SELECT 
                        COUNT(*)
                    FROM 
                        club_members cm2
                    WHERE 
                        cm2.club_id = c.club_id
                ) AS size,
                (
                    SELECT 
                        JSON_ARRAYAGG(
                            JSON_OBJECT(
                                'tag_id', t.tag_id,
                                'name', t.name
                            )
                        )
                    FROM
                        club_tags ct
                    LEFT JOIN
                        tags t ON t.tag_id = ct.tag_id
                    WHERE
                        ct.club_id = c.club_id
                ) AS tags
            FROM
                clubs c
            LEFT JOIN
                club_members m
            ON
                m.club_id = c.club_id
            AND
                m.user_id = %s
            WHERE
                c.club_id IN ({placeholders})
        """, (user_id, *club_ids))
        clubs = []
        for club in cursor.fetchall():
            if club.get("tags"):
                club["tags"] = json.loads(club["tags"])
            else:
                club["tags"] = []
            clubs.append(club)
        return clubs

    @staticmethod
    def all_details():
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT club_id FROM clubs")
        club_ids = [row["club_id"] for row in cursor.fetchall()]
        return Club.list_details(club_ids)

    def add_members(self, user_ids):
        if not user_ids:
            return 0
        unique_ids = list(dict.fromkeys(user_ids))
        cursor = mysql.connection.cursor()
        cursor.executemany("""
            INSERT IGNORE INTO 
                club_members
                (user_id, club_id)
            VALUES
                (%s, %s)
        """, [(user_id, self.club_id) for user_id in unique_ids])
        return cursor.rowcount

    def remove_members(self, user_ids):
        if not user_ids:
            return 0
        unique_ids = list(dict.fromkeys(user_ids))
        placeholders = ", ".join(["%s"] * len(unique_ids))
        cursor = mysql.connection.cursor()
        cursor.execute(f"""
            DELETE FROM 
                club_members
            WHERE
                club_id = %s AND user_id IN ({placeholders})
        """, (self.club_id, *unique_ids))
        return cursor.rowcount

    def add_leader(self, user_id, is_leader):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE 
                club_members
            SET 
                is_leader = %s
            WHERE
                user_id = %s AND club_id = %s
        """, (1 if is_leader else 0, user_id, self.club_id))
        return cursor.rowcount

    def demote_leader(self, user_id, is_leader):
        leader_value = 1 if is_leader else 0
        cursor = mysql.connection.cursor()
        cursor.execute("""
            UPDATE 
                club_members
            SET 
                is_leader = %s
            WHERE
                user_id = %s AND club_id = %s
        """, (leader_value, user_id, self.club_id))
        return cursor.rowcount

    def leaders(self):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                u.*
            FROM 
                club_members cm
            JOIN
                users u ON u.user_id = cm.user_id
            WHERE
                cm.club_id = %s AND cm.is_leader = 1
        """, (self.club_id,))
        self.leaders = cursor.fetchall()
        return self.leaders

    def members(self):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                u.*
            FROM 
                club_members cm
            JOIN
                users u ON u.user_id = cm.user_id
            WHERE
                cm.club_id = %s AND cm.is_leader = 0
        """, (self.club_id,))
        self.members = cursor.fetchall()
        return self.members

    def meetings(self, recent):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                m.*
            FROM 
                meetings m 
            WHERE 
                m.club_id = %s
            AND
                (
                    %s = 0
                    OR
                    (
                        (m.is_meeting = 1 AND m.date >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 DAY))
                        OR
                        (m.is_meeting = 0 AND m.post_time >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 MONTH))
                    )
                )
            ORDER BY
                m.is_meeting DESC,
                CASE WHEN m.is_meeting = 1 THEN m.date END ASC,
                CASE WHEN m.is_meeting = 1 THEN m.start_time END ASC,
                CASE WHEN m.is_meeting = 0 THEN m.post_time END DESC
        """, (self.club_id, 1 if recent else 0))
        return [Meeting.from_dict(row) for row in cursor.fetchall()]

    def import_emails(self, emails):
        if not emails:
            return []
        normalized = [email.lower() for email in emails if email]
        normalized = list(dict.fromkeys(normalized))
        if not normalized:
            return []
        cursor = mysql.connection.cursor()
        cursor.execute(f"""
            INSERT IGNORE INTO 
                users (email)
            VALUES 
                {", ".join(["(%s)"] * len(normalized))}
        """, normalized)
        cursor.execute(f"""
            SELECT 
                u.*
            FROM 
                users u
            LEFT JOIN 
                club_members cm
            ON 
                cm.user_id = u.user_id AND cm.club_id = %s
            WHERE 
                u.email IN ({", ".join(["%s"] * len(normalized))}) AND cm.user_id IS NULL
        """, (self.club_id, *normalized))
        new_members = cursor.fetchall()
        if new_members:
            self.add_members([member["user_id"] for member in new_members])
        return new_members
  
    @staticmethod
    def create_tag(tag_name):
        if not tag_name:
            return None
        normalized = tag_name.strip().lower()[:16]
        if not normalized:
            return None
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT INTO 
                tags
                (name)
            VALUES
                (%s)
            ON DUPLICATE KEY UPDATE
                tag_id = LAST_INSERT_ID(tag_id)
        """, (normalized,))
        return {"tag_id": cursor.lastrowid, "name": normalized}

    def add_tag(self, tag_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            INSERT IGNORE INTO 
                club_tags
                (club_id, tag_id)
            VALUES
                (%s, %s)
        """, (self.club_id, tag_id))
        return cursor.rowcount

    def tags(self):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                t.*
            FROM
                club_tags ct
            JOIN
                tags t ON t.tag_id = ct.tag_id
            WHERE
                ct.club_id = %s
        """, (self.club_id,))
        self.tags = cursor.fetchall()
        return self.tags
