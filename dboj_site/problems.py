import os, sys, yaml
import secrets
from flask import render_template, make_response, send_from_directory, send_file, url_for, flash, redirect, request, abort
from dboj_site import app, settings, extras, bucket
from dboj_site import problem_uploading as problem_uploading
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

def in_contest(post):
    elapsed = contests.compare(post['start'], contests.current_time())
    contest_len = getLen(settings, post['mode'])
    return elapsed <= contest_len

def contest_problems(problems):
    if not current_user.is_authenticated or current_user.is_anonymous:
        return None
    contest = None
    for x in settings.find({"type":"access", "name":current_user.name}):
        if x['mode'] != 'admin' and x['mode'] != 'owner' and in_contest(x):
            contest = x['mode']
    if not contest:
        return None

    solved = []
    try:
        solved = settings.find_one({"type":"profile", "name":current_user.name})['solved']
    except:
        pass

    for problem in settings.find({"type":"problem", "contest":contest}):
        if not perms(problem, current_user.name):
            problems.append((problem['name'], problem['name'] in solved, problem['points'], ", ".join(problem['types']), ", ".join(problem['authors'])))
    problems.sort(key = cmp_to_key(cmpProblem))
    return contest

@app.route("/problems")
def problems():
    problems = []
    contest = contest_problems(problems)
    if not contest:
        problems = sorted([(x['name'], x['points'], ", ".join(x['types']), ", ".join(x['authors'])) for x in settings.find({"type":"problem", "published":True})], key = cmp_to_key(extras.cmpProblem))
    return render_template('problems.html', problems=problems, contest=contest, title="Problems")

@app.route("/problems/private")
@login_required
def private_problems():
    arr = []
    for x in settings.find({"type":"problem", "published":False}):
        if not extras.perms(x, current_user.name):
            arr.append((x['name'], x['points'], x['contest'], ", ".join(x['types']), ", ".join(x['authors'])))
    arr = sorted(arr, key = cmp_to_key(cmpProblem))
    return render_template('private_problems.html', private_problems = arr, title = "Private problems visible to " + current_user.name)

@app.route("/viewproblem/<string:problemName>")
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

    bucket.blob("TestData/" + problemName + "/resources.yaml").download_to_filename("resources.yaml")
    resources = yaml.safe_load(open("resources.yaml", "r").read())

    return render_template('view_problem.html', title="View problem " + problemName, problemName=problemName, resources=resources, src = ("\n" + src.replace("<", "%lft%").replace(">", "%rit%")))

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
    

@app.route("/raw_submission/<int:sub_id>")
def raw_submission(sub_id):
    sub = settings.find_one({"type":"submission", "id":sub_id})
    if not sub:
        abort(404)
    print(sub['output'])
    output = sub['output'].replace("diff", "").replace("`", "").replace("+ ", "  ").replace("- ", "  ").replace(" ", "%sp%").strip().replace("\n", "%nl%")
    response = make_response(output)
    response.headers.add('Access-Control-Allow-Origin', '*')
    return response

@app.route("/submission/<int:sub_id>")
@login_required
def submission(sub_id):
    sub = settings.find_one({"type":"submission", "id":sub_id})
    if not sub:
        abort(404)
    elif sub['author'] != current_user.name:
        abort(403)
    return render_template('submission.html', title="Submission " + str(sub_id), sub_problem=sub['problem'], sub_id=sub_id)
    
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

@app.route('/problems/export')
@login_required
def export():
    if not current_user.is_admin:
        abort(403)
    return render_template('export.html', title="Export problem data")

def is_busy():
    return settings.find_one({"type":"busy"})['busy']

@app.route('/problems/export', methods=['POST'])
def upload_file():
    if not current_user.is_admin:
        abort(403)
    uploaded_file = request.files['file']

    if is_busy():
        flash("An upload is in progress. Please try again in a few seconds.", "danger")
        return redirect("/problems/export")
    settings.update_one({"type":"busy"}, {"$set":{"busy":True}})
    if uploaded_file.filename != '':
        if not uploaded_file.filename.endswith(".zip"):
            flash("Error: the uploaded file does not have a .zip extention", "danger")
            settings.update_one({"type":"busy"}, {"$set":{"busy":False}})
            return redirect("/problems/export")
        os.system("rm data.zip; rm -r problemdata")
        uploaded_file.save("data.zip")
        try:
            msg = problem_uploading.uploadProblem(settings, storage.Client(), current_user.name)
            flash(msg, "success")
        except Exception as e:
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            print(exc_type, fname, exc_tb.tb_lineno)
            print(e)
            flash("An error occurred: " + str(e), "danger")
            settings.update_one({"type":"busy"}, {"$set":{"busy":False}})
            return redirect("/problems/export")
    else:
        flash("No file was selected", "danger")
        settings.update_one({"type":"busy"}, {"$set":{"busy":False}})
        return redirect("/problems/export")
    print("Done")
    settings.update_one({"type":"busy"}, {"$set":{"busy":False}})
    return redirect("/problems/export")