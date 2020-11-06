from random import randint
from sqlalchemy.exc import IntegrityError
from faker import Faker
from . import db
from .models import User, Post


def users(count=100):
    fake = Faker()
    i = 0
    while i < count:
        u = User(email=fake.email(), username=fake.username(), image_file='default.jpg', password='password',
                 confirmed=True, location=fake.location(), about_me=fake.about_me())
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
        u = User.query.offset(randint(0, user_count - 1)).first()
        p = Post(title=fake.text(), description=fake.text(), post_image='default.jpg', rating=randint(0, 5),
                 date_posted=fake.past_date(), portions=randint(1, 24), prep_time=randint(15, 500),
                 type_category='meat', ingredients=fake.text(), preparation=fake.text(), user_id=u)
        db.session.add(p)
    db.session.commit()
