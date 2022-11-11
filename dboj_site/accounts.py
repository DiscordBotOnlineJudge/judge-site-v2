import os
import secrets
from flask import render_template, flash, redirect, request, abort
from dboj_site import app, settings, extras
from dboj_site.forms import LoginForm, UpdateAccountForm, PostForm, SubmitForm
from dboj_site.models import User
from flask_login import login_user, current_user, logout_user, login_required
from google.cloud import storage
from functools import cmp_to_key
from flaskext.markdown import Markdown
from dboj_site.judge import *
from dboj_site.extras import *
from multiprocessing import Process, Manager
from werkzeug.utils import secure_filename
md = Markdown(app,
              safe_mode=True,
              output_format='html4',
              )


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect('/home')
    form = LoginForm()
    if form.validate_on_submit():
        user = None
        for x in settings.find({"type": "account"}):
            if extras.check_equal(x['pswd'], form.password.data):
                user = x
                break
        if not user is None:
            login_user(User(user['name']), remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login Success!', 'success')
            return redirect(next_page) if next_page else redirect('/home')
        else:
            flash('Login Unsuccessful. Please check your password. To create an account, use the "-register" command on the Discord bot', 'danger')
    return render_template('login.html', title='Log In', form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash('Successfully logged out. See you later!', 'success')
    return redirect('/home')


@app.route("/register")
def register():
    return render_template("register.html", title="Register")
