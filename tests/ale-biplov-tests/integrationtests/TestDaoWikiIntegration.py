import unittest
from unittest.mock import MagicMock, patch

from pymongo import MongoClient
from wiki.core import Wiki


class TestWikiIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up a test MongoDB database and connect to it
        cls.connection_string = "mongodb+srv://sgavin0813:password_1234@atlascluster.qdshz9s.mongodb.net/"
        cls.client = MongoClient(cls.connection_string)
        cls.db = cls.client.test_wikiDB
        cls.wiki = Wiki()

    @classmethod
    def tearDownClass(cls):
        cls.wiki.collection.delete_many({})
        cls.client.close()

    def tearDown(self):
        self.wiki.collection.delete_many({})

    def setUp(self):
        test_page_data = [
            {"url": "test_page_1", "meta": {"title": "Test Page 1"}, "tags": "tag1, tag2", "content": "Content for test page 1", "author": "unique_id"},
            {"url": "test_page_2", "meta": {"title": "Test Page 2"}, "tags": "tag2, tag3", "content": "Content for test page 2", "author": "unique_id"},
            {"url": "test_page_3", "meta": {"title": "Test Page 3"}, "tags": "tag3, tag4", "content": "Content for test page 3", "author": "unique_id"},
        ]
        self.wiki.collection.insert_many(test_page_data)

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'unique_id'))
    def test_page_operations(self):
        # Test basic page operations
        self.assertTrue(self.wiki.exists("test_page_1"))
        self.assertFalse(self.wiki.exists("nonexistent_page"))
        self.assertIsNotNone(self.wiki.get("test_page_1"))
        self.assertIsNone(self.wiki.get("nonexistent_page"))
        self.assertEqual(len(self.wiki.get_all()), 3)
        self.assertTrue(self.wiki.delete("test_page_1"))
        self.assertFalse(self.wiki.exists("test_page_1"))

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'unique_id'))
    def test_move_page(self):
        # Test moving a page
        self.wiki.move("test_page_2", "moved_page")
        self.assertFalse(self.wiki.exists("test_page_2"))
        self.assertTrue(self.wiki.exists("moved_page"))

        # Attempt to move to an existing page should raise RuntimeError
        with self.assertRaises(RuntimeError):
            self.wiki.move("test_page_3", "moved_page")

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'unique_id'))
    def test_index_and_search(self):
        # Test index and search functionality
        pages = self.wiki.index()
        print(self.wiki.index())
        self.assertEqual(len(pages), 3)

        pages_with_tag = self.wiki.index_by_tag("tag3")
        self.assertEqual(len(pages_with_tag), 2)

        # search in content
        search_results = self.wiki.search("Content")
        self.assertEqual(len(search_results), 3)

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'unique_id'))
    def test_get_by_title(self):
        # Test retrieving a page by title
        page_data = self.wiki.get_by_title("Test Page 2")
        self.assertIsNotNone(page_data)
        self.assertEqual(page_data["url"], "test_page_2")

        nonexistent_page_data = self.wiki.get_by_title("Nonexistent Page")
        self.assertIsNone(nonexistent_page_data)

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'unique_id'))
    def test_get_tags(self):
        # Test retrieving tags
        tags = self.wiki.get_tags()
        self.assertEqual(len(tags), 4)

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'unique_id'))
    def test_search_by_author(self):
        # Test searching by author
        author_search_results = self.wiki.search_by_author("unique_id")
        self.assertEqual(len(author_search_results), 3)

if __name__ == '__main__':
    unittest.main()