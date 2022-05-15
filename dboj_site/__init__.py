from flask import Flask
from flask_login import LoginManager
from flask_codemirror import CodeMirror

# Databases and Storage
from pymongo import MongoClient
from google.cloud import storage
import os

# import .env environment variables
from dotenv import load_dotenv
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("SECRET_KEY")
app.config['MAX_CONTENT_LENGTH'] = 469762048

# Codemirror for Flask
CODEMIRROR_LANGUAGES = ['python']
app.config.from_object(__name__)
codemirror = CodeMirror(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# MongoDB Database
cluster = MongoClient("mongodb+srv://onlineuser:$" + os.getenv("PASSWORD") + "@discord-bot-online-judg.7gm4i.mongodb.net/database?retryWrites=true&w=majority")
mdb = cluster['database']
settings = mdb['settings']

# Google cloud storage
stc = storage.Client()
bucket = stc.bucket("discord-bot-oj-file-storage")

settings.update_one({"type":"busy"}, {"$set":{"busy":False}})

from dboj_site import routes
