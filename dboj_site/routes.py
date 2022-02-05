import os
import secrets
from flask import render_template, url_for, flash, redirect, request, abort
from dboj_site import app, settings, extras
from dboj_site.forms import LoginForm, UpdateAccountForm, PostForm, SubmitForm
from dboj_site.models import User
from dboj_site.problems import *
from dboj_site.accounts import *
from dboj_site.error_handlers import *
from dboj_site.announcements import *
from dboj_site.about import *
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


@app.route("/contests")
def view_contests():
    return render_template('contests.html', title="Contests")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ['zip']

@app.route('/export', methods=['GET', 'POST'])
def upload_file():
    abort(404)
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            flash('No file part', 'danger')
            return redirect(request.url)
        file = request.files['file']
        # If the user does not select a file, the browser submits an
        # empty file without a filename.
        if file.filename == '':
            flash('No selected file', 'danger')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(filename)
            return redirect(url_for('download_file', name=filename))
    return render_template('export.html', title="Export problem data")

