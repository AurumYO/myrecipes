import re
import json
from base64 import b64encode
import unittest
from recblog import create_app, db, bcrypt
from recblog.models import Permission, Role, User, Comment, Post


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

    # test 404 response
    def test_404(self):
        response = self.client.get('/wrong/url', headers=self.get_api_headers('email', 'password'))
        self.assertEqual(response.status_code, 404)
        # json_response = json.loads(response.get_data(as_text=True))
        # self.assertEqual(json_response['error'], 'Not Found')

    def test_bad_authorization(self):
        user_role = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(user_role)
        u = User(username='Kiwi', email='kiwi@example.com', password=bcrypt.generate_password_hash('green'),
                 confirmed=True, role=user_role)
        db.session.add(u)
        db.session.commit()
        # authenticate with invalid password
        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('kiwi@example.com', 'free'))
        self.assertEqual(response.status_code, 401)

    def test_anonymous(self):
        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('', ''))
        self.assertEqual(response.status_code, 401)

    def test_token(self):
        # add test user
        user_role = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(user_role)
        u = User(username='Sweety', email='sweety@example.com', password=bcrypt.generate_password_hash('orange'),
                 confirmed=True, role=user_role)
        db.session.add(u)
        db.session.commit()

        # issue a request with bad token
        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('bad bunny', ''))
        self.assertEqual(response.status_code, 401)

        # issue a request with token
        response = self.client.post('/api/v1/tokens/', headers=self.get_api_headers('sweety@example.com', 'orange'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('token'))
        token = json_response['token']

        # issue a request with authorization token
        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers(token, ''))
        self.assertEqual(response.status_code, 200)

    # test response with unconfirmed account
    def test_unconfirmed(self):
        # register new user
        user_role = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(user_role)
        u = User(username='Janice', email='janice@example.com', password=bcrypt.generate_password_hash('Chandler'),
                 confirmed=False, role=user_role)
        db.session.add(u)
        db.session.commit()

        # get list of posts with unconfirmed account
        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('janice@example.com', 'Chandler'))
        self.assertEqual(response.status_code, 403)

    # testing post creation from registerred user with permission to create posts
    def test_posts(self):
        # create test users with role User and user instance 'u2' should be following user instance 'u'
        rl = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(rl)
        u = User(username='Suesan', email='sue@example.com', password=bcrypt.generate_password_hash('foam'),
                 confirmed=True, role=rl)
        db.session.add(u)
        u2 = User(username='Sam', email='sam@example.com', password=bcrypt.generate_password_hash('sand'),
                  confirmed=True, role=rl)
        db.session.add(u2)
        u2.follow_user(u)
        db.session.commit()

        # write a post
        response = self.client.post('api/v1/posts/', headers=self.get_api_headers('sue@example.com', 'foam'),
                                    data=json.dumps({'name': 'Updated Test recipe #1',
                                                     'description': 'Test description to the Test Title',
                                                     'image': 'default.jpg', 'portions': 6, 'recipeYield': '12 pieces',
                                                     'cookTime': '50', 'prepTime': 45, 'ready': 135,
                                                     'recipeCategory': 'meat', 'main_ingredient': 'beef',
                                                     'recipeIngredient': 'test post.recipeIngredient',
                                                     'recipeInstructions': 'Test recipeInstructions'
                                                     }))
        self.assertEqual(response.status_code, 201)
        url = response.headers.get('Location')
        self.assertIsNotNone(url)

        # display the created post
        response = self.client.get(url, headers=self.get_api_headers('sue@example.com', 'foam'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['name'], 'Updated Test recipe #1')
        self.assertEqual(json_response['prepTime'], '45')
        self.assertEqual(json_response['recipeInstructions'], 'Test recipeInstructions')
        self.assertEqual(json_response['recipeInstructions_html'], '<p>Test recipeInstructions</p>')
        json_post = json_response

        # display the posts by the specific user
        response = self.client.get(f"/api/v1/user_posts/{u.id}", headers=self.get_api_headers('sue@example.com', 'foam'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        # get the posts from the followed user
        response = self.client.get(f'/api/v1/user_account/{u2.id}/followed_posts',
                                   headers=self.get_api_headers('sue@example.com', 'foam'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        # test of editing posts by the user, which created the post
        post = Post.query.order_by(Post.date_posted.desc()).first()
        response = self.client.put(f'/api/v1/posts/{post.id}',
                                   headers=self.get_api_headers('sue@example.com', 'foam'),
                                   data=json.dumps({'name': 'Updated Test recipe #1',
                                                    'description': 'Test description to the Test Title',
                                                    'image': 'default.jpg', 'portions': 6, 'recipeYield': '12 pieces',
                                                    'cookTime': '50', 'prepTime': 45, 'ready': 135,
                                                    'recipeCategory': 'meat', 'main_ingredient': 'beef',
                                                    'recipeIngredient': 'test post.recipeIngredient',
                                                    'recipeInstructions': 'Test recipeInstructions'
                                                    }))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['name'], 'Updated Test recipe #1')

    # test users API response
    def test_users(self):
        # add test users to database
        rl = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(rl)
        u1 = User(username='Suesan', email='sue@example.com', password=bcrypt.generate_password_hash('foam'),
                confirmed=True, role=rl )
        db.session.add(u1)
        u2 = User( username='Sam', email='sam@example.com', password=bcrypt.generate_password_hash('sand'),
                   confirmed=True, role=rl, location='Kyiv')
        db.session.add(u2)
        u2.follow_user(u1)
        db.session.commit()
        # get user info from database by another registered user
        response = self.client.get(f'/api/v1/user_account/{u1.id}',
                                   headers=self.get_api_headers('sam@example.com', 'sand'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'Suesan')
        response = self.client.get(f'/api/v1/user_account/{u2.id}',
                                   headers=self.get_api_headers('sue@example.com', 'foam'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'Sam')
        self.assertEqual(json_response['location'], 'Kyiv')

        # test get by user info on own profile information

    # test users comments
    def test_comments(self):
        # register three users with User role
        rl = Role.query.filter_by(name='User').first()
        self.assertIsNotNone(rl)
        u1 = User(username='Suesan', email='sue@example.com', password=bcrypt.generate_password_hash('foam'),
                confirmed=True, role=rl)
        u2 = User(username='Sam', email='sam@example.com', password=bcrypt.generate_password_hash('sand'),
                  confirmed=True, role=rl, location='Kyiv')
        u3 = User( username='Weisly', email='weisly@example.com', password=bcrypt.generate_password_hash('monarch'),
                   confirmed=True, role=rl)
        db.session.add_all([u1, u2, u3])
        db.session.commit()

        # write a post to database by u1
        post = Post(title='Test recipe #2', description='Test description to the Comments test',
                    post_image='default.jpg', portions=6, recipe_yield=12, cook_time=25, prep_time=45, ready=70,
                    type_category='meat', main_ingredient='vegetables', ingredients='test  comments - post.ingredients',
                    preparation='Test API Comments section preparation', author=u1)
        db.session.add(post)
        db.session.commit()

        # write a new comment to the post
        response = self.client.post(f'/api/v1/post/{post.id}/comments',
                                    headers=self.get_api_headers('sam@example.com', 'sand'),
                                    data=json.dumps({'body': 'Very nice post. by sue@example.com from Sam'}))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data(as_text=True))
        url = response.headers.get('Location')
        self.assertIsNotNone(url)
        self.assertEqual(json_response['body'], 'Very nice post. by sue@example.com from Sam')
        self.assertEqual(re.sub('<p>', '', json_response['body_html']), 'Very nice post. by sue@example.com from Sam</p>')

        # get new comment for display
        response = self.client.get(url, headers=self.get_api_headers('weisly@example.com', 'monarch'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], url)
        self.assertEqual(json_response['body'], 'Very nice post. by sue@example.com from Sam')

        # add another comment by user3 directly to database
        new_comment = Comment(body='Yes, I need to do he same', author=u3, post=post)
        db.session.add(new_comment)
        db.session.commit()

        # get all comments to a new post by post.id by the registered confirmed user
        response = self.client.get(f'/api/v1/post/{post.id}/comments/',
                                   headers=self.get_api_headers('sue@example.com', 'foam'))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('comment'))
        self.assertEqual(json_response.get('count', 0), 2)

        # fail post comment by unregistered user
        response = self.client.post( f'/api/v1/post/{post.id}/comments',
                                     headers=self.get_api_headers('sam@gmail.com', 'sand'),
                                     data=json.dumps({'body': 'I am not registered but want to comment'}))
        self.assertEqual(response.status_code, 401)

