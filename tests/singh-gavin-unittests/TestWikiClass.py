import unittest
import mongomock
from wiki import Wiki, DataAccessObject



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
        self.assertEqual(result.url, url)

    # Other test methods...

if __name__ == '__main__':
    unittest.main()