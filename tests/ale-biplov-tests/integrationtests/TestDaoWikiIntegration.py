import unittest
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

    def setUp(self):
        test_page_data = [
            {"url": "test_page_1", "meta": {"title": "Test Page 1", "tags": "tag1, tag2", "body": "Content for test page 1"}},
            {"url": "test_page_2", "meta": {"title": "Test Page 2", "tags": "tag2, tag3", "body": "Content for test page 2"}},
            {"url": "test_page_3", "meta": {"title": "Test Page 3", "tags": "tag3, tag4", "body": "Content for test page 3"}},
        ]
        self.wiki.collection.insert_many(test_page_data)

    def test_exists(self):
        self.assertTrue(self.wiki.exists("test_page_1"))
        self.assertFalse(self.wiki.exists("nonexistent_page"))

    def test_get(self):
        page = self.wiki.get("test_page_1")
        self.assertIsNotNone(page)
        self.assertEqual(page.url, "test_page_1")

        nonexistent_page = self.wiki.get("nonexistent_page")
        self.assertIsNone(nonexistent_page)

    def test_get_all(self):
        pages = self.wiki.get_all()
        self.assertEqual(len(pages), 3)

        self.assertTrue(all(page.author == "unique_id" for page in pages))

    def test_get_or_404(self):
        existing_page = self.wiki.get_or_404("test_page_1")
        self.assertIsNotNone(existing_page)

        with self.assertRaises(Exception):
            self.wiki.get_or_404("nonexistent_page")

    def test_get_bare(self):
        new_page = self.wiki.get_bare("new_page")
        self.assertIsNotNone(new_page)
        self.assertEqual(new_page.url, "new_page")

        existing_page = self.wiki.get_bare("test_page_1")
        self.assertFalse(existing_page)

    def test_move(self):
        self.wiki.move("test_page_1", "moved_page")
        self.assertFalse(self.wiki.exists("test_page_1"))
        self.assertTrue(self.wiki.exists("moved_page"))

        with self.assertRaises(RuntimeError):
            self.wiki.move("test_page_2", "moved_page")

    def test_delete(self):
        self.assertTrue(self.wiki.delete("test_page_1"))
        self.assertFalse(self.wiki.exists("test_page_1"))

        self.assertFalse(self.wiki.delete("nonexistent_page"))

    def test_index(self):
        pages = self.wiki.index()
        self.assertEqual(len(pages), 3)

    def test_index_by(self):
        indexed_by_tags = self.wiki.index_by("tags")
        self.assertEqual(len(indexed_by_tags), 4)

    def test_get_by_title(self):
        page_data = self.wiki.get_by_title("Test Page 1")
        self.assertIsNotNone(page_data)
        self.assertEqual(page_data["url"], "test_page_1")

        nonexistent_page_data = self.wiki.get_by_title("Nonexistent Page")
        self.assertIsNone(nonexistent_page_data)

    def test_get_tags(self):
        tags = self.wiki.get_tags()
        self.assertEqual(len(tags), 4)

    def test_index_by_tag(self):
        pages_with_tag = self.wiki.index_by_tag("tag2")
        self.assertEqual(len(pages_with_tag), 2)

    def test_search(self):
        search_results = self.wiki.search("content")
        self.assertEqual(len(search_results), 3)

        search_results_case_sensitive = self.wiki.search("Content", ignore_case=False)
        self.assertEqual(len(search_results_case_sensitive), 0)

        search_results_specific_attrs = self.wiki.search("Test", attrs=["title"])
        self.assertEqual(len(search_results_specific_attrs), 3)


if __name__ == '__main__':
    unittest.main()