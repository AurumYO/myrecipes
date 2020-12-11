from flask import render_template, url_for, request, redirect, flash
from flask_login import login_user, logout_user, login_required, current_user
from . import users
from .. import db, bcrypt
from ..models import User, Post, Permission
from .forms import RegistrationForm, LoginForm, UpdateUserForm, RequestResetForm, ResetPasswordForm, UpdateUserEmail
from .utils import send_reset_email, send_confirmation_email, add_profile_pic
from recblog.content_management.decorators import permission_required


@users.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()
        if not current_user.confirmed and request.endpoint \
                and request.blueprint != 'users' \
                and request.endpoint != 'static':
            return redirect(url_for('users.unconfirmed'))


@users.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for('main.home'))
    return render_template('unconfirmed.html', user=current_user)


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


@users.route('/account', methods=["GET"])
@login_required
def account():
    user = User.query.filter_by(username=current_user.username).first_or_404()
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file )
    return render_template('account.html', user=user, image_file=image_file)


@users.route('/user_account/<string:username>', methods=["GET"])
# @login_required
def user_account(username):
    user = User.query.filter_by(username=username).first_or_404()
    image_file = url_for('static', filename='profile_pics/' + user.image_file)
    posts = user.posts.order_by(Post.date_posted.desc()).all()
    return render_template('user_account.html', user=user, image_file=image_file, posts=posts)



@users.route("/update_account/<int:user_id>", methods=["GET", "POST"])
@login_required
def update_account(user_id):
    form = UpdateUserForm()
    if form.validate_on_submit():
        if form.picture.data:
            username = current_user.username
            pic = add_profile_pic(form.picture.data, username)
            current_user.image_file = pic
        current_user.username = form.username.data
        current_user.location = form.location.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash("Your account info has been updated!", 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.location.data = current_user.location
        form.about_me.data = current_user.about_me
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('update_account.html', title='Account', image_file=image_file, form=form)


@users.route("/update_email/<int:user_id>", methods=["GET", "POST"])
@login_required
def update_email(user_id):
    form = UpdateUserEmail()
    if form.validate_on_submit():
        new_email = form.email.data
        token = current_user.generate_email_change_token(new_email)
        send_confirmation_email(new_email, 'Confirm Your new email with Recipes', 'confirm_email', user=current_user, token=token)
        current_user.email = new_email
        current_user.confirmed = False
        db.session.commit()
        flash("Your email has been change. Please check your email for further instructions!", 'success')
        return redirect(url_for('users.account'))
    elif request.method == 'GET':
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('update_email.html', title='Update Email', form=form, image_file=image_file)


@users.route("/update_email/<token>")
@login_required
def change_email(token):
    if current_user.confirm_email(token):
        db.session.commit()
        flash("You have sucessfully confirmed your new email.", 'success')
    else:
        flash("The confirmation link is expired or not valid. Please, contact site administrator via Contact Form.", 'danger')
    return redirect(url_for('main.home'))


@users.route("/user_posts/<string:username>")
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


@users.route('/confirm/<token>')
@login_required
def confirm_token(token):
    if current_user.confirmed:
        return redirect(url_for('main.home'))
    if current_user.confirm(token):
        db.session.commit()
        flash("You have confirmed your account. Welcome to the Delicious Life!", 'success')
    else:
        flash("The confirmation link is expired or not valid. Please, contact site administrator via Contact Form.")
    return redirect(url_for('main.home'))


@users.route('/confirm')
@login_required
def resend_confirmation():
    token = current_user.generate_confirmation_token()
    send_confirmation_email(current_user.email, 'Confirm Your Account', 'confirm_registration', user=current_user, token=token)
    flash("A new confirmation email has been sent to you by email. "
          "Please follow instructions from email to confirm your account.", 'success')
    return redirect(url_for('main.home'))


@users.route('/follow_user/<string:username>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.FOLLOW)
def follow_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user.', 'danger')
        return redirect(url_for('main.home'))
    if current_user.is_following_user(user):
        flash(f"You are already following {user.username}.", 'info')
        return redirect(url_for('users.user_account', username=username))
    current_user.follow_user(user)
    db.session.commit()
    flash(f"You are now following {user.username}", 'success')
    return redirect(url_for('users.user_account', username=username))


@users.route('/stop_follow_user/<string:username>', methods=['GET', 'POST'])
@login_required
@permission_required(Permission.FOLLOW)
def stop_follow_user(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user', 'danger')
        return redirect(url_for('main.home'))
    if not current_user.is_following_user(user):
        flash(f"You are not following {user.username}.", 'info')
        return redirect(url_for('users.user_account', username=username))
    current_user.stop_follow_user(user)
    db.session.commit()
    flash(f"You have stopped following {user.username} from now on.", 'info' )
    return redirect(url_for('.user_account', username=username))


@users.route('/followers/<string:username>', methods=['GET'])
@login_required
def followers(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash('Invalid user', 'danger')
        return redirect(url_for('main.home'))
    # # pagination will be implemented later
    # page = request.args.get('page', 1, type=int)
    # pagination = user.followers.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE], error_out=False)
    follows = [{'user': item.follower, 'timestamp': item.timestamp} for item in user.followers]

    return render_template('followers.html', user=user, title='Followers of', endpoint='.followers', follows=follows)

@users.route('/followed/<string:username>', methods=['GET'])
@login_required
def followed(username):
    user = User.query.filter_by(username=username).first()
    if user is None:
        flash(f'Invalid user')
        return redirect(url_for('main.home'))
    # # pagination will be implemented later
    # page = request.args.get('page', 1, type=int)
    # pagination = user.followers.paginate(page, per_page=current_app.config['FLASKY_FOLLOWERS_PER_PAGE], error_out=False)
    followed = [{'user': item.followed, 'timestamp': item.timestamp} for item in user.followed]

    return render_template('followed.html', user=user, title='Followed by', endpoint='.followed', followed=followed)

