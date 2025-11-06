from os import environ
MYSQL_HOST = environ.get('MYSQL_HOST')
MYSQL_USER = environ.get('MYSQL_USER')
MYSQL_PASSWORD = environ.get('MYSQL_PASSWORD')
MYSQL_DB = environ.get('MYSQL_DB')
MYSQL_CURSORCLASS = 'DictCursor'
GOOGLE_CLIENT_ID = environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'
SECRET_KEY = environ.get('SECRET_KEY')