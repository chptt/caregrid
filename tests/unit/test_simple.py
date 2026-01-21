"""
Simple test to verify test discovery works.
"""

from django.test import TestCase


class SimpleTest(TestCase):
    """Simple test class."""
    
    def test_simple(self):
        """Simple test method."""
        self.assertEqual(1 + 1, 2)