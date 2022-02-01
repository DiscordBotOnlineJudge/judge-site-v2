from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager

# Databases and Storage
from pymongo import MongoClient
from google.cloud import storage
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = '9791627cffb23ce1d67adcde28dbf2e6'

login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

# Google cloud storage application credentials
os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'C:/Users/jimmy/OneDrive/Documents/GitHub/judge-site-v2/google-service-key.json'

# MongoDB Database
cluster = MongoClient("mongodb+srv://onlineuser:$" + os.getenv("PASSWORD") + "@discord-bot-online-judg.7gm4i.mongodb.net/database?retryWrites=true&w=majority")
mdb = cluster['database']
settings = mdb['settings']

from dboj_site import routes
