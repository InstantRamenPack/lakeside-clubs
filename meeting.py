from datetime import datetime, time, date as date_cls
import io

from app import client
from flask import g
import config
from db import mysql
from md_utils import render_markdown_plain, render_markdown_safe


class Meeting:
    def __init__(self, club_id, title, description, start_time = None, end_time = None, date = None, location = None, is_meeting = True, is_leader = False, meeting_id = None, post_time = None):
        self.meeting_id = meeting_id
        self.club_id = club_id
        self.title = title
        self.description = description
        self.start_time = self._parse_time(start_time)
        self.end_time = self._parse_time(end_time)
        self.date = self._parse_date(date)
        self.location = location
        self.is_meeting = bool(is_meeting)
        self.is_leader = bool(is_leader)
        self.post_time = self._parse_datetime(post_time)

    @staticmethod
    def _parse_time(value):
        if value is None or isinstance(value, time):
            return value
        if isinstance(value, str) and value:
            for fmt in ("%H:%M:%S", "%H:%M"):
                try:
                    return datetime.strptime(value, fmt).time()
                except ValueError:
                    continue
        return None

    @staticmethod
    def _parse_date(value):
        if value is None or isinstance(value, date_cls):
            return value
        if isinstance(value, str) and value:
            try:
                return datetime.strptime(value, "%Y-%m-%d").date()
            except ValueError:
                return None
        return None

    @staticmethod
    def _parse_datetime(value):
        if value is None or isinstance(value, datetime):
            return value
        if isinstance(value, str) and value:
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue
            try:
                return datetime.fromisoformat(value)
            except ValueError:
                return None
        return None

    def description_safe(self):
        return render_markdown_safe(self.description or "")

    def description_plain(self):
        return render_markdown_plain(self.description or "")

    def create(self):
        cursor = mysql.connection.cursor()
        if self.is_meeting:
            cursor.execute("""
                INSERT INTO 
                    meetings
                    (club_id, title, description, start_time, end_time, date, location, is_meeting)
                VALUES 
                    (%s, %s, %s, %s, %s, %s, %s, 1)
            """, (self.club_id, self.title, self.description, self.start_time, self.end_time, self.date, self.location))
        else:
            cursor.execute("""
                INSERT INTO 
                    meetings
                    (club_id, title, description, is_meeting)
                VALUES 
                    (%s, %s, %s, 0)
            """, (self.club_id, self.title, self.description))
        self.meeting_id = cursor.lastrowid
        created = Meeting.get(self.meeting_id)
        if created:
            created.is_leader = self.is_leader
            return created
        return self

    @staticmethod
    def all_meetings(recent = True):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT 
                m.*,
                c.name AS club_name,
                cm.user_id IS NOT NULL AS is_member
            FROM 
                meetings m
            JOIN
                clubs c ON c.club_id = m.club_id
            LEFT JOIN
                club_members cm ON cm.club_id = c.club_id AND cm.user_id = %s
            WHERE
                (%s = 0)
            OR
                (m.is_meeting = 1 AND m.date >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 DAY))
            OR
                (m.is_meeting = 0 AND m.post_time >= DATE_SUB(CURRENT_TIMESTAMP, INTERVAL 1 MONTH))
            ORDER BY
                m.is_meeting DESC,
                CASE WHEN m.is_meeting = 1 THEN m.date END ASC,
                CASE WHEN m.is_meeting = 1 THEN m.start_time END ASC,
                CASE WHEN m.is_meeting = 0 THEN m.post_time END DESC
        """, (g.user.user_id, 1 if recent else 0))
        meeting_objects = []
        for meeting in cursor.fetchall():
            m = Meeting.from_dict(meeting)
            m.club_name = meeting.get("club_name")
            m.is_member = bool(meeting.get("is_member"))
            meeting_objects.append(m)
        return meeting_objects

    @staticmethod
    def delete(meeting_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            DELETE FROM 
                meetings
            WHERE 
                meeting_id = %s
        """, (meeting_id,))
        return cursor.rowcount

    @staticmethod
    def get(meeting_id):
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT * FROM meetings WHERE meeting_id = %s
        """, (meeting_id,))
        meeting = cursor.fetchone()
        if not meeting:
            return None
        return Meeting.from_dict(meeting)

    @staticmethod
    def from_dict(meeting):
        return Meeting(
            meeting_id = meeting.get("meeting_id"),
            club_id = meeting.get("club_id"),
            title = meeting.get("title"),
            description = meeting.get("description"),
            start_time = meeting.get("start_time"),
            end_time = meeting.get("end_time"),
            date = meeting.get("date"),
            location = meeting.get("location"),
            is_meeting = meeting.get("is_meeting"),
            is_leader = meeting.get("is_leader", False),
            post_time = meeting.get("post_time")
        )
    
    def as_dict(self):
        return {
            "meeting_id": self.meeting_id,
            "club_id": self.club_id,
            "title": self.title,
            "description": self.description,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "date": self.date,
            "location": self.location,
            "is_meeting": self.is_meeting,
            "is_leader": self.is_leader,
            "post_time": self.post_time
        }

    def as_vector_store(self):
        file = io.BytesIO(self.description_plain().encode("utf-8"))
        file.name = f"meeting_{self.meeting_id}.txt"

        attributes = {
            "meeting_id": self.meeting_id,
            "club_id": self.club_id,
            "title": self.title,
            "location": self.location,
            "is_meeting": self.is_meeting
        }

        uploaded = client.files.create(
            file = file,
            purpose = "assistants"
        )

        return client.vector_stores.files.create_and_poll(
            vector_store_id = config.OPENAI_VECTOR_STORE_ID,
            file_id = uploaded.id,
            attributes = attributes
        )
