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
        abort(403)


@app.route("/post/<int:post_id>")
def post(post_id):
    post = settings.find_one({"type":"post", "id":post_id})
    if not post:
        abort(404)
    return render_template('post.html', title=post['title'], post=post, specific_post = True)


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
    return render_template('create_post.html', title='Update Announcement ' + str(post_id),
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
