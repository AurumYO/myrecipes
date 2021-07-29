# MyRecipes - is a personal blog about eating delicious food!

## Table of contents
* [General info](#general-info)
* [Technologies](#technologies)
* [Setup](#setup)
* [Features](#feature)
* [Sources](#sources)
* [TODO](#todo)

## General info
### On MyRecipes created for people who love to eat and cook to share their recipes and to search for new ideas and recipes.
### This particular app was created for training purposes.

## Technologies
Project is created with: 
* Flask version: 1.0.2
* SQLAlchemy version: 1.3.20
* Bootstrap 5
* API Authenticaton implemented with Flask-JWTManager


## Setup
##### to be added soon

## Features
#### User registration:
* Anyone can register with their Username, Email and Passord;
* A registered user is verified via email confirmation;
* A registered user can add additional imformation about themself in Account page;
* A registered user can follow/unfollow other registerred users to see what those users posted recenply;
* A registered user can have different permission roles: write, comment, moderate, admin with different priviledges;
#### Making Posts
* Posts can wriet only registerred users;
* A registered user can add any post they liked very much to favorites and find them easily in Favorites posts section from Home page;
* Posts can be edditted or deletted by author of the post or by Moderator/Administrator;

## Sources
This app is inspired by Miguel Grinberg's Flask tutorials and problem resolutions from book "Flask Web Development", 2nd edition
and his personal blog at (https://blog.miguelgrinberg.com/post/the-flask-mega-tutorial-part-i-hello-world)

## TODO
* Add search based on Elasticsearch version: 7.11.1