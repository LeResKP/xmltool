#!/usr/bin/env python

from unittest import TestCase
from xmltool import utils


class TestUtils(TestCase):
    def test_truncate(self):
        s = "This text should be truncated"
        self.assertEqual(utils.truncate(s, 11), "This text...")
        self.assertEqual(utils.truncate(s, 25), "This text should be...")
        self.assertEqual(utils.truncate(s, 60), s)
