import unittest
import mongomock
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

    def test_exists(self):
        # Add a document to the mock collection
        url = "test_url"
        self.mock_collection.insert_one({"url": url})
        # Test the exists method
        result = self.wiki.exists(url)
        self.assertTrue(result)

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

if __name__ == '__main__':
    unittest.main()