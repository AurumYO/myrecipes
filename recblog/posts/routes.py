import os
from flask import render_template, request, url_for, redirect, flash, abort, current_app
from flask_login import current_user, login_required
from .. import db
from . import posts
from ..models import Permission, Post, Comment, FavoritePosts
from .forms import PostForm, CommentForm
from .utils import save_picture


@posts.route("/post/new", methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if current_user.can(Permission.WRITE) and form.validate_on_submit():
        if form.post_picture.data:
            picture_file = save_picture(form.post_picture.data)
            p_image = picture_file
        elif not form.post_picture.data:
            p_image = os.path.join(current_app.root_path, 'uploads/recipes_pics', 'default.jpg')
        post = Post(title=form.title.data, description=form.description.data, post_image=p_image,
                    portions=form.portions.data, recipe_yield=form.recipe_yield.data, cook_time=form.cook_time.data,
                    prep_time=form.prep_time.data, ready=form.ready_in.data, type_category=form.type_category.data,
                    main_ingredient = form.main_ingredient.data, ingredients=form.ingredients.data,
                    preparation=form.preparation.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash("Your post has been created!", 'success')
        return redirect(url_for('main.home'))

    return render_template('create_post.html', title='Post New Recipe', form=form, legend='Post New Recipe')


# render template by given id of the post
@posts.route("/post/<int:post_id>", methods=["GET", "POST"])
def post(post_id):
    post = Post.query.get_or_404(post_id)
    post_image = url_for('static', filename='uploads/recipes_pics/' + post.post_image)
    comments_form = CommentForm()
    if comments_form.validate_on_submit():
        comment = Comment(body=comments_form.body.data, post=post, author=current_user._get_current_object())
        db.session.add(comment)
        db.session.commit()
        flash('Your comment has been published!', 'success')
        return redirect(url_for('posts.post', post_id=post.id, page=-1))
    page = request.args.get('page', 1, type=int)
    if page == -1:
        page = (post.comments.count() - 1) // current_app.config['MYRECBLOG_COMMENTS_PER_PAGE'] + 1
    pagination = post.comments.order_by(Comment.comment_date.asc()).paginate(
        page, per_page=current_app.config['MYRECBLOG_COMMENTS_PER_PAGE'], error_out=False)
    comments = pagination.items
    return render_template('post.html', title=post.title, post=post, post_image=post_image, form=comments_form,
                           comments=comments, pagination=pagination)


@posts.route("/add_post_to_favorite/<int:post_id>")
@login_required
def add_post_to_favorite(post_id):
    post = Post.query.get_or_404(post_id)
    favorite = FavoritePosts(user=current_user, post=post)
    db.session.add(favorite)
    db.session.commit()
    flash('Successfully added to favorites', 'success')
    return redirect(url_for('posts.post', post_id=post.id))


@posts.route("/delete_post_from_favorite/<int:post_id>")
@login_required
def delete_post_from_favorite(post_id):
    post = Post.query.get_or_404(post_id)
    favorite = FavoritePosts(user=current_user, post=post)
    if not favorite:
        flash('You have not added this recipe to your favorites!')
        redirect(url_for('posts.post', post_id=post.id))
    post.delete_post_from_favorites(user_id=current_user.id)
    db.session.commit()
    flash('Successfully removed from favorites!', 'success')
    return redirect(url_for('posts.post', post_id=post.id))


@posts.route("/post/<int:post_id>/update", methods=["GET", "POST"])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.user_id != current_user.id:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        if form.post_picture.data:
            picture_file = save_picture(form.post_picture.data)
            p_image = picture_file
        elif not form.post_picture.data:
            p_image = post.post_image
        post.title = form.title.data
        post.description = form.description.data
        post.post_image = p_image
        post.portions = form.portions.data
        post.recipe_yield = form.recipe_yield.data
        post.cook_time = form.cook_time.data
        post.prep_time = form.prep_time.data
        post.ready = form.ready_in.data
        post.type_category = form.type_category.data
        post.main_ingredient = form.main_ingredient.data
        post.ingredients = form.ingredients.data
        post.preparation = form.preparation.data
        db.session.commit()
        flash('Your post has been updated!', 'success')
        return redirect(url_for('posts.post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.description.data = post.description
        post_image = url_for('static', filename='post_pictures/' + post.post_image)
        form.portions.data = post.portions
        form.recipe_yield.data = post.recipe_yield
        form.cook_time.data = post.cook_time
        form.prep_time.data = post.prep_time
        form.ready_in.data = post.ready
        form.type_category.data = post.type_category
        form.main_ingredient.data = post.main_ingredient
        form.ingredients.data = post.ingredients
        form.preparation.data = post.preparation
    return render_template('create_post.html', title='Update Recipe', form=form, legend='Update Recipe',
                           post_image=post_image)


@posts.route("/post/<int:post_id>/delete", methods=["POST"])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Your recipe has been deleted!', 'success')
    return redirect(url_for('main.home'))


@posts.route('/recent_recipes')
def recent_recipes():
    page = request.args.get('page', 1, type=int)
    rec_posts = Post.query.order_by(Post.date_posted.desc()).paginate(page=page, per_page=current_app.config['RECENT_PER_PAGE'])
    return render_template('recent_recipes.html', title='Recent Recipes', rec_posts=rec_posts)


@posts.route('/recipes/<string:category>',  methods=["GET"])
def categorical_recipes(category):
    page = request.args.get('page', 1, type=int)
    category_posts = Post.query.filter_by(type_category=category).paginate(page=page, per_page=current_app.config['RECENT_PER_PAGE'])
    return render_template('category_recipe.html', title=category.capitalize(), category_posts=category_posts)
