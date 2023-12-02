import unittest
from unittest.mock import patch

import mongomock
from flask import Flask, session

from wiki import Wiki, DataAccessObject
from wiki.core import Page


class WikiTest(unittest.TestCase):
    def setUp(self):
        # Create a mock MongoDB collection
        self.mock_db = mongomock.MongoClient().db
        self.mock_collection = self.mock_db.pages
        DataAccessObject.db = self.mock_db
        # Initialize Wiki object
        self.wiki = Wiki()

        self.app = Flask(__name__)
        self.app.secret_key = 'your_secret_key_here'
        self.ctx = self.app.test_request_context()
        self.ctx.push()
        with self.app.test_request_context():
            session['unique_id'] = 'test_unique_id'

    def tearDown(self):
        # This method is called after each test
        self.ctx.pop()

    def test_get(self):
        # Add a document to the mock collection
        url = "existing_page"
        self.mock_collection.insert_one({"url": url, "content": "Test Content", "meta": {}})
        # Test the get method
        result = self.wiki.get(url)
        self.assertIsNotNone(result)
        # since only 1 page we can match the urls
        self.assertEqual(result.url, url)

    def test_get_or_404(self):
        url = "existing_page"
        self.mock_collection.insert_one({"url": url, "content": "Test Content", "meta": {}})
        result = self.wiki.get_or_404(url)
        self.assertIsNotNone(result)
        with self.assertRaises(Exception):  # Replace Exception with the specific exception you expect for 404
            self.wiki.get_or_404("non_existing_page")

    def test_get_bare(self):
        new_url = "new_page"
        result = self.wiki.get_bare(new_url)
        self.assertIsInstance(result, Page)
        self.assertTrue(result.new)
        existing_url = "existing_page"
        self.mock_collection.insert_one({"url": existing_url, "content": "Test Content", "meta": {}})
        result = self.wiki.get_bare(existing_url)
        self.assertFalse(result)

    def test_move(self):
        old_url = "old_page"
        new_url = "new_page"
        # Insert a page with a specific original url
        self.mock_collection.insert_one({"url": old_url, "content": "Old Content", "meta": {}})
        # moving page to a new url
        self.wiki.move(old_url, new_url)
        # test if new url exists
        self.assertTrue(self.wiki.exists(new_url))
        # test if new url is deleted
        self.assertFalse(self.wiki.exists(old_url))
        # Test for RuntimeError when the target URL already exists
        self.mock_collection.insert_one({"url": "existing_page", "content": "Content", "meta": {}})
        # checks if page can handle case when url we are moving to already exists
        with self.assertRaises(RuntimeError):
            self.wiki.move(new_url, "existing_page")

    def test_delete(self):
        url = "delete_page"
        # Insert a page with a specific url
        self.mock_collection.insert_one({"url": url})
        # result of deleting page
        result = self.wiki.delete(url)
        # if page was deleted, result should store true
        self.assertTrue(result)
        # since page is deleted, this should be false
        self.assertFalse(self.wiki.exists(url))

    def test_index(self):
        # Insert some pages into the mock collection
        self.mock_collection.insert_many([
            {"url": "page1", "content": "Content1", "meta": {}},
            {"url": "page2", "content": "Content2", "meta": {}}
        ])
        # Test the index method
        pages = self.wiki.index()
        # test the number of pages , should be 2
        self.assertEqual(len(pages), 2)
        # test if url matches, with index page[0] can be any of the 2 pages we have added previously
        self.assertIn(pages[0].url, ["page1", "page2"])

    def test_get_by_title(self):
        # Insert a page with a specific test_title
        test_title = "Unique Title"
        url = "unique-page"
        self.mock_collection.insert_one({"url": url, "content": "Content", "meta": {"title": test_title}})
        # Test the get_by_title method
        page = self.wiki.get_by_title(test_title)
        self.assertIsNotNone(page)
        # check if "title" returned is same as  "test_title"
        self.assertEqual(page.get("meta", {}).get("title"), test_title)

    def test_search(self):
        # Insert pages with different content and metadata
        self.mock_collection.insert_many([
            {"url": "page1", "content": "Test Content 1", "meta": {"title": "Test Title 1", "tags": "tag1,tag2"}},
            {"url": "page2", "content": "Another Test Content", "meta": {"title": "Another Title", "tags": "tag2,tag3"}}
        ])
        # Test the search method
        search_term = "test"
        # search_results has pages that contain term "test" in them
        search_results = self.wiki.search(search_term)
        # check if page1 was returned as it did contain keyword "test"
        self.assertTrue(any(page.url == "page1" for page in search_results))
        # check if page2 was returned as it did contain keyword "test"
        self.assertFalse(any(page.url == "page2" for page in search_results))
        # Test search by tags
        search_results = self.wiki.search("tag2", attrs=["tags"])
        self.assertEqual(len(search_results), 2)

    def test_search_by_author(self):
        # Insert pages with different authors
        self.mock_collection.insert_many([
            {"url": "page1", "content": "Content for page 1", "meta": {}, "author": "test_unique_id"},
            {"url": "page2", "content": "Content for page 2", "meta": {}, "author": "other_id"},
            {"url": "page3", "content": "Content for page 3", "meta": {}, "author": "test_unique_id"}
        ])
        result = self.wiki.search_by_author('test_unique_id')
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 2)

    def test_get_tags(self):
        with self.app.test_request_context():
            # Set the session unique_id
            session['unique_id'] = 'test_unique_id'

            # Insert pages with different tags
            self.mock_collection.insert_one(
                {"url": "page1", "content": "Content for page 1", "meta": {}, "author": "test_unique_id",
                 "tags": "tag1"}
            )

            # Test the get_tags method
            tags = self.wiki.get_tags()
            self.assertIsNotNone(tags)

            # Check if 'tag1' is in the tags dictionary
            self.assertIn('tag1', tags)

            # Check if the correct URL is associated with 'tag1'
            self.assertIn("page1", tags['tag1'])

    class TestPage(unittest.TestCase):
        def setUp(self):
            self.mock_db = mongomock.MongoClient().database
            DataAccessObject.db = self.mock_db

        def test_page_load(self):
            # Data for testing
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
        # Test data
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

    @patch('wiki.core.session', {'unique_id': 'test_user'})
    def test_get_all(self):
        # Insert some pages into the mock collection with the same author
        self.mock_collection.insert_many([
            {"url": "page1", "content": "Content1", "meta": {}, "author": "test_user"},
            {"url": "page2", "content": "Content2", "meta": {}, "author": "test_user"}
        ])

        # Test the get_all method
        pages = self.wiki.get_all()
        # Assertions to verify the expected behavior
        self.assertEqual(len(pages), 2)
        self.assertTrue(any(page.url == "page1" for page in pages))
        self.assertTrue(any(page.url == "page2" for page in pages))


if __name__ == '__main__':
    unittest.main()
