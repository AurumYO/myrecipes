from flask import render_template, url_for, flash, redirect, request, Blueprint
from recblog import db, bcrypt
from recblog.users.forms import RegistrationForm, LoginForm, UpdateUserForm, RequestResetForm, ResetPasswordForm
from recblog.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from recblog.users.utils import add_profile_pic
from recblog.users.utils import send_reset_email, send_confirmation_email


users = Blueprint('users', __name__)

@users.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_confirmation_email(user.email, 'Confirm Your Account with Recipes', 'confirm_registration', user=user, token=token)
        flash(f'Account created for {form.username.data}! Confirmation email was send to your registered email', 'success')

        return redirect(url_for('users.login'))
    return render_template('register.html', title='Register', form=form)


@users.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('main.home'))
        else:
            flash(f'Login Unsuccessful! Please check your email and password!', 'danger')
    return render_template('login.html', title='Login', form=form)


@users.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('main.home'))


@users.route("/account", methods=["GET", "POST"])
@login_required
def account():
    form = UpdateUserForm()
    if form.validate_on_submit():
        if form.picture.data:
            username = current_user.username
            pic = add_profile_pic(form.picture.data, username)
            current_user.image_file = pic
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash("Your account info has been updated!", 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
        form.picture.data = current_user.image_file
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@users.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=8)
    return render_template('user_posts.html', posts=posts, user=user)


@users.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('users.login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@users.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token!', 'warning')
        return redirect(url_for('users.reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('users.login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@users.route('/confirm_registration_token/<token>')
@login_required
def confirm_registration_token(token):
    if current_user.confirmed:
        return redirect(url_for('main.home'))
    if current_user.confirm_user_registration(token):
        db.session.commit()
        flash("You have confirmed your account. Welcome to the Delicious Life!", 'success')
    else:
        flash("The confirmation link is expired or not valid. Please, contact site administrator via Contact Form.")
    return redirect(url_for('main.home'))


## replace with Blueprints with app.before_app_request
@users.before_app_request
def before_request():
    if current_user.is_authenticated and not current_user.confirmed and request.endpoint != 'static':
        ## add after blueprints  - and request.blueprint != 'auth' and request.endpoint != 'static':
        return redirect(url_for('users.unconfirmed'))


@users.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.home'))
    return render_template('unconfirmed.html', user=current_user)


@users.route('/confirm')
@login_required
def resend_confirmation():
    confirmation_token = current_user.generate_confirmation_token()
    send_confirmation_email(current_user.email, 'Confirm Your Account', user=current_user, token=confirmation_token)
    flash("A new confirmation email has been sent to you by email. "
          "Please follow instructions from email to confirm your account.", 'success')
    return redirect(url_for('main.home'))