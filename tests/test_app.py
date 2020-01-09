import unittest

from itviec import create_app


class BasicTestCase(unittest.TestCase):

    def test_index(self):
        app = create_app(profile="testing")
        tester = app.test_client(self)
        response = tester.get('/', content_type='html/text')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[:15], b'<!DOCTYPE html>')


if __name__ == '__main__':
    unittest.main()
