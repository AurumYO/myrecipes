# import re
# import threading
# import time
# import unittest
# from selenium import webdriver
# from recblog import create_app, db, fake_data, bcrypt
# from recblog.models import Role, User, Post


# class SeleniumTestCase(unittest.TestCase):
#     client = None

#     @classmethod
#     def setUpClass(cls):
#         # start Chrome
#         options = webdriver.ChromeOptions()
#         options.add_argument('--headless')
#         options.add_argument('--disable-gpu' )  # Last I checked this was necessary.
#         try:
#             cls.client = webdriver.Chrome(chrome_options=options)  #executable_path=r"/usr/lib/chromium-browser/chromedriver")
#         except:
#             pass

#         # skip these tests if the browser could not be started
#         if cls.client:
#             # create the application
#             cls.app = create_app('testing')
#             cls.app_context = cls.app.app_context()
#             cls.app_context.push()

#             # suppress logging to keep unittest output clean
#             import logging
#             logger = logging.getLogger('werkzeug')
#             logger.setLevel(logging.ERROR)

#             # create the database and populate with some fake data
#             db.create_all()
#             Role.insert_roles()
#             fake_data.users(10)
#             fake_data.posts(10)

#             # add an administrator user
#             admin_role = Role.query.filter_by( name='Administrator' ).first()
#             admin = User(email='sue@examle.com', username='Suesan', password=bcrypt.generate_password_hash('foam').decode('utf-8'), role=admin_role, confirmed=True)
#             print(admin.role)
#             db.session.add(admin)
#             db.session.commit()
#             print('Start thread')
#             # start the Flask server in a thread

#             cls.server_thread = threading.Thread(target=cls.app.run,
#                                                   kwargs={'debug': False})
#             cls.server_thread.start()

#             # give the server a second to ensure it is up
#             time.sleep(1)

#     @classmethod
#     def tearDownClass(cls):
#         if cls.client:
#             # stop the flask server and the browser
#             cls.client.get( 'http://localhost:5000/shutdown' )
#             cls.client.quit()
#             cls.server_thread.join()
#             # destroy database
#             db.session.remove()
#             db.drop_all()
#             # remove application context
#             cls.app_context.pop()

#     def setUp(self):
#         if not self.client:
#             self.skipTest('Web browser not available' )

#     def tearDown(self):
#         pass

#     # def test_chrome_admin_home_page(self):
#     #     print('Start test')
#     #     # navigate to homepage
#     #     self.client.get( 'http://localhost:5000/' )
#     #     self.assertTrue(re.search('Cakes Recipes', self.client.page_source))
