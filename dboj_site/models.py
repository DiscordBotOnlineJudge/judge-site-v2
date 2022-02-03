from datetime import datetime
from dboj_site import login_manager
from dboj_site import settings
from flask_login import UserMixin


@login_manager.user_loader
def load_user(user_id):
    return User.get_user(ord(user_id))

class LoginUser:
    def __init__(self, name):
        self.name = name
        self.is_active = True

class User:
    def __init__(self, name):
        self.name = name
        self.is_active = True
        self.id = settings.find_one({"type":"account", "name":name})['id']
        self.is_authenticated = True
        self.is_active = True
        self.is_anonymous = False
        self.is_admin = (not settings.find_one({"type":"access", "mode":"admin", "name":name}) is None)
    
    def get_id(self):
        return chr(self.id)

    def __repr__(self):
        return f"User('{self.username}')"

    def get_user(id):
        return User(settings.find_one({"type":"account", "id":id})['name'])


"""class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"
"""