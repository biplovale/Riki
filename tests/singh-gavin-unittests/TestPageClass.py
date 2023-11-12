import unittest
import mongomock
from wiki import DataAccessObject
from wiki.core import Page
from unittest.mock import patch


class TestPage(unittest.TestCase):
    def setUp(self):
        self.mock_db = mongomock.MongoClient().databse
        DataAccessObject.db = self.mock_db

    def test_page_load(self):
        # data for testing
        test_url = "test_page"
        test_content = "This is a test page."
        self.mock_db.pages.insert_one({"url": test_url, "content": test_content, "meta": {}})
        # initialize Page first
        page = Page(self.mock_db, test_url)
        # loading data
        page.load()
        # Assertions
        # test will fail if we cannot load the content from Database
        self.assertEqual(page.content, test_content)
        # test will fail if we cannot load the url from Database
        self.assertEqual(page.url, test_url)

    # patch is used here to simulate unique_id for the test
    @patch('wiki.core.session', {'unique_id': 'test_user'})
    def test_page_save(self):
        # Create a Page instance and call the save method
        test_url = "test_page"
        test_content = "This is a test page."
        # initialize new Page first
        page = Page(self.mock_db, test_url, new=True)
        page.body = test_content
        # calling page.save() for saving data
        page.save()
        # Now we are retrieving page object we have just saved using url we had provided
        saved_page = self.mock_db.pages.find_one({"url": test_url})
        # test will fail if data loaded back from Database is not same as what we had loaded
        self.assertEqual(saved_page["content"], test_content)


if __name__ == '__main__':
    unittest.main()
