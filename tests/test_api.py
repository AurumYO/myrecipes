import re
import json
from base64 import b64encode
import unittest
from recblog import create_app, db, bcrypt
from recblog.models import Permission, Role, User


class APITestCase(unittest.TestCase):
    # set up test application
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()
        self.client = self.app.test_client(use_cookies=True)

    # destroy test application after finishing of the testing
    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()


    def get_api_headers(self, email, password):
        return {'Authorization': 'Basic ' + b64encode((email + ':' + password).encode('utf-8')).decode('utf-8'),
                'Accept': 'application/json',
                'Content-Type': 'application/json'}

    def test_no_authentication(self):
        response = self.client.get('api/v1/posts/', content_type='application/json')
        self.assertEqual(response.status_code, 401)

    # testing post creation from registerred user with permission to create posts
    def test_posts(self):
        # create test user with role User
        r = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(r)
        u = User(username='Suesan', email='sue@example.com', password=bcrypt.generate_password_hash('foam'),
                 confirmed=True, role=r)
        db.session.add(u)
        db.session.commit()

        # write a post
        response = self.client.post('api/v1/posts/', headers=self.get_api_headers('sue@example.com', 'foam'),
                                    data=json.dumps({'title': 'Test recipe #1',
                                                     'description': 'Test description to the Test Title',
                                                     'image_file': 'default.jpg', 'portions': 6,
                                                     'prep_time': 45, 'type_category': 'meat',
                                                     'ingredients': 'test post.ingredients',
                                                     'preparation': 'Test preparation'
                                                     }))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # display the created post
        response = self.client.get(url, headers=self.get_api_headers('sue@example.com', 'foam'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['title'], 'Test recipe #1')
        self.assertEqual(json_response['prep_time'], 45)
        self.assertEqual(json_response['preparation'], 'Test preparation')
        self.assertEqual(json_response['preparation_html'], '<p>Test preparation</p>')
