from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_codemirror import CodeMirror

# Databases and Storage
from pymongo import MongoClient
from google.cloud import storage
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '9791627cffb23ce1d67adcde28dbf2e6'
app.config['MAX_CONTENT_LENGTH'] = 134217728

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

settings.update_one({"type":"busy"}, {"$set":{"busy":False}})

from dboj_site import routes
