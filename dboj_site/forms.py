from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from flask_codemirror.fields import CodeMirrorField
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms import *
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from dboj_site.models import User
from dboj_site import settings

class LoginForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateAccountForm(FlaskForm):
    username = StringField('Username',
                           validators=[DataRequired(), Length(min=2, max=20)])
    email = StringField('Email',
                        validators=[DataRequired(), Email()])
    picture = FileField('Update Profile Picture', validators=[FileAllowed(['jpg', 'png'])])
    submit = SubmitField('Update')

    def validate_username(self, username):
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('That username is taken. Please choose a different one.')

    def validate_email(self, email):
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('That email is taken. Please choose a different one.')


class PostForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    content = TextAreaField('Content', validators=[DataRequired()])
    submit = SubmitField('Post')


class SubmitForm(FlaskForm):
    lang = SelectField('Language', choices = [x['name'] for x in settings.find({"type":"lang"})])
    src = CodeMirrorField('Source code', config={'lineNumbers' : 'true'})
    submit = SubmitField('Submit!')