import os
import secrets
import traceback, requests # Error handling
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
from werkzeug.exceptions import HTTPException, MethodNotAllowed
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

@app.errorhandler(405)
def page_not_found(e):
    return render_template('405.html', title="405 Method Not Allowed", error = True), 405

@app.errorhandler(Exception)
def handle_exception(e):
    if isinstance(e, HTTPException) or isinstance(e, MethodNotAllowed):
        return e
    if "ERRORS_WEBHOOK" in os.environ:
        requests.post(os.environ['ERRORS_WEBHOOK'], json = {"content":f"{os.environ.get('PING_MESSAGE')}\n**Error occured in the DBOJ Online Judge website:**\n```{traceback.format_exc()}```"})
    return render_template("500.html", title="500 Something Went Wrong", e=e), 500

@app.errorhandler(413)
def file_upload_too_large(e):
    return render_template('413.html', title="413 File Upload Too Large", error = True), 413