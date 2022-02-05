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


@app.route("/")
@app.route("/home")
def home():
    return render_template('home.html', posts=[x for x in settings.find({"type":"post"})])


@app.route("/about")
def about():
    return render_template('about.html', legend = "About Discord Bot Online Judge", title='About DBOJ')


@app.route("/register")
def register():
    return render_template("register.html")


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = None
        for x in settings.find({"type":"account"}):
            if extras.check_equal(x['pswd'], form.password.data):
                user = x
                break
        if not user is None:
            login_user(User(user['name']), remember=form.remember.data)
            next_page = request.args.get('next')
            flash('Login Success!', 'success')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Login Unsuccessful. Please check your password. To create an account, use the "-register" command on the Discord bot', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    flash('Successfully logged out. See you later!', 'success')
    return redirect(url_for('home'))

@app.errorhandler(403)
def error_occurred(e):
    return render_template('403.html'), 403

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404


@app.errorhandler(500)
def error_occurred(e):
    return render_template('500.html'), 500

@app.route("/about/languages")
def languages():
    return render_template('languages.html', langs = [(x['name'], x['compl'], x['run']) for x in settings.find({"type":"lang"})])

@app.route("/problems")
def problems():
    problems = sorted([(x['name'], x['points'], x['types'], x['authors']) for x in settings.find({"type":"problem", "published":True})], key = cmp_to_key(extras.cmpProblem))
    return render_template('problems.html', problems=problems, title="Problems")

@app.route("/viewproblem/<string:problemName>", methods=['GET', 'POST'])
def viewProblem(problemName):
    problem = settings.find_one({"type":"problem", "name":problemName})
    if problem is None or (not problem['published'] and (not current_user.is_authenticated or current_user.is_anonymous or (perms(problem, current_user.name)))):
        return render_template('404.html'), 404
    storage_client = storage.Client()
    storage_client.get_bucket("discord-bot-oj-file-storage").get_blob("ProblemStatements/" + problemName + ".txt").download_to_filename("statement.md")
    src = open("statement.md", "r").read()
    return render_template('view_problem.html', problemName=problemName, src = ("\n" + src))

@app.route("/contests")
def view_contests():
    return render_template('contests.html')

@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    if current_user.is_admin:
        form = PostForm()
        if form.validate_on_submit():
            post_cnt = settings.find_one({"type":"post_cnt"})['cnt']
            settings.update_one({"type":"post_cnt"}, {"$inc":{"cnt":1}})
            settings.insert_one({"type":"post", "title":form.title.data, "content":form.content.data, "author":current_user.name, "id":post_cnt})
            
            flash('Your post has been created!', 'success')
            return redirect(url_for('home'))
        return render_template('create_post.html', title='New Site Announcement',
                            form=form, legend='New Site Announcement', user = current_user)
    else:
        return render_template('404.html'), 404


@app.route("/post/<int:post_id>")
def post(post_id):
    post = settings.find_one({"type":"post", "id":post_id})
    return render_template('post.html', title=post['title'], post=post)


@app.route("/post/<int:post_id>/update", methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = settings.find_one({"type":"post", "id":post_id})
    if post['author'] != current_user.name:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        settings.update_one({"_id":post['_id']}, {"$set":{"title":form.title.data, "content":form.content.data}})
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post['id']))
    elif request.method == 'GET':
        form.title.data = post['title']
        form.content.data = post['content']
    return render_template('create_post.html', title='Update Post',
                           form=form, legend='Update Post')


@app.route("/post/<int:post_id>/delete", methods=['POST'])
@login_required
def delete_post(post_id):
    post = settings.find_one({"type":"post", "id":post_id})
    if post['author'] != current_user.name:
        abort(403)
    settings.delete_one({"_id":post['_id']})
    flash('Your post has been deleted!', 'success')
    return redirect(url_for('home'))

@app.route("/viewproblem/<string:problemName>/submit", methods=['GET', 'POST'])
@login_required
def submit(problemName):
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
    return render_template('submit.html', title='Submit to ' + problemName,
                        form=form, legend='Submit to ' + problemName, user = current_user, sub_problem=problemName)

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
    return render_template('submission.html', sub_problem=sub['problem'], finished="COMPLETED" in sub['output'], sub_id=sub_id, output = sub['output'].replace("diff", "").replace("`", "").replace("+ ", "  ").replace("- ", "  ").replace("\n", "%nl%"))

@app.route("/submission/<int:sub_id>/source")
@login_required
def view_source(sub_id):
    sub = settings.find_one({"type":"submission", "id":sub_id})
    if not sub:
        abort(404)
    elif sub['author'] != current_user.name:
        abort(403)
    return render_template('view_source.html', sub_problem=sub['problem'], src=sub['message'], author=sub['author'])

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
    return render_template('export.html')


@app.route("/about/problem-setting")
def problem_setting_documentation():
    return render_template('problem-setting.html')