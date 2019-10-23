import unittest
from ieddit import app
import json
from uuid import uuid4

class AccountTests(unittest.TestCase):
    
    def setUp(self):
        app.testing = True
        self.app = app.test_client()
        self.getNewID = lambda: str(uuid4()).split('-')[3]
    
    def test_1_successful_login_post(self):
        print(' Test 1: Login Success POST '.center(32, '='))
        data = {
            'username': 'a',
            'password': 'a'
        }
        res = self.app.post('/login/', data=data, headers={ 'content-type': 'www/form-data' }, follow_redirects=True)
        self.assertTrue(res.status_code == 200)
        
    def test_2_bad_login_post(self):
        print(' Test 2: Login Failure POST '.center(32, '='))
        data = {
            'username': 'badcreds123',
            'password': 'badpassword1234'
        }
        res = self.app.post('/login/', data=data, headers={ 'content-type': 'www/form-data' }, follow_redirects=True)
        self.assertTrue('Username or Password missing.' in str(res.data))
    
    def test_3_successful_login_get(self):
        print(' Test 3: Login Success GET '.center(32, '='))
        res = self.app.get('/login/', follow_redirects=True)
        self.assertTrue(res.status_code == 200)
        
    
        
        