from django.test import TestCase

class baseTest(TestCase):
    def test_basic(self):
        self.assertEqual(1, 1)
