import re
import json
from base64 import b64encode
import unittest
from flask_jwt_extended import create_access_token, get_jwt_identity, verify_jwt_in_request
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
        response = self.client.get('api/v1/users/', content_type='application/json')
        self.assertEqual(response.status_code, 401)

    # test 404 response
    def test_404(self):
        response = self.client.get('/wrong/url', headers=self.get_api_headers('email', 'password'))
        self.assertEqual(response.status_code, 404)

    # test adding new users via API
    def test_add_new_user(self):
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
                  'password': 'foam', 'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'Suesan')


    # test add new user without providing username
    def test_add_new_user_without_required_fields(self):
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': '', 'email': 'sue@example.com', 'password': 'foam',\
                  'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': '', 'password': 'foam',\
                  'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 400)
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
                  'password': '', 'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 400)
    
    # test logout and token revoking
    def test_logout(self):
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com', 'password': 'foam',\
                  'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.delete(f'/api/v1/logout',\
             headers=self.get_api_headers('sue@example.com', 'foam'),)
        self.assertEqual(response.status_code, 401)

    # test login and authentication
    def test_login_and_authentication(self):
        # add new user
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
                              'password': 'foam', 'about_me': 'JM',\
                              'location': 'Here'}))
        self.assertEqual(response.status_code, 200)
        token_data = response.get_json('access_token')
        self.assertFalse('access_token' in token_data)
        # try to access protected route
        response = self.client.get('api/v1/posts/', headers=self.get_api_headers('sue@example.com', 'foam'))
        self.assertEqual(response.status_code, 401)
        # new user login
        response = self.client.post(f'/api/v1/login',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'email': 'sue@example.com', 'password': 'foam'}))
        token_data = response.get_json('access_token')
        self.assertTrue('access_token' in token_data)
        access_token = token_data['access_token']
        self.assertEqual(response.status_code, 200)
        # try to access protected route with logged in user
        access_headers = {'Authorization': 'Bearer {}'.format(access_token)}
        response = self.client.get('api/v1/posts/', headers=access_headers)
        self.assertEqual(response.status_code, 200)
    
    def test_bad_authorization(self):
        #add new user
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
                  'password': 'foam', 'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 200)
        # authenticate with invalid password
        response = self.client.post(f'/api/v1/login',\
             headers=self.get_api_headers('sue@example.com', 'freeze'),\
             data=json.dumps({'email': 'sue@example.com', 'password': 'freeze'}))
        self.assertEqual(response.status_code, 401)

    def test_anonymous(self):
        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('', ''))
        self.assertEqual(response.status_code, 401)

    def test_token(self):
        # add test user
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
                  'password': 'foam', 'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 200)

        # login new test user
        response = self.client.post(f'/api/v1/login',\
                                    headers=self.get_api_headers('sue@example.com', 'foam'),\
                                    data=json.dumps({'email': 'sue@example.com', 'password': 'foam'}))
        self.assertEqual(response.status_code, 200)
        token_data = response.get_json('access_token')
        self.assertTrue('access_token' in token_data)
        access_token = token_data['access_token']
        self.assertIsNotNone(access_token)

        # issue a request without token
        response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('sue@example.com', 'foam'))
        self.assertEqual(response.status_code, 401)

        # issue a request with token
        access_headers = {'Authorization': 'Bearer {}'.format(access_token)}
        response = self.client.get('/api/v1/posts/', headers=access_headers)
        self.assertEqual(response.status_code, 200)
        self.assertIsNotNone(access_headers)
        
        # issue a request with authorization token
        response = self.client.get('/api/v1/posts/', headers=access_headers)
        self.assertEqual(response.status_code, 200)

    # TODO! test response with unconfirmed account
    # def test_unconfirmed(self):
        # # register new user
        # response = self.client.post(f'/api/v1/new_user/',\
        #      headers=self.get_api_headers('sue@example.com', 'foam'),\
        #      data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
        #           'password': 'foam', 'about_me': 'JM', 'location': 'Here'}))
        # self.assertEqual(response.status_code, 200)

        # get list of posts with unconfirmed account
        # response = self.client.get('/api/v1/posts/', headers=self.get_api_headers('janice@example.com', 'Chandler'))
        # self.assertEqual(response.status_code, 403)

    # testing post creation from registerred user with permission to create posts
    def test_posts(self):
        # create test users with role User and user instance 'u2' should be following user instance 'u1'
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
                  'password': 'foam', 'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('ramie@example.com', 'dentas'),\
             data=json.dumps({'username': 'Ramie', 'email': 'ramie@example.com',\
                  'password': 'dentas', 'about_me': 'RM-JM', 'location': 'Kyiv'}))
        self.assertEqual(response.status_code, 200)

        # log in new registerred user_1, recive authorization token and create authorizatoin header
        # for issueing new requests by user_1
        response = self.client.post(f'/api/v1/login',\
                                    headers=self.get_api_headers('sue@example.com', 'foam'),\
                                    data=json.dumps({'email': 'sue@example.com', 'password': 'foam'}))
        self.assertEqual(response.status_code, 200)
        token_data_u1 = response.get_json('access_token')
        self.assertTrue('access_token' in token_data_u1)
        access_token_u1 = token_data_u1['access_token']
        self.assertIsNotNone(access_token_u1)
        access_headers_u1 = {'Authorization': 'Bearer {}'.format(access_token_u1)}
        
        # write a post
        response = self.client.post('api/v1/post_new/',\
                        headers=access_headers_u1,\
                        data=json.dumps({'name': 'Test recipe #1',
                                         'description': 'Test description to the Test Title',
                                         'image': 'default.jpg', 'portions': 6,
                                         'recipeYield': '12 pieces', 'cookTime': '50', 'prepTime': 45,
                                         'ready': 135, 'recipeCategory': 'meat', 'main_ingredient': 'beef',
                                         'recipeIngredient': 'test post.recipeIngredient',
                                         'recipeInstructions': 'Test recipeInstructions'
                                         }))
        self.assertEqual(response.status_code, 201)
        post_url = response.headers.get('Location')
        self.assertIsNotNone(post_url)

        # display the created post
        response = self.client.get(post_url, headers=access_headers_u1)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], post_url)
        self.assertEqual(json_response['name'], 'Test recipe #1')
        self.assertEqual(json_response['cookTime'], '50')
        self.assertEqual(json_response['recipeInstructions'], 'Test recipeInstructions')
        self.assertEqual(json_response['recipeInstructions_html'], '<p>Test recipeInstructions</p>')
        json_post = json_response

        # display the posts by the specific user
        u1 = User.query.filter_by(email='sue@example.com').first()
        response = self.client.get(f"/api/v1/user_posts/{u1.id}", headers=access_headers_u1)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        # log in second user
        response = self.client.post(f'/api/v1/login',\
                                    headers=self.get_api_headers('ramie@example.com', 'dentas'),\
                                    data=json.dumps({'email': 'ramie@example.com', 'password': 'dentas'}))
        self.assertEqual(response.status_code, 200)
        token_data_u2 = response.get_json('access_token')
        self.assertTrue('access_token' in token_data_u2)
        access_token_u2 = token_data_u2['access_token']
        self.assertIsNotNone(access_token_u2)
        access_headers_u2 = {'Authorization': 'Bearer {}'.format(access_token_u2)}
        self.assertNotEqual(access_headers_u1 , access_headers_u2)

        # follow user_1 by user_2
        u2 = User.query.filter_by(email='ramie@example.com').first()
        u2.follow_user(u1)
      
        # get the posts from the followed user
        response = self.client.get(f'/api/v1/user_account/{u2.id}/followed_posts',
                                   headers=access_headers_u2)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('posts'))
        self.assertEqual(json_response.get('count', 0), 1)
        self.assertEqual(json_response['posts'][0], json_post)

        # test of editing posts by the user, which has not created the post
        eddited_post = Post.query.order_by(Post.date_posted.desc()).first()
        response = self.client.put(f'/api/v1/post/{eddited_post.id}',
                                   headers=access_headers_u2,
                                   data=json.dumps({'name': 'Updated Test recipe #1',
                                                    'description': 'Test description to the Test Title',
                                                    'image': 'default.jpg', 'portions': 6, 'recipeYield': '12 pieces',
                                                    'cookTime': '50', 'prepTime': 45, 'ready': 135,
                                                    'recipeCategory': 'meat', 'main_ingredient': 'beef',
                                                    'recipeIngredient': 'test post.recipeIngredient',
                                                    'recipeInstructions': 'Test recipeInstructions'
                                                    }))
        self.assertEqual(response.status_code, 403)

        # test of editing posts by the user, which has did created the post
        eddited_post = Post.query.order_by(Post.date_posted.desc()).first()
        response = self.client.put(f'/api/v1/post/{eddited_post.id}',
                                   headers=access_headers_u1,
                                   data=json.dumps({'name': 'Updated Test recipe #1',
                                                    'description': 'Test description to the Test Title',
                                                    'image': 'default.jpg', 'portions': 6, 'recipeYield': '12 pieces',
                                                    'cookTime': '30', 'prepTime': 45, 'ready': 135,
                                                    'recipeCategory': 'meat', 'main_ingredient': 'beef',
                                                    'recipeIngredient': 'Updated ingredients',
                                                    'recipeInstructions': 'Test recipeInstructions'
                                                    }))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], post_url)
        self.assertEqual(json_response['name'], 'Updated Test recipe #1')
        self.assertEqual(json_response['cookTime'], '30')
        self.assertEqual(json_response['recipeIngredient'], 'Updated ingredients')
        self.assertEqual(json_response['recipeIngredient_html'], '<p>Updated ingredients</p>')

        
    # test users API response
    def test_users(self):
        # add test users to database
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
                  'password': 'foam', 'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('ramie@example.com', 'dentas'),\
             data=json.dumps({'username': 'Ramie', 'email': 'ramie@example.com',\
                  'password': 'dentas', 'about_me': 'RM-JM', 'location': 'Kyiv'}))
        self.assertEqual(response.status_code, 200)
        
        # query the users in database
        u1 = User.query.filter_by(username='Suesan').first()
        u2 = User.query.filter_by(username='Ramie').first()
        self.assertIsNotNone(u1)
        self.assertIsNotNone(u1)

        # log in user_2 and get authentication token
        response = self.client.post(f'/api/v1/login',\
                                    headers=self.get_api_headers('ramie@example.com', 'dentas'),\
                                    data=json.dumps({'email': 'ramie@example.com', 'password': 'dentas'}))
        self.assertEqual(response.status_code, 200)
        token_data_u2 = response.get_json('access_token')
        access_token_u2 = token_data_u2['access_token']
        access_headers_u2 = {'Authorization': 'Bearer {}'.format(access_token_u2)}
        self.assertIsNotNone(access_headers_u2)

        # get user info from database by another registered user
        response = self.client.get(f'/api/v1/user_account/{u1.id}',
                                   headers=access_headers_u2)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'Suesan')
        self.assertEqual(json_response['location'], 'Here')

        # test get by user info on own profile information
        response = self.client.get(f'/api/v1/user_account/{u2.id}',\
            headers=access_headers_u2)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['username'], 'Ramie')
        self.assertEqual(json_response['location'], 'Kyiv')

    # test users comments
    def test_comments(self):
        # register three users with User role
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('sue@example.com', 'foam'),\
             data=json.dumps({'username': 'Suesan', 'email': 'sue@example.com',\
                  'password': 'foam', 'about_me': 'JM', 'location': 'Here'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('ramie@example.com', 'dentas'),\
             data=json.dumps({'username': 'Ramie', 'email': 'ramie@example.com',\
                  'password': 'dentas', 'about_me': 'RM-JM', 'location': 'Kyiv'}))
        self.assertEqual(response.status_code, 200)
        response = self.client.post(f'/api/v1/new_user/',\
             headers=self.get_api_headers('weisly@example.com', 'dentas'),\
             data=json.dumps({'username': 'Weslie', 'email': 'wesliy@example.com',\
                  'password': 'sand', 'about_me': 'Lazy', 'location': 'KPGH'}))
        self.assertEqual(response.status_code, 200)

        # write a post to database by u1
        u1 = User.query.filter_by(email='sue@example.com').first()
        post = Post(title='Test recipe #2', description='Test description to the Comments test',
                    post_image='default.jpg', portions=6, recipe_yield=12, cook_time=25, prep_time=45, ready=70,
                    type_category='meat', main_ingredient='vegetables', ingredients='test  comments - post.ingredients',
                    preparation='Test API Comments section preparation', author=u1)
        db.session.add(post)
        db.session.commit()

        # login user_2 and write a new comment to the post
        response = self.client.post(f'/api/v1/login',\
                                    headers=self.get_api_headers('ramie@example.com', 'dentas'),\
                                    data=json.dumps({'email': 'ramie@example.com', 'password': 'dentas'}))
        self.assertEqual(response.status_code, 200)
        token_data_u2 = response.get_json('access_token')
        access_token_u2 = token_data_u2['access_token']
        access_headers_u2 = {'Authorization': 'Bearer {}'.format(access_token_u2)}
        self.assertIsNotNone(access_headers_u2)
        response = self.client.post(f"/api/v1/post/{post.id}/comments/", headers=access_headers_u2,\
            data=json.dumps({'body': 'Very nice post Sue. By ramie@example.com'}))
        self.assertEqual(response.status_code, 201)
        json_response = json.loads(response.get_data(as_text=True))
        comment_url = response.headers.get('Location')
        self.assertIsNotNone(comment_url)
        self.assertEqual(json_response['body'], 'Very nice post Sue. By ramie@example.com')
        self.assertEqual(json_response['body_html'], '<p>Very nice post Sue. By ramie@example.com</p>')



        # get new comment for display
        response = self.client.get(comment_url, headers=access_headers_u2)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual('http://localhost' + json_response['url'], comment_url)
        self.assertEqual(json_response['body'], 'Very nice post Sue. By ramie@example.com')

        # modify the comment by its author
        comment = Comment.query.filter_by(author_id=2).first()
        response = self.client.put(f"/api/v1/comment/{comment.id}", headers=access_headers_u2,\
                                    data=json.dumps({'body': 'Update not a nice post Sue. By ramie@example.com'}))
        self.assertEqual(response.status_code, 200)
        # check thad modifications of the comment have been saved to database
        response = self.client.get(comment_url, headers=access_headers_u2)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertEqual(json_response['body'], 'Update not a nice post Sue. By ramie@example.com')
        self.assertEqual(json_response['body_html'], '<p>Update not a nice post Sue. By ramie@example.com</p>')


        # add another comment by user3 directly to database
        u3 = User.query.filter_by(email='wesliy@example.com').first()
        new_comment = Comment(body='Yes, I need to do he same', author=u3, post=post)
        db.session.add(new_comment)
        db.session.commit()

        # get all comments to a new post by post.id by the registered confirmed user
        response = self.client.get(f"/api/v1/post/{post.id}/comments/",\
                                   headers=access_headers_u2)
        self.assertEqual(response.status_code, 200)
        json_response = json.loads(response.get_data(as_text=True))
        self.assertIsNotNone(json_response.get('comment'))
        self.assertEqual(json_response.get('count', 0), 2)

        # fail post comment by unregistered user
        response = self.client.post(f"/api/v1/post/{post.id}/comments/",\
                                    headers=self.get_api_headers('sam@gmail.com', 'sand'),\
                                    data=json.dumps({'body': 'Very nice post Sue. By ramie@example.com'}))
        self.assertEqual(response.status_code, 401)

