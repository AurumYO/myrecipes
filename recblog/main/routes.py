from flask import request, render_template, redirect, url_for, make_response
from flask_login import login_required, current_user
from . import main
from ..models import Post


@main.route('/')
@main.route('/home')
def home():
    # selects 3 latest posts from database for carousel
    carousel_posts = Post.query.order_by(Post.date_posted.desc())
    # latest posts section
    latest_page = request.args.get('page', 1, type=int)
    latest_posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=latest_page, per_page=4)
    cake_page = request.args.get('page', 1, type=int)
    cake_recipes = Post.query.filter_by(type_category='cake').order_by(Post.date_posted.desc()).paginate(page=cake_page, per_page=4)

    # followed posts section
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed'))
    if show_followed:
        followed_posts = current_user.following_posts
    else:
        followed_posts = Post.query
    followed_page = request.args.get('page', 1, type=int)
    followed_posts_page = followed_posts.order_by(Post.date_posted.desc()).paginate(followed_page, per_page=4, error_out=False)

    return render_template("home.html", carousel_posts=carousel_posts, latest_posts=latest_posts, cake_recipes=cake_recipes, followed_posts_page=followed_posts_page)


@main.route('/all')
@login_required
def show_all():
    resp = make_response(redirect(url_for('main.home')))
    resp.set_cookie( 'show_followed', '', max_age=30 * 24 * 60 * 60 )
    return resp



@main.route('/followed')
@login_required
def show_followed():
    resp = make_response(redirect(url_for('main.home')))
    resp.set_cookie('show_followed', '1', max_age=30*24*60*60)
    return resp

@main.route('/about')
def about():
    return render_template("about.html", title='About')
