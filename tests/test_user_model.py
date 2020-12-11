import unittest
import time
from datetime import datetime
from recblog import create_app, db, bcrypt
from recblog.models import User, AnonymousUser, Role, Permission, Follow

class UserModeltestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_password_setter(self):
        u = User(password=bcrypt.generate_password_hash('palace').decode('utf-8'))
        self.assertTrue(u.password is not None)

    def test_check_password(self):
        u = User(password=bcrypt.generate_password_hash('foam').decode('utf-8'))
        self.assertTrue(u.check_password('foam'))
        self.assertFalse(u.check_password('froam'))

    def test_paswords_are_same(self):
        u1 = User(username='Sue', email='sue@example.com', confirmed=True,
                  password=bcrypt.generate_password_hash('salt').decode('utf-8'))
        u2 = User( username='Sue', email='sue@yahoo.com', confirmed=True,
                   password=bcrypt.generate_password_hash('salt').decode('utf-8'))
        self.assertTrue(u1.password != u2.password)

    def test_confirmation_token_valid(self):
        u = User(username='Sue', email='sue@example.com', confirmed=True,
                  password=bcrypt.generate_password_hash('salt').decode('utf-8'))
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token()
        self.assertTrue(u.confirm(token))

    # test if user confirmation token is valid with expires_sec parameter shorter than default
    def test_confirmation_token_valid_with_expires_sec(self):
        u2 = User(username='Sue', email='sue@gmail.com', confirmed=True,
                  password=bcrypt.generate_password_hash('salt').decode('utf-8'))
        db.session.add(u2)
        db.session.commit()
        token = u2.generate_confirmation_token(expires_sec=500)
        self.assertTrue(u2.confirm(token))

    def test_confirmation_token_expired(self):
        u = User( username='Sue', email='sue@example.com', confirmed=True,
                  password=bcrypt.generate_password_hash('foam').decode('utf-8'))
        db.session.add(u)
        db.session.commit()
        token = u.generate_confirmation_token(2)
        time.sleep(3)
        self.assertFalse(u.confirm(token))

    def test_reset_token_valid(self):
        u = User(username='John', email='john@gmail.com', confirmed=True,
                   password=bcrypt.generate_password_hash('fire').decode('utf-8'))
        db.session.add(u)
        db.session.commit()
        reset_token = u.get_reset_token()
        self.assertTrue(User.verify_reset_token(reset_token))

    def test_reset_token_invalid(self):
        u = User(username='Joshua', email='joshua@example.com', confirmed=True,
                   password=bcrypt.generate_password_hash('fox20').decode('utf-8'))
        db.session.add(u)
        db.session.commit()
        reset_token = u.get_reset_token()
        self.assertFalse(User.verify_reset_token(reset_token + 'gm'))

    def test_password_reset(self):
        u = User(username='Dina', email='dina@example.com', confirmed=True,
                  password=bcrypt.generate_password_hash('squirrel').decode('utf-8'))
        db.session.add(u)
        db.session.commit()
        reset_token = u.get_reset_token()
        if User.verify_reset_token(reset_token):
            u.password = bcrypt.generate_password_hash('chestnut').decode('utf-8')
            db.session.commit()
        self.assertTrue(u.check_password('chestnut'))
        self.assertFalse(u.check_password('hestnut'))

    def test_email_change_valid(self):
        u = User(username='Agnes', email='agnes@example.com', confirmed=True,
                 password=bcrypt.generate_password_hash('frog').decode('utf-8'))
        db.session.add(u)
        db.session.commit()
        token = u.generate_email_change_token('agnes15@example.com')
        self.assertTrue(u.confirm_email(token))
        self.assertTrue(u.email == 'agnes15@example.com')

    
    def test_email_change_token_invalid(self):
        u1 = User(username='Agnes', email='agnes@example.com', confirmed=True,
                 password=bcrypt.generate_password_hash('frog').decode('utf-8'))
        u2 = User(username='Jinn', email='jinn@example.com', confirmed=True,
                password=bcrypt.generate_password_hash('cassa').decode('utf-8'))
        db.session.add_all([u1, u2])   
        db.session.commit()
        token = u2.generate_email_change_token('jinniy@example.com')
        self.assertTrue(u2.confirm_email(token))
        self.assertFalse(u1.confirm_email(token))
        self.assertTrue(u2.email == 'jinniy@example.com')

    def test_duplicate_email_change(self):
        u1 = User(username='Agnes', email='agnes@example.com', confirmed=True,
                 password=bcrypt.generate_password_hash('frog').decode('utf-8'))
        u2 = User(username='Jinn', email='jinn@example.com', confirmed=True,
                password=bcrypt.generate_password_hash('cassa').decode('utf-8'))
        db.session.add_all([u1, u2])   
        db.session.commit()
        token = u2.generate_email_change_token('agnes@example.com')
        self.assertFalse(u1.confirm_email(token))
        self.assertTrue(u2.email == 'jinn@example.com')

    def test_user_role(self):
        u = User(username='Jinn', email='jinn@example.com', confirmed=True,
                password=bcrypt.generate_password_hash('cassa').decode('utf-8'))
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertFalse(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_moderator_role(self):
        moderator_role = Role.query.filter_by(name='Moderator').first()
        u = User(username='Sam', email='sam@example.com', confirmed=True,
                 password=bcrypt.generate_password_hash('Lylah').decode('utf-8'), role=moderator_role)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertFalse(u.can(Permission.ADMIN))

    def test_admin_role(self):
        admin_role = Role.query.filter_by(name='Administrator').first()
        u = User(username='Sam', email='sam@example.com', confirmed=True,
                 password=bcrypt.generate_password_hash('Lylah').decode('utf-8'), role=admin_role)
        self.assertTrue(u.can(Permission.FOLLOW))
        self.assertTrue(u.can(Permission.WRITE))
        self.assertTrue(u.can(Permission.COMMENT))
        self.assertTrue(u.can(Permission.MODERATE))
        self.assertTrue(u.can(Permission.ADMIN))

    def test_anonymous_user(self):
        anonim = AnonymousUser()
        self.assertFalse(anonim.can(Permission.FOLLOW))
        self.assertFalse(anonim.can(Permission.WRITE))
        self.assertFalse(anonim.can(Permission.COMMENT))
        self.assertFalse(anonim.can(Permission.MODERATE))
        self.assertFalse(anonim.can(Permission.ADMIN))

    def test_last_seen(self):
        u = User(username='Sam', email='sam@example.com',
                 password=bcrypt.generate_password_hash('fox20').decode('utf-8'))
        db.session.add(u)
        db.session.commit()
        self.assertTrue((datetime.utcnow() - u.last_seen).total_seconds() < 3)

    def test_ping(self):
        u = User( username='Elisa', email='elisa@example.com',
                  password=bcrypt.generate_password_hash('plant0').decode('utf-8'))
        db.session.add(u)
        db.session.commit()
        time.sleep(2)
        last_seen_before = u.last_seen
        u.ping()
        self.assertTrue(u.last_seen > last_seen_before)

    def test_follows(self):
        u1 = User(username='Sam', email='sam@example.com', confirmed=True,
                 password=bcrypt.generate_password_hash('Lylah').decode('utf-8'))
        u2 = User(username='Frank', email='frank@example.com', confirmed=True,
                  password=bcrypt.generate_password_hash('Laurel').decode('utf-8'))
        u3 = User(username='Bonnie', email='bonnie@example.com', confirmed=True,
                  password=bcrypt.generate_password_hash('Peter').decode('utf-8'))
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        self.assertFalse(u1.is_following_user(u3))
        self.assertFalse(u1.is_followed_by_user(u2))
        time_before = datetime.utcnow()
        u1.follow_user(u3)
        u1.follow_user(u2)
        db.session.add(u1)
        db.session.commit()
        time_after = datetime.utcnow()
        self.assertTrue(u1.is_following_user(u3))
        self.assertFalse(u1.is_followed_by_user(u3))
        self.assertTrue(u1.is_following_user(u2))
        self.assertTrue(u3.is_followed_by_user(u1))
        self.assertTrue(u1.followed.count() == 2)
        self.assertTrue(u3.followers.count() == 1)
        followed_table = u1.followed.all()[-1]
        self.assertTrue(followed_table.followed == u3)
        self.assertTrue(time_before <= followed_table.timestamp <= time_after)
        followed_table = u3.followers.all()[-1]
        self.assertTrue(followed_table.follower == u1)
        u1.stop_follow_user(u2)
        db.session.add(u1)
        db.session.commit()
        self.assertTrue(u1.followed.count() == 1)
        self.assertTrue(u2.followers.count() == 0)
        self.assertTrue(Follow.query.count() == 1)
        u2.follow_user(u1)
        db.session.add(u1)
        db.session.add(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 2)
        db.session.delete(u2)
        db.session.commit()
        self.assertTrue(Follow.query.count() == 1)

    def test_user_to_json(self):
        u = User(username='Sam', email='sam@example.com', confirmed=True,
                 password=bcrypt.generate_password_hash('Lylah').decode('utf-8' ))
        db.session.add(u)
        db.session.commit()
        with self.app.test_request_context('/'):
            json_user = u.convert_user_json(include_email=True)
        expected_keys = ['url', 'username', 'image_file', 'posts_url', 'location', 'last_seen', 'post_count', 'role_id',
                         'followed_posts_url', 'about_me', 'followers_number', 'followed_number', 'email',
                         'favorite_posts_total', 'comments_total']
        self.assertEqual(sorted(json_user.keys()), sorted(expected_keys))
        self.assertEqual('/api/v1/user_account/' + str(u.id), json_user['url'])

    def test_get_all_users(self):
        # create and add to database three users
        u1 = User(username='Sam', email='sam@example.com', confirmed=True,
                 password=bcrypt.generate_password_hash('Lylah').decode('utf-8'))
        u2 = User(username='Frank', email='frank@example.com', confirmed=True,
                  password=bcrypt.generate_password_hash('Laurel').decode('utf-8'))
        u3 = User(username='Bonnie', email='bonnie@example.com', confirmed=True,
                  password=bcrypt.generate_password_hash('Peter').decode('utf-8'))
        db.session.add_all([u1, u2, u3])
        db.session.commit()
        all_u = User.query.all()
        self.assertEqual(len(all_u), 3)
