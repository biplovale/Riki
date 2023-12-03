import unittest
from unittest.mock import MagicMock, patch

from pymongo import MongoClient
from wiki.core import Wiki, Page
from wiki.DataAccessObject import DatabaseSingleton

class TestWikiPageIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Set up a test MongoDB database and connect to it
        cls.connection_string = "mongodb+srv://sgavin0813:password_1234@atlascluster.qdshz9s.mongodb.net/"
        cls.client = MongoClient(cls.connection_string)
        cls.db = cls.client.test_wikiDB

    @classmethod
    def tearDownClass(cls):
        # Clean up after the tests
        cls.db.pages.delete_many({})
        cls.client.close()

    def tearDown(self):
        self.wiki.collection.delete_many({})

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def setUp(self):
        # Create a test Wiki instance
        self.wiki = Wiki()
        self.wiki.collection = self.db.pages

        # Create a test page
        self.test_url = "test_page"
        self.test_page = Page(self.db, self.test_url, new_flag=True)

        self.test_page.load()
        self.test_page.render()

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def test_page_saving(self):
        # Set some page metadata and content
        self.test_page.title = "Test Title"
        self.test_page.tags = "tag1, tag2"
        self.test_page.content = "## Test Content"

        # save the page to the test database
        self.test_page.save()

        # Load the page from the test database
        loaded_page = Page(self.db, self.test_url, new_flag=False)

        # Check if the loaded page has the same metadata and content
        self.assertEqual(self.test_page.title, loaded_page.title)
        self.assertEqual(self.test_page.tags, loaded_page.tags)
        self.assertEqual(self.test_page.content, loaded_page.content)
        self.assertEqual(loaded_page.author, 'mock_author')

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def test_page_update(self):
        # Update the existing test_page from setup
        self.test_page.title = "New Title"

        # save the page to the test database
        self.test_page.save()

        # Load the page from the test database
        updated_page = Page(self.db, self.test_url, new_flag=False)

        self.assertEqual(self.test_page.title, updated_page.title)

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def test_page_deletion(self):
        # Test deleting an existing page
        test_page_url = "page_to_delete"
        page_to_delete = Page(self.db, test_page_url, new_flag=True)
        page_to_delete.title = "Page to Delete"
        page_to_delete.save()

        # Ensure the page exists
        self.assertTrue(self.wiki.exists(test_page_url))

        # Delete the page
        self.wiki.delete(test_page_url)

        # Ensure the page is deleted
        self.assertFalse(self.wiki.exists(test_page_url))

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def test_search_pages(self):
        # Test searching for pages
        test_page1 = Page(self.db, "search_page_1", new_flag=True)
        test_page1.title = "Search Page 1"
        test_page1.tags = "tag1, tag2"
        test_page1.content = "Content for Search Page 1"
        test_page1.save()

        test_page2 = Page(self.db, "search_page_2", new_flag=True)
        test_page2.title = "Search Page 2"
        test_page2.tags = "tag2, tag3"
        test_page2.content = "Content for Search Page 2"
        test_page2.save()

        # Search for pages with "tag2" in tags
        search_results = self.wiki.search("tag2", ignore_case=True, attrs=['tags'])

        self.assertEqual(len(search_results), 2)

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def test_index_pages(self):
        # Test indexing all pages
        test_page1 = Page(self.db, "index_page_1", new_flag=True)
        test_page1.title = "Index Page 1"
        test_page1.save()

        test_page2 = Page(self.db, "index_page_2", new_flag=True)
        test_page2.title = "Index Page 2"
        test_page2.save()

        # Get all pages
        all_pages = self.wiki.index()

        self.assertEqual(len(all_pages), 2)

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def test_move_page(self):
        # Test moving a page
        test_page_url = "page_to_move"
        page_to_move = Page(self.db, test_page_url, new_flag=True)
        page_to_move.title = "Page to Move"
        page_to_move.save()

        new_url = "moved_page"
        self.wiki.move(test_page_url, new_url)

        # Ensure the old URL does not exist
        self.assertFalse(self.wiki.exists(test_page_url))

        # Ensure the page exists at the new URL
        self.assertTrue(self.wiki.exists(new_url))

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def test_get_tags(self):
        # Test retrieving tags
        test_page = Page(self.db, "tags_page", new_flag=True)
        test_page.title = "Tags Page"
        test_page.tags = "tag1, tag2"
        test_page.save()

        # Get tags from the Wiki
        tags = self.wiki.get_tags()

        self.assertEqual(len(tags), 2)

    @patch('wiki.core.session', MagicMock(get=lambda *args, **kwargs: 'mock_author'))
    def test_index_by_tag(self):
        # Test indexing pages by tag
        test_page1 = Page(self.db, "tagged_page_1", new_flag=True)
        test_page1.title = "Tagged Page 1"
        test_page1.tags = "tag1, tag2"
        test_page1.save()

        test_page2 = Page(self.db, "tagged_page_2", new_flag=True)
        test_page2.title = "Tagged Page 2"
        test_page2.tags = "tag2, tag3"
        test_page2.save()

        # Index pages with "tag2"
        tagged_pages = self.wiki.index_by_tag("tag2")

        self.assertEqual(len(tagged_pages), 2)

if __name__ == '__main__':
    unittest.main()