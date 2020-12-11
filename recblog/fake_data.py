from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db, bcrypt
from .models import User, Post


def users(count=100):
    fake = Faker()
    i = 0
    while i < count:
        u = User(email=fake.email(), username=fake.name(), image_file='default.jpg',
                 password=bcrypt.generate_password_hash('password').decode('utf-8'),
                 confirmed=True, location=fake.city(), about_me=fake.job())
        db.session.add(u)
        try:
            db.session.commit()
            i += 1
        except IntegrityError:
            db.session.rollback()


def posts(count=100):
    fake = Faker()
    user_count = User.query.count()
    for i in range(count):
        u = User.query.offset(randint(0, user_count-1)).first()
        p = Post(title=fake.text(), description=fake.text(), post_image='default.jpg', recipe_yield=randint(1, 32),
                 cook_time=randint(15, 160), date_posted=fake.date_time(), portions=randint(1, 24),
                 prep_time=randint(15, 500), ready = randint(50, 200), main_ingredient='meat',
                 type_category='pie', ingredients=fake.text(), preparation=fake.text(), author=u)
        db.session.add(p)
    db.session.commit()
