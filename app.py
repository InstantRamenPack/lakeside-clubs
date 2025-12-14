from flask import Flask, g

import db
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