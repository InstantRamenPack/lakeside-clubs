from functools import wraps

from flask import Flask, g, request
from openai import OpenAI

import db
from club import Club
from user import User
import config

app = Flask(__name__)
app.config.from_object(config)
db.init(app)
client = OpenAI(api_key = config.OPENAI_API_KEY)

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

        club_id = request.values.get("club_id")

        if not Club.is_leader(club_id):
            return "Forbidden", 403

        return func(*args, **kwargs)
    return wrapper

import routes
