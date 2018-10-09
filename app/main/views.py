from datetime import datetime
from flask import render_template, session, redirect, url_for, flash, abort, request, current_app
from . import main
from .forms import PostForm, EditProfileForm, CommentForm
from .. import db
from ..models import User, Comment
from ..decorators import admin_required, permission_required
from flask_login import login_required, current_user
from ..models import Permission, Post

@main.route('/', methods=['GET', 'POST'])
def index():
	form = PostForm()
	if current_user.can(Permission.WRITE_ARTICLES) and \
		form.validate_on_submit():
		post = Post(body = form.body.data,author=current_user._get_current_object())
		db.session.add(post)
		return redirect(url_for('.index'))
	page = request.args.get('page', 1, type=int)
	pagination = Post.query.order_by(Post.timestamp.desc()).paginate(
		page, per_page=current_app.config['FLASK_POSTS_PER_PAGE'],
		error_out=False)
	posts = pagination.items

	return render_template('index.html', form=form, posts=posts, pagination=pagination)

@main.app_context_processor
def inject_permissions():
	return dict(Permission=Permission)

@main.route('/admin')
@login_required
@admin_required
def for_admins_only():
	return "For administrators!"

@main.route('/moderator')
@login_required
@permission_required(Permission.MODERATE_COMMENTS)
def for_moderators_only():
	return "For comment moderators!"

@main.route('/user/<username>')
def user(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		abort(404)
	# if(current_user==user):
	# 	user.ping()
	posts = user.posts.order_by(Post.timestamp.desc()).all()
	return render_template('user.html', user=user, posts=posts)

@main.route('/edit-profile',methods=['GET', 'POST'])
@login_required
def edit_profile():
	form = EditProfileForm()
	if form.validate_on_submit():
		current_user.name = form.name.data
		current_user.location = form.location.data
		current_user.about_me = form.about_me.data
		user = current_user
		db.session.add(user)
		flash('your profile has been updated')
		return redirect(url_for('.user', username=current_user.username))
	form.name.data = current_user.name
	form.location.data = current_user.location
	form.about_me.data = current_user.about_me
	return render_template('edit_profile.html', form=form)

@main.route('/edit-profile/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_profile_admin(id):
	user = User.query.get_or_404(id)
	form = EditProfileAdminForm(user=user)
	if form.validate_on_submit():
		user.email = form.email.data
		user.username = form.username.data
		user.confirmed = form.confirmed.data
		user.role = Role.query.get(form.role.data)
		user.name = form.name.data
		user.location = form.location.data
		user.about_me = form.about_me.data
		db.session.add(user)
		flash('The profile has been updated.')
		return redirect(url_for('.user', username=user.username))

	form.email.data = user.email
	form.username.data = user.username
	form.confirmed.data = user.confirmed
	form.role.data = user.role_id
	form.name.data = user.name
	form.location.data = user.location
	form.about_me.data = user.about_me
	return render_template('edit_profile.html', form=form, user=user)

@main.route('/post/<int:id>', methods=['POST','GET'])
def post(id):
	post = Post.query.get_or_404(id)
	form = CommentForm()
	if form.validate_on_submit():
		comment = Comment(body = form.body.data,
							post=post,
							author=current_user._get_current_object())
		db.session.add(comment)
		flash('Your comment has been published')
		return redirect(url_for('.post',id=post.id, page=-1))
	page = request.args.get('page', 1, type=int)
	if page==-1:
		page = (post.comments.count() - 1) / \
				current_app.config['FLASKY_COMMENTS_PER_PAGE'] + 1
	pagination = post.comments.order_by(Comment.timestamp.asc()).paginate(
			page, per_page=current_app.config['FLASKY_COMMENTS_PER_PAGE'],
			error_out=False)
	comments = pagination.items
	return render_template('post.html', post=post, form=form,comments=comments, pagination=pagination)

@main.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
	post = Post.query.get_or_404(id)
	if current_user != post.author and not current_user.can(Permission.ADMINISTER):
		abort(403)
	form = PostForm()
	if form.validate_on_submit():
		post.body = form.body.data
		db.session.add(post)
		flash('The post has been updated.')
		return redirect(url_for('.post', id=post.id))
	form.body.data = post.body
	return render_template('edit_post.html', form=form)

@main.route('/follow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def follow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid User.')
		return redirect(url_for('.index'))
	if current_user.is_following(user):
		flash('You are already Following this user.')
		return redirect(url_for('.user',username=username))
	current_user.follow(user)
	flash('You are now following %s.' % username)
	return redirect(url_for('.user',username=username))

@main.route('/unfollow/<username>')
@login_required
@permission_required(Permission.FOLLOW)
def unfollow(username):
	user = User.query.filter_by(username=username).first()
	if user is None:
		flash('Invalid user.')
		return redirect(url_for('.index'))
	if not current_user.is_following(user):
		flash('You are already not following this user.')
		return redirect(url_for('.user', username=username))
	current_user.unfollow(user)
	flash('You unfollowed %s' % username)
	return redirect(url_for('.user', username=username))