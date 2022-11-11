import os
import sys
import secrets
from dboj_site import problem_uploading
from google.cloud import storage
from flask import render_template, flash, redirect, request, abort, send_from_directory
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


def cmpPost(a, b):
    return (-1 if a['id'] > b['id'] else 1)


@app.route("/")
@app.route("/home")
def home():
    posts = sorted([x for x in settings.find(
        {"type": "post"})], key=cmp_to_key(cmpPost))
    return render_template('home.html', title="Home", posts=posts)


@app.context_processor
def inject_contest_time():
    try:
        contest = get_contest()
        if not contest:
            return dict(t=None)
        else:
            return dict(t=contest['start'].split(), len=settings.find_one({"type": "contest", "name": contest['mode']})['len'], ctst=contest['mode'])
    except:
        return {}


@app.route("/favicon.ico")
def favicon():
    return send_from_directory("static", "favicon.ico")
