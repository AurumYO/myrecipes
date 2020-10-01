import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from recblog import app, db, bcrypt, mail, admin
from recblog.forms import RegistrationForm, LoginForm, PostForm, UpdateUserForm, RequestResetForm, ResetPasswordForm
from recblog.models import User, Post, Permission
from flask_login import login_user, current_user, logout_user, login_required
from recblog.picture_handler import add_profile_pic
from recblog.utils import send_reset_email, send_confirmation_email
from flask_admin.contrib.sqla import ModelView
from recblog.decorators import admin_required, permission_required


## later replace with app.app_context_processor
@app.context_processor
def inject_permissions():
    return dict(Permission=Permission)

admin.add_view(ModelView(User, db.session))
admin.add_view(ModelView(Post, db.session))



@app.route('/')
@app.route('/home')
def home():
    # selects 3 latest posts from database for carousel
    carousel_posts = Post.query.order_by(Post.date_posted.desc())
    # latest posts section
    latest_page = request.args.get('page', 1, type=int)
    latest_posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=latest_page, per_page=4)
    cake_page = request.args.get('page', 1, type=int)
    cake_recipes = Post.query.filter_by(type_category='cake').order_by(Post.date_posted.desc()).paginate(page=cake_page, per_page=4)
    return render_template("home.html", carousel_posts=carousel_posts, latest_posts=latest_posts, cake_recipes=cake_recipes)


@app.route('/about')
def about():
    return render_template("about.html", title='About')


@app.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        token = user.generate_confirmation_token()
        send_confirmation_email(user.email, 'Confirm Your Account with Recipes', 'confirm_registration', user=user, token=token)
        flash(f'Account created for {form.username.data}! Confirmation email was send to your registered email', 'success')

        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash(f'Login Unsuccessful! Please check your email and password!', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('home'))


@app.route("/account", methods=["GET", "POST"])
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
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Account', image_file=image_file, form=form)


@app.route("/user/<string:username>")
def user_posts(username):
    page = request.args.get('page', 1, type=int)
    user = User.query.filter_by(username=username).first_or_404()
    posts = Post.query.filter_by(author=user)\
        .order_by(Post.date_posted.desc())\
        .paginate(page=page, per_page=8)
    return render_template('user_posts.html', posts=posts, user=user)


@app.route("/reset_password", methods=["GET", "POST"])
def reset_request():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('An email has been sent with instructions to reset your password.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


@app.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    user = User.verify_reset_token(token)
    if user is None:
        flash('That is an invalid or expired token!', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash('Your password has been updated! You are now able to log in.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)

@app.route('/confirm/<token>')
@login_required
def confirm_registration_token(token):
    if current_user.confirmed:
        return redirect(url_for('home'))
    if current_user.confirm_user_registration(token):
        db.session.commit()
        flash("You have confirmed your account. Welcome to the Delicious Life!", 'success')
    else:
        flash("The confirmation link is expired or not valid. Please, contact site administrator via Contact Form.")
    return redirect(url_for('home'))


## replace with Blueprints with app.before_app_request
@app.before_request
def before_request():
    if current_user.is_authenticated and not current_user.confirmed:
        ## add after blueprints  - and request.blueprint != 'auth' and request.endpoint != 'static':
        return redirect(url_for('unconfirmed'))


@app.route('/unconfirmed')
def unconfirmed():
    if current_user.is_anonymus or current_user.confirmed:
        return redirect(url_for('home'))
    return render_template('unconfirmed.html', user=current_user)


@app.route('/confirm')
@login_required
def resend_confirmation():
    confirmation_token = current_user.generate_confirmation_token()
    send_confirmation_email(current_user.email, 'Confirm Your Account', user=current_user, token=confirmation_token)
    flash("A new confirmation email has been sent to you by email. "
          "Please follow instructions from email to confirm your account.", 'success')
    return redirect(url_for('home'))



def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/post_pictures', picture_fn)

    output_size = (1540, 1540)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn




@app.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        if form.post_picture.data:
            picture_file = save_picture(form.post_picture.data)
            p_image = picture_file
        elif not form.post_picture.data:
            p_image = os.path.join(app.root_path, 'static/post_pictures', 'default.jpg')
        post = Post(title=form.title.data, description=form.description.data, post_image=p_image, portions=form.portions.data,
                    prep_time=form.prep_time.data, type_category=form.type_category.data, ingredients=form.ingredients.data, preparation=form.preparation.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created!", 'success')
        return redirect(url_for('home'))

    return render_template('create_post.html', title='Post Recipe', form=form, legend='Post Recipe')


# render template by given id of the post
@app.route("/post/<int:post_id>")
def post(post_id):
    post = Post.query.get_or_404(post_id)
    post_image = url_for('static', filename='post_pictures/' + post.post_image)
    return render_template('post.html', title=post.title, post=post, post_image=post_image)


@app.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.post_picture.data:
            picture_file = save_picture(form.post_picture.data)
            p_image = picture_file
        elif not form.post_picture.data:
            p_image = os.path.join(app.root_path, 'static/post_pictures', 'default.jpg')
        post.title = form.title.data
        post.description = form.description.data
        post.post_image = p_image
        post.portions = form.portions.data
        post.prep_time = form.prep_time.data
        post.type_category = form.type_category.data
        post.ingredients = form.ingredients.data
        post.preparation = form.preparation.data
        # post = Post(title=form.title.data, description=form.description.data, post_image=p_image,
        #              portions=form.portions.data,
        #              prep_time=form.prep_time.data, type_category=form.type_category.data,
        #              ingredients=form.ingredients.data, preparation=form.preparation.data, author=current_user)
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.description.data = post.description
        post_image = url_for('static', filename='post_pictures/' + post.post_image)
        form.portions.data = post.portions
        form.prep_time.data = post.prep_time
        form.type_category.data = post.type_category
        form.ingredients.data = post.ingredients
        form.preparation.data = post.preparation
    return render_template('create_post.html', title='Update Recipe', form=form, legend='Update Recipe', post_image=post_image)


@app.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your recipe has been deleted!')
    return redirect(url_for('home'))


@app.route('/recent_recipes')
def recent_recipes():
    page = request.args.get('page', 1, type=int)
    rec_posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=4)
    return render_template('recent_recipes.html', title='Recent Recipes', rec_posts=rec_posts)


@app.route('/admin')
@login_required
@admin_required
def for_admins_only():
    return "For admins only!"


@app.route('/moderate')
@login_required
@permission_required(Permission.MODERATE)
def for_moderators_only():
    return "For comments moderators!"



@app.errorhandler(404)
def error_404(error):
    return render_template('404.html'), 404


@app.errorhandler(403)
def error_403(error):
    return render_template('403.html'), 403

@app.errorhandler(500)
def error_500(error):
    db.session.rollback()
    render_template('500.html'), 500

