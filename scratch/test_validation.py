import os
import sys
import unittest

# Add workspace directory to python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from flask import session
from app import app
from database import get_db, dict_cursor

class TestActivityFrequencyLimits(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app_context = app.app_context()
        self.app_context.push()
        
        # We will use the existing test student '4SO24AI029' who is in Sem 4, Year 2
        self.student_id = '4SO24AI029'
        
        # Clean up any existing submissions for these test activities first to guarantee clean runs
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM submissions WHERE student_id = %s AND activity_id IN (7, 14)", (self.student_id,))
        conn.commit()
        conn.close()

    def tearDown(self):
        # Clean up after tests
        conn = get_db()
        cur = conn.cursor()
        cur.execute("DELETE FROM submissions WHERE student_id = %s AND activity_id IN (7, 14)", (self.student_id,))
        conn.commit()
        conn.close()
        self.app_context.pop()

    def set_session(self, client):
        with client.session_transaction() as sess:
            sess['user_id'] = self.student_id
            sess['role'] = 'student'
            sess['name'] = 'Test Student'

    def test_frequency_limit_regular_activity(self):
        client = app.test_client()
        self.set_session(client)
        
        # 1. First claim for Hackathon (activity_id=7) should succeed (redirects to dashboard)
        response1 = client.post('/student/submit', data={
            'activity_id': '7',
            'role': 'participant',
            'organized_by': 'SJEC IEEE',
            'activity_date': '2026-06-12',
            'duration_hours': '8',
            'points_claimed': '10'
        })
        self.assertEqual(response1.status_code, 302)
        self.assertIn('/student/dashboard', response1.location)
        
        # 2. Second claim for Hackathon in the same semester (same year, Year 2) should fail with validation error
        response2 = client.post('/student/submit', data={
            'activity_id': '7',
            'role': 'participant',
            'organized_by': 'SJEC IEEE',
            'activity_date': '2026-06-12',
            'duration_hours': '8',
            'points_claimed': '10'
        })
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b"You have already claimed points for &#39;Hackathon/Ideathon&#39; in this academic year (Year 2). It can only be claimed once a year.", response2.data)

    def test_frequency_limit_class_representative(self):
        client = app.test_client()
        self.set_session(client)
        
        # 1. First claim for Class Representative (activity_id=14) should succeed
        response1 = client.post('/student/submit', data={
            'activity_id': '14',
            'role': 'participant',
            'organized_by': 'SJEC CS',
            'activity_date': '2026-06-12',
            'duration_hours': '2',
            'points_claimed': '5'
        })
        self.assertEqual(response1.status_code, 302)
        self.assertIn('/student/dashboard', response1.location)
        
        # 2. Second claim for Class Representative in the same semester should fail
        response2 = client.post('/student/submit', data={
            'activity_id': '14',
            'role': 'participant',
            'organized_by': 'SJEC CS',
            'activity_date': '2026-06-12',
            'duration_hours': '2',
            'points_claimed': '5'
        })
        self.assertEqual(response2.status_code, 200)
        self.assertIn(b"You have already claimed Class Representative points for this semester.", response2.data)

if __name__ == '__main__':
    unittest.main()
