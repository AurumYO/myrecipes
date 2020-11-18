import re
import unittest
from recblog import create_app, db
from recblog.models import Permission, Role, User



class FlaskClientTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_home_page(self):
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertTrue('Newest recipes' in response.get_data(as_text=True))


    def test_register_and_login(self):
        # test of the new account registration
        response = self.client.post('/register', data={
            'username': 'Suesan',
            'email': 'sue@example.com',
            'password': 'foot',
            'confirm_password': 'foot'
        })
        self.assertEqual(response.status_code, 302)

        # log in with recently created account credentials
        response = self.client.post('/login', data={'email': 'sue@example.com', 'password': 'foot'},
                                    follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse(re.search('Posts by followed Users', response.get_data(as_text=True)))
        self.assertTrue( re.search('Dear Suesan', response.get_data( as_text=True)))
        self.assertTrue('Check your inbox,' in response.get_data(as_text=True))

        # confirmation of the account with token
        user = User.query.filter_by(email='sue@example.com').first()
        token = user.generate_confirmation_token()
        response = self.client.get(f'/confirm/{token}', follow_redirects=True)
        user.confirm(token)
        self.assertEqual(response.status_code, 200)
        self.assertTrue('You have confirmed your account. Welcome to the Delicious Life!'
                        in response.get_data(as_text=True))

        # testing of the log out user route
        response = self.client.get('/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertFalse("You've been logged out!" in response.get_data(as_text=True))
