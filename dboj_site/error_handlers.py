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

@app.errorhandler(403)
def error_occurred(e):
    return render_template('403.html', title="403 Forbidden", error = True), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html', title="404 Not Found", error = True), 404


@app.errorhandler(500)
def error_occurred(e):
    return render_template('500.html', title="500 Something Went Wrong", error = True), 500

@app.errorhandler(413)
def file_upload_too_large(e):
    return render_template('413.html', title="413 File Upload Too Large", error = True), 413