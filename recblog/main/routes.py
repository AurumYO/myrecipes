from flask import request, render_template
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
    return render_template("home.html", carousel_posts=carousel_posts, latest_posts=latest_posts, cake_recipes=cake_recipes)


@main.route('/about')
def about():
    return render_template("about.html", title='About')
