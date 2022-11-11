import os
import sys
import secrets
from dboj_site import problem_uploading
from google.cloud import storage
from flask import render_template, flash, redirect, request, abort
from dboj_site import app, settings, extras, bucket
from dboj_site.forms import LoginForm, UpdateAccountForm, PostForm, SubmitForm, ContestForm
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
    for x in settings.find({"type": "contest"}):
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
    contest = settings.find_one({"type": "contest", "name": contestName})
    if not contest:
        abort(404)

    inactive = ""
    try:
        date(contest['start'], contest['end'], current_time())
    except Exception as e:
        inactive = str(e)

    bucket.blob("ContestInstructions/" + contestName +
                ".txt").download_to_filename("instructions.txt")
    return render_template('view_contest.html', title="Contest " + contestName, join_contest=True, contestName=contestName, inactive=inactive, src=open("instructions.txt", "r").read().replace("\n", "%nl%").replace(" ", "%sp%"))


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
    for x in settings.find({"type": "access", "name": current_user.name}):
        if x['mode'] != 'admin' and x['mode'] != 'owner' and in_contest(x):
            contest = x
    return contest


@app.route("/contests/new")
@login_required
def set_contest():
    if not current_user.is_admin:
        abort(403)
    form = ContestForm()
    return render_template('set_contest.html', form=form)


@app.route("/contests/new", methods=['POST'])
@login_required
def submit_contest():
    if not current_user.is_admin:
        abort(403)
    form = ContestForm()
    if form.validate_on_submit():
        if not settings.find_one({"type": "contest", "name": form.name.data}) is None:
            flash("Error: A contest with this code already exists.", "danger")
            return redirect("/contests/new")

        inst = form.inst.data
        with open("instructions.txt", "w") as f:
            f.write(inst)
            f.flush()
            f.close()

        stc = storage.Client()
        blob = stc.bucket(
            "discord-bot-oj-file-storage").blob("ContestInstructions/" + form.name.data + ".txt")
        blob.upload_from_filename("instructions.txt")
        settings.insert_one({"type": "contest", "name": form.name.data, "start": form.start.data, "end": form.end.data, "problems": form.problems.data,
                            "len": form.len.data, "has-penalty": form.type.data == 'Submission Penalty', "has-time-bonus": form.type.data == 'Time Bonus'})
        flash(f"Successfully created contest {form.name.data}", "success")
    return redirect("/contests/new")


"""
@app.route("/viewproblem/<string:problemName>/submit", methods=['GET', 'POST'])
@login_required
def submit(problemName):
    problem = settings.find_one({"type":"problem", "name":problemName})
    if problem is None:
        abort(404)
    elif (not problem['published'] and (not current_user.is_authenticated or current_user.is_anonymous or (perms(problem, current_user.name)))):
        abort(403)

    form = SubmitForm()
    if form.validate_on_submit():
        sub_cnt = settings.find_one({"type":"sub_cnt"})['cnt']
        settings.update_one({"type":"sub_cnt"}, {"$inc":{"cnt":1}})
        
        lang = form.lang.data
        src = form.src.data
        settings.insert_one({"type":"submission", "problem":problemName, "author":current_user.name, "lang":lang, "message":src, "id":sub_cnt, "output":""})        

        judges = settings.find_one({"type":"judge", "status":0})
        if judges is None:
            flash("All of the judge's grading servers are currently offline or in use. Please resubmit in a few seconds.", "danger")
            return redirect("/viewproblem/" + problemName + "/submit")

        manager = Manager()
        return_dict = manager.dict()
        rpc = Process(target = runSubmission, args = (judges, current_user.name, src, lang, problemName, False, return_dict, sub_cnt,))
        rpc.start()

        return redirect('/submission/' + str(sub_cnt))
    return render_template('submit.html', title='Submit to ' + problemName,
                        form=form, pn = problemName, user = current_user, sub_problem=problemName)"""
