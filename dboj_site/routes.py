import os, sys
import secrets
from dboj_site import problem_uploading
from google.cloud import storage
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

@app.route('/export')
@login_required
def export():
    return render_template('export.html', title="Export problem data")

def is_busy():
    return settings.find_one({"type":"busy"})['busy']

@app.route('/export', methods=['POST'])
def upload_file():
    if not current_user.is_admin:
        abort(403)
    uploaded_file = request.files['file']

    if is_busy():
        flash("An upload is in progress. Please try again in a few seconds.", "danger")
        return redirect(url_for('export'))
    settings.update_one({"type":"busy"}, {"$set":{"busy":True}})
    if uploaded_file.filename != '':
        if not uploaded_file.filename.endswith(".zip"):
            flash("Error: the uploaded file does not have a .zip extention", "danger")
            settings.update_one({"type":"busy"}, {"$set":{"busy":False}})
            return redirect(url_for('export'))
        uploaded_file.save("data.zip")
        try:
            os.system("rm data.zip; rm -r problemdata")
            msg = problem_uploading.uploadProblem(settings, storage.Client(), current_user.name)
            flash(msg, "success")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(e)
            flash("An error occurred: " + str(e), "danger")
            settings.update_one({"type":"busy"}, {"$set":{"busy":False}})
            return redirect(url_for("export"))
    else:
        flash("No file was selected", "danger")
        return redirect("/export")
    print("Done")
    settings.update_one({"type":"busy"}, {"$set":{"busy":False}})
    return redirect(url_for('home'))