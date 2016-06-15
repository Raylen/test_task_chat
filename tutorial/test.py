__author__ = 'Kael'

import unittest

from pyramid import testing


class TutorialViewTests(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_home(self):
        from .views import TutorialViews

        request = testing.DummyRequest()
        inst = TutorialViews(request)
        response = inst.start()
        self.assertEqual(response.status_code, 200)
#        self.assertIn(b'Visit', response.body)
#        self.assertEqual('Home View', response['name'])
#        self.assertEqual(response.status, '302 Found')


class TutorialFunctionalTests(unittest.TestCase):
    def setUp(self):
        from tutorial import main
        app = main({})
        from webtest import TestApp

        self.testapp = TestApp(app)