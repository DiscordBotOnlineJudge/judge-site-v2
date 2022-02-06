import os
import secrets
from flask import render_template, url_for, flash, redirect, request, abort
from dboj_site import app, settings, extras, bucket
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


@app.route("/problems")
def problems():
    problems = sorted([(x['name'], x['points'], ", ".join(x['types']), ", ".join(x['authors'])) for x in settings.find({"type":"problem", "published":True})], key = cmp_to_key(extras.cmpProblem))
    return render_template('problems.html', problems=problems, title="Problems")

@app.route("/private-problems")
@login_required
def private_problems():
    arr = []
    for x in settings.find({"type":"problem", "published":False}):
        if not extras.perms(x, current_user.name):
            arr.append((x['name'], x['points'], x['contest'], ", ".join(x['types']), ", ".join(x['authors'])))
    arr = sorted(arr, key = cmp_to_key(cmpProblem))
    return render_template('private_problems.html', private_problems = arr, title = "Private problems visible to " + current_user.name)

@app.route("/viewproblem/<string:problemName>", methods=['GET', 'POST'])
def viewProblem(problemName):
    problem = settings.find_one({"type":"problem", "name":problemName})
    if problem is None:
        abort(404)
    elif (not problem['published'] and (not current_user.is_authenticated or current_user.is_anonymous or (perms(problem, current_user.name)))):
        abort(403)
        
    src = None
    try:
        bucket.blob("ProblemStatements/" + problemName + ".txt").download_to_filename("statement.md")
        src = open("statement.md", "r").read()
    except:
        src = "This problem does not yet have a problem statement."
    return render_template('view_problem.html', title="View problem " + problemName, problemName=problemName, src = ("\n" + src))

@app.route("/viewproblem/<string:problemName>/submit", methods=['GET', 'POST'])
@login_required
def submit(problemName):
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
            return

        manager = Manager()
        return_dict = manager.dict()
        rpc = Process(target = runSubmission, args = (judges, current_user.name, src, lang, problemName, False, return_dict, sub_cnt,))
        rpc.start()

        return redirect('/submission/' + str(sub_cnt))
    return render_template('submit.html', title='Submit to ' + problemName,
                        form=form, pn = problemName, user = current_user, sub_problem=problemName)

"""@app.route("")
def resubmit():
    form = SubmitForm()
    if form.validate_on_submit():
        sub_cnt = settings.find_one({"type":"sub_cnt"})['cnt']
        settings.update_one({"type":"sub_cnt"}, {"$inc":{"cnt":1}})
        
        lang = form.lang.data
        src = form.src.data
        settings.insert_one({"type":"submission", "problem":problemName, "author":current_user.name, "message":src, "id":sub_cnt, "output":""})        

        judges = settings.find_one({"type":"judge", "status":0})
        if judges is None:
            flash("All of the judge's grading servers are currently offline or in use. Please resubmit in a few seconds.", "danger")
            return

        manager = Manager()
        return_dict = manager.dict()
        rpc = Process(target = runSubmission, args = (judges, current_user.name, src, lang, problemName, False, return_dict, sub_cnt,))
        rpc.start()

        return redirect('/submission/' + str(sub_cnt))
    elif request.method == 'GET':

        form.lang.data = post['title']
        form.src.data = post['content']
    return render_template('submit.html', title='Submit to ' + problemName,
                        form=form, legend='Submit to ' + problemName, user = current_user, sub_problem=problemName)"""
    

@app.route("/submission/<int:sub_id>")
@login_required
def submission(sub_id):
    sub = settings.find_one({"type":"submission", "id":sub_id})
    if not sub:
        abort(404)
    elif sub['author'] != current_user.name:
        abort(403)
    return render_template('submission.html', title="Submission " + str(sub_id), sub_problem=sub['problem'], finished="COMPLETED" in sub['output'], sub_id=sub_id, output = sub['output'].replace("diff", "").replace("`", "").replace("+ ", "  ").replace("- ", "  ").replace("\n", "%nl%"))

@app.route("/viewproblem/<string:problemName>/submissions/<string:user>")
def submission_page(problemName, user):
    return render_template('submission-page.html', title="Submissions for " + problemName + " by " + user, problemName = problemName, user = user)

@app.route("/submission/<int:sub_id>/source")
@login_required
def view_source(sub_id):
    sub = settings.find_one({"type":"submission", "id":sub_id})
    if not sub:
        abort(404)
    elif sub['author'] != current_user.name:
        abort(403)
    return render_template('view_source.html', title="View source from " + str(sub_id), sub_problem=sub['problem'], lang=sub['lang'], sid=sub_id, src=sub['message'].replace("\n", "%nl%").replace(" ", "%sp%"), author=sub['author'])
