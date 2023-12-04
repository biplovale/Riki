import unittest
from unittest.mock import patch
import mongomock
from flask import Flask, session

from wiki.core import Page, DataAccessObject

class TestPage(unittest.TestCase):
    def setUp(self):
        # Create a mock MongoDB database
        self.mock_db = mongomock.MongoClient().db
        DataAccessObject.db = self.mock_db

        # Create Flask app and test request context
        self.app = Flask(__name__)
        self.app.secret_key = 'your_secret_key_here'
        self.ctx = self.app.test_request_context()
        self.ctx.push()

        # Set a test session user
        with self.app.test_request_context():
            session['unique_id'] = 'test_user'

    def tearDown(self):
        # Pop the Flask test request context
        self.ctx.pop()

    def test_page_load(self):
        test_url = "test_page"
        test_content = "This is a test page."

        # Insert test data into mock DB
        self.mock_db.pages.insert_one({"url": test_url, "content": test_content, "meta": {}})

        # Initialize Page and load data
        page = Page(self.mock_db, test_url)

        # Test loading an existing page
        page.load()
        self.assertEqual(page.content, test_content)
        self.assertEqual(page.url, test_url)

        # Test loading a non-existing page
        non_existing_url = "non_existing_page"
        page_non_existing = Page(self.mock_db, non_existing_url)
        page_non_existing.load()
        self.assertEqual(page_non_existing.content, "")
        self.assertEqual(page_non_existing.url, non_existing_url)

    def test_page_render(self):
        test_content = "# Test Header\nTest paragraph."
        page = Page(self.mock_db, "render_test", new_flag=True)
        page.content = test_content
        page.render()
        self.assertIn("<h1>Test Header</h1>", page.html)

    @patch('wiki.core.session', {'unique_id': 'test_user'})
    def test_save_existing_page(self):
        test_url = "existing_page"
        original_content = "Original content."
        updated_content = "Updated content."

        self.mock_db.pages.insert_one({"url": test_url, "content": original_content})
        page = Page(self.mock_db, test_url)
        page.content = updated_content
        page.save()

        saved_page = self.mock_db.pages.find_one({"url": test_url})
        self.assertEqual(saved_page['content'], updated_content)

    @patch('wiki.core.session', {'unique_id': 'test_user'})
    def test_save_new_page(self):
        new_url = "new_page"
        new_content = "Content for new page."

        # Create new page and save
        new_page = Page(self.mock_db, new_url, new_flag=True)
        new_page.content = new_content
        new_page.save()

        # Retrieve the saved page from the database
        saved_page = self.mock_db.pages.find_one({"url": new_url})

        # Assertions
        self.assertIsNotNone(saved_page)
        self.assertEqual(saved_page['content'], new_content)

    def test_tags_property(self):
        page = Page(self.mock_db, "test_page")
        page.tags = "tag1, tag2"
        self.assertEqual(page.tags, "tag1, tag2")

    def test_meta_property(self):
        page = Page(self.mock_db, "test_page")
        page['description'] = "Test Description"
        self.assertEqual(page.meta['description'], "Test Description")

    def test_title_property(self):
        page = Page(self.mock_db, "test_page")
        page.title = "Test Title"
        self.assertEqual(page.title, "Test Title")

    def test_getitem_setitem(self):
        page = Page(self.mock_db, "test_page")
        page['author'] = 'Test Author'
        self.assertEqual(page['author'], 'Test Author')

    def test_html_method(self):
        page = Page(self.mock_db, "test_page")
        page.content = "# Test Header\nTest content."
        page.render()
        self.assertIn("<h1>Test Header</h1>", page.__html__())

    def test_render_empty_content(self):
        page = Page(self.mock_db, "empty_content_page", new_flag=True)
        page.content = ""
        page.render()
        self.assertEqual(page._html, "")

if __name__ == '__main__':
    unittest.main()
