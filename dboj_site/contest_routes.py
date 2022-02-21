import os, sys
import secrets
from dboj_site import problem_uploading
from google.cloud import storage
from flask import render_template, url_for, flash, redirect, request, abort
from dboj_site import app, settings, extras, bucket
from dboj_site.forms import LoginForm, UpdateAccountForm, PostForm, SubmitForm
from dboj_site.models import User
from dboj_site.judge import *
from dboj_site.contests import *
from dboj_site.problems import in_contest
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

@app.route("/contests")
def view_contests():
    contests = []
    for x in settings.find({"type":"contest"}):
        try:
            date(x['start'], x['end'], current_time())
            x['color'] = 'lightgreen'
        except Exception as e:
            if "started" in str(e):
                x['color'] = 'yellow'
            else:
                x['color'] = 'lightgray'
        contests.append(x)
    return render_template('contests.html', title="Contests", contests=contests)

@app.route("/contest/<string:contestName>")
def contest_page(contestName):
    if not settings.find_one({"type":"contest", "name":contestName}):
        abort(404)
    bucket.blob("ContestInstructions/" + contestName + ".txt").download_to_filename("instructions.txt")
    return render_template('view_contest.html', title="Contest " + contestName, join_contest = True, contestName=contestName, src = open("instructions.txt", "r").read().replace("\n", "%nl%").replace(" ", "%sp%"))

@app.route("/contest/<string:contestName>", methods=['POST'])
@login_required
def join_contest(contestName):
    try:
        msg = joinContest(settings, contestName, current_user.name)
        flash(msg, 'success')
        return redirect("/problems")
    except Exception as e:
        flash(str(e), 'danger')
        return redirect("/contest/" + contestName)

def get_contest():
    if not current_user.is_authenticated or current_user.is_anonymous:
        return None
    contest = None
    for x in settings.find({"type":"access", "name":current_user.name}):
        if x['mode'] != 'admin' and x['mode'] != 'owner' and in_contest(x):
            contest = x
    return contest

@app.route("/contests/new")
@login_required
def set_contest():
    return render_template('set_contest.html')

@app.route("/contests/new", methods = ['POST'])
@login_required
def submit_contest():
    form = ContestForm()
    if form.validate_on_submit():
        pass

