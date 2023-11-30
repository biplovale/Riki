import unittest
from unittest.mock import patch, MagicMock

from pymongo import MongoClient
from wiki.core import Page


class TestDaoPageIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up a test database and client
        cls.connection_string = "mongodb+srv://sgavin0813:password_1234@atlascluster.qdshz9s.mongodb.net/"
        cls.client = MongoClient(cls.connection_string)
        cls.test_db = cls.client.test_wikiDB

    @classmethod
    def tearDownClass(cls):
        # Clean up after the tests
        cls.test_db.pages.delete_many({})
        cls.client.close()

    def setUp(self):
        # Create a test page
        self.test_url = "test_page"
        self.test_page = Page(self.test_db, self.test_url, new_flag=True)

        self.test_page.load()
        self.test_page.render()

    @patch('wiki.core.session', MagicMock(get=lambda x: 'mock_author'))
    def test_save_and_load_page(self):
        # Set some page metadata and content
        self.test_page.title = "Test Title"
        self.test_page.tags = "tag1, tag2"
        self.test_page.content = "## Test Content"

        # save the page to the test database
        self.test_page.save()

        # Load the page from the test database
        loaded_page = Page(self.test_db, self.test_url, new_flag=False)

        # Check if the loaded page has the same metadata and content
        self.assertEqual(self.test_page.title, loaded_page.title)
        self.assertEqual(self.test_page.tags, loaded_page.tags)
        self.assertEqual(self.test_page.content, loaded_page.content)


    def test_render_html(self):
        self.test_page.content = "## HTML Render Test Content"

        self.test_page.render()

        # Check if the rendered HTML is not empty with the updated content
        self.assertTrue(self.test_page.html)
        self.assertEqual(self.test_page.content, "## HTML Render Test Content")


if __name__ == '__main__':
    unittest.main()
