import os
import secrets
from flask import render_template, url_for, flash, redirect, request, abort
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

@app.route("/about")
def about():
    return render_template('about.html', legend = "About Discord Bot Online Judge", title='About DBOJ')


@app.route("/about/languages")
def languages():
    return render_template('languages.html', title="Languages", langs = [(x['name'], x['compl'], x['run']) for x in settings.find({"type":"lang"})])

@app.route("/about/problem-setting")
def problem_setting_documentation():
    return render_template('problem-setting.html', title="Problem Setting Documentation")