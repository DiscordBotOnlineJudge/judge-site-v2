import os, sys
import secrets
from dboj_site import problem_uploading
from google.cloud import storage
from flask import render_template, url_for, flash, redirect, request, abort
from dboj_site import app, settings, extras, bucket
from dboj_site.forms import LoginForm, UpdateAccountForm, PostForm, SubmitForm
from dboj_site.models import User
from dboj_site.problems import *
from dboj_site.accounts import *
from dboj_site.error_handlers import *
from dboj_site.announcements import *
from dboj_site.about import *
from dboj_site.contest_routes import *
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


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', title="Home", posts=[x for x in settings.find({"type":"post"})])

