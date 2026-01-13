from os import environ

from dotenv import load_dotenv

load_dotenv()

MYSQL_HOST = environ.get('MYSQL_HOST')
MYSQL_USER = environ.get('MYSQL_USER')
MYSQL_PASSWORD = environ.get('MYSQL_PASSWORD')
MYSQL_DB = environ.get('MYSQL_DB')
MYSQL_PORT = environ.get('MYSQL_PORT')
MYSQL_CURSORCLASS = 'DictCursor'

GOOGLE_CLIENT_ID = environ.get('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = environ.get('GOOGLE_CLIENT_SECRET')
GOOGLE_DISCOVERY_URL = 'https://accounts.google.com/.well-known/openid-configuration'

SECRET_KEY = environ.get('SECRET_KEY')

OPENAI_API_KEY = environ.get('OPENAI_API_KEY')
OPENAI_VECTOR_STORE_ID = environ.get('OPENAI_VECTOR_STORE_ID')

ALLOWED_TAGS = [
    "p", "br", "hr", "pre", "code", "blockquote",
    "ul", "ol", "li", "em", "strong", "b", "i", "u",
    "h1", "h2", "h3", "h4", "h5", "h6",
    "table", "thead", "tbody", "tr", "th", "td",
    "a", "img", "del"
]
ALLOWED_ATTRS = {
    "a": ["href", "title", "rel", "target"],
    "th": ["align"], "td": ["align"],
    "code": ["class"], "pre": ["class"], "span": ["class"], "div": ["class"],
    "img": ["src", "alt", "title", "width", "height"]
}
ALLOWED_PROTOCOLS = ["http", "https", "mailto"]

MD_EXTENSIONS = [
    "extra",
    "sane_lists",
    "nl2br",
    "md_utils"
]
