from flask_sqlalchemy import get_debug_queries
from flask import request, render_template, redirect, url_for, make_response, current_app, abort
from flask_login import login_required, current_user
from . import main
from ..models import Post

# @main.before_app_request
# def sidebar_category():
#     categories = {('beef', 'Beef'), ('cheese', 'Cheese'), ('cereal', 'Cereal'), 
#     ('chicken', 'Chicken'), ('chocolate', 'Chocolate'), ('eggs', 'Eggs'),
#     ('fish', 'Fish'), ('flour', 'Flour'), ('fruit', 'Fruits'), ('lamb', 'Lamb'),
#      ('meat', 'Meat, other'), ('milk', 'Milk'), ('mushroom', 'Mushrooms'), 
#      ('pasta', 'Pasta'), ('pork', 'Pork'), ('sausage', 'Sausage'), 
#      ('seafood', 'Seafood'), ('turkey', 'Turkey'), ('vegetables', 'Vegetables')}
#     return categories


@main.after_app_request
def after_request(response):
    for query in get_debug_queries():
        if query.duration >= current_app.config['MYRECBLOG_SLOW_DB_QUERY_TIME']:
            current_app.logger.warning(f'Slow query: {query.statement}\nParameters: {query.parameters}\nDuration: {query.duration}\nContext: {query.context}\n')
    return response


@main.route('/shutdown')
def server_shutdown():
    if not current_app.testing:
        abort(404)
    shutdown = request.environ.get('werkzeug.server.shutdown')
    if not shutdown:
        abort(500)
    shutdown()
    return 'Shutting  down MyRecipesBlog...'



@main.route('/')
@main.route('/home')
def home(latest_page=1):
    # selects 3 latest posts from database for display in carousel
    carousel_posts = Post.query.order_by(Post.date_posted.desc())[:3]
    # latest posts section
    latest_page = request.args.get('latest_page', 1, type=int)
    latest_pagination = Post.query.order_by(Post.date_posted.desc()).paginate(latest_page, current_app.config['LATEST_PER_PAGE'], False)
    # pies posts section
    pie_posts = Post.query.filter_by(type_category='pie').order_by(Post.date_posted.desc())[:12]
    # followed posts section
    show_followed = False
    if current_user.is_authenticated:
        show_followed = bool(request.cookies.get('show_followed', ''))
        if not show_followed:
            followed_posts = current_user.followed_posts
        if show_followed:
             followed_posts = Post.query
        followed_page = request.args.get('page', 1, type=int )
        followed_posts_page = followed_posts.order_by(Post.date_posted.desc()).paginate(
            followed_page, per_page=4, error_out=False)
    else:
        followed_posts_page = []
    # category_sidebar = sidebar_category()
    return render_template("home.html", title='Home Page', carousel_posts=carousel_posts, latest_posts=latest_pagination, pie_posts=pie_posts,
                            followed_posts_page=followed_posts_page, latest_page=latest_pagination)


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


@main.route('/sitemap')
def sitemap():
    return render_template('sitemap.html', title='Sitemap')

