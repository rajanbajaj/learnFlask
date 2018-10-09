from flask import render_template, redirect, request, url_for, flash
from . import auth
from flask_login import login_user, logout_user, login_required, current_user
from ..models import User
from .forms import LoginForm, RegistrationForm
from app import db
from ..email import send_email

@auth.route('/login', methods = ['GET', 'POST'])
def login():
  form = LoginForm()
  if form.validate_on_submit():
  	user = User.query.filter_by(email = form.email.data).first()
  	if user is not None and user.verify_password(form.password.data):
  		login_user(user, form.remember_me.data)
  		return redirect(request.args.get('next') or url_for('main.index'))
  	flash('Invalid username or password.')
  return render_template('login.html', form=form)

@auth.route('/logout')
@login_required
def logout():
	logout_user()
	flash('You have been logged out.')
	return redirect(url_for('main.index'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
  form = RegistrationForm()
  if form.validate_on_submit():
    user = User(email=form.email.data,username=form.username.data,password=form.password.data)
    db.session.add(user)
    db.session.commit()
    token = user.generate_confirmation_token()
    send_email(user.email, 'Confirm Your Account','auth/email/confirm', user=user, token=token)
    flash('A confirmation email has been sent to you by email.')
    flash('You can now login.')
    return redirect(url_for('main.index'))
  return render_template('auth/register.html', form=form)

#confirm a user accouunt
@auth.route('/confirm/<token>')
@login_required
def confirm(token):
  if current_user.confirmed:
    return redirect(url_for('main.index'))
  if current_user.confirm(token):
    flash('You have confirmed your account. Thanks!')
  else:
    flash('The confirmation link is invalid or has expired.')
  return redirect(url_for('main.index'))

# The before_app_request handler will intercept a request when three conditions are
# true:
# 1. A user is logged in ( current_user.is_authenticated() must return True ).
# 2. The account for the user is not confirmed.
# 3. The requested endpoint (accessible as request.endpoint ) is outside of the au‐
# thentication blueprint. Access to the authentication routes needs to be granted, as
# those are the routes that will enable the user to confirm the account or perform
# other account management functions.
@auth.before_app_request
def before_request():
  if current_user.is_authenticated \
      and not current_user.confirmed \
      and request.endpoint[:5]  != 'auth.':
    return redirect(url_for('auth.unconfirmed'))

@auth.route('/unconfirmed')
def unconfirmed():
  if current_user.is_anonymous or current_user.confirmed:
    return redirect('main.index')
  return render_template('auth/unconfirmed.html')

@auth.route('/confirm')
@login_required
def resend_confirmation():
  token = current_user.generate_confirmation_token()
  send_email(user.email, 'Confirm Your Account','auth/email/confirm', user=current_user.username, token=token)
  flash('A new confirmation email has been sent to you by email.')
  return redirect(url_for('main.index'))

@auth.before_app_request
def before_request():
  if current_user.is_authenticated:
    current_user.ping
    if not current_user.confirmed and request.endpoint[:5] != 'auth.':
      return redirect(url_for('auth.unconfirmed'))