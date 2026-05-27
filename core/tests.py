from django.test import TestCase
from rest_framework.test import APIClient
from unittest.mock import patch
from .models import Student, School
from django.contrib.auth.hashers import make_password

class AuthApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.login_url = '/api/students/login'
        self.info_url = '/api/students/info'
        
        self.school = School.objects.create(name="가천대학교")
        
        self.existing_student = Student.objects.create(
            school=self.school,
            login_id='testuser',
            password_hash=make_password('testpass'),
            name='Test User',
            major='Computer Science',
            year=3,
            gpa=4.0,
            income_bracket=5
        )

    @patch('core.views.requests.post')
    def test_login_missing_credentials(self, mock_post):
        response = self.client.post(self.login_url, {'username': 'testuser'})
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error_code'], 'REQ_001')

    @patch('core.views.requests.post')
    def test_login_invalid_credentials(self, mock_post):
        mock_post.return_value.text = "아이디 또는 패스워드가 잘못 입력되었습니다."
        response = self.client.post(self.login_url, {
            'username': 'wronguser',
            'password': 'wrongpass',
            'school_id': 1
        })
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.data['error_code'], 'AUTH_001')

    @patch('core.views.requests.post')
    def test_login_first_time_success(self, mock_post):
        mock_post.return_value.text = "강좌 전체보기"
        response = self.client.post(self.login_url, {
            'username': 'newuser',
            'password': 'newpass',
            'school_id': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertIsNone(response.data['data'])
        self.assertEqual(response.data['message'], '첫 로그인 입니다.')

    @patch('core.views.requests.post')
    def test_login_existing_user_success(self, mock_post):
        mock_post.return_value.text = "강좌 전체보기"
        response = self.client.post(self.login_url, {
            'username': 'testuser',
            'password': 'testpass',
            'school_id': 1
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertIsNotNone(response.data['data']['access_token'])
        self.assertEqual(response.data['data']['login_id'], 'testuser')

    def test_student_info_missing_login_id(self):
        response = self.client.post(self.info_url, {
            'school_id': 1,
            'name': 'New User'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error_code'], 'REQ_001')

    def test_student_info_duplicate_user(self):
        response = self.client.post(self.info_url, {
            'login_id': 'testuser',
            'password': 'testpass',
            'school_id': 1,
            'name': 'Test User Duplicate'
        })
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data['error_code'], 'AUTH_002')

    def test_student_info_success(self):
        response = self.client.post(self.info_url, {
            'login_id': 'newuser',
            'password': 'newpass',
            'school_id': 1,
            'name': 'New User',
            'major': 'CS',
            'grade': 1,
            'gpa': 3.5,
            'income_bracket': 3,
            'profile_img': ''
        })
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['status'], 'success')
        self.assertIsNotNone(response.data['data']['access_token'])
        
        self.assertTrue(Student.objects.filter(login_id='newuser').exists())
