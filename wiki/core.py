"""
    Wiki core
    ~~~~~~~~~
"""
import re
from collections import OrderedDict
from datetime import *

import markdown
from flask import abort, session
from flask import url_for

from wiki import DataAccessObject


def clean_url(url):
    """
        Cleans the url and corrects various errors. Removes multiple
        spaces and all leading and trailing spaces. Changes spaces
        to underscores and makes all characters lowercase. Also
        takes care of Windows style folders use.

        :param str url: the url to clean


        :returns: the cleaned url
        :rtype: str
    """
    url = re.sub('[ ]{2,}', ' ', url).strip()
    url = url.lower().replace(' ', '_')
    url = url.replace('\\\\', '/').replace('\\', '/')
    return url


def wikilink(text, url_formatter=None):
    """
        Processes Wikilink syntax "[[Link]]" within the html body.
        This is intended to be run after content has been processed
        by markdown and is already HTML.

        :param str text: the html to highlight wiki links in.
        :param function url_formatter: which URL formatter to use,
            will by default use the flask url formatter

        Syntax:
            This accepts Wikilink syntax in the form of [[WikiLink]] or
            [[url/location|LinkName]]. Everything is referenced from the
            base location "/", therefore sub-pages need to use the
            [[page/subpage|Subpage]].

        :returns: the processed html
        :rtype: str
    """
    if url_formatter is None:
        url_formatter = url_for
    link_regex = re.compile(
        r"((?<!<code>)\[\[([^<].+?)\s*([|]\s*(.+?)\s*)?]])",
        re.X | re.U
    )
    for i in link_regex.findall(text):
        title = [i[-1] if i[-1] else i[1]][0]
        url = clean_url(i[1])
        html_url = "<a href='{0}'>{1}</a>".format(
            url_formatter('wiki.display', url=url),
            title
        )
        text = re.sub(link_regex, html_url, text, count=1)
    return text


class Processor(object):
    """
        The processor handles the processing of file content into
        metadata and markdown and takes care of the rendering.

        It also offers some helper methods that can be used for various
        cases.
    """

    preprocessors = []
    postprocessors = [wikilink]

    def __init__(self, text):
        """
            Initialization of the processor.

            :param str text: the text to process
        """
        self.md = markdown.Markdown(extensions=[
            'codehilite',
            'fenced_code',
            'meta',
            'tables'
        ])
        self.input = text
        self.markdown = None
        self.meta_raw = None
        self.pre = None
        self.html = None
        self.final = None
        self.meta = None

    def process_pre(self):
        """
            Content preprocessor.
        """
        current = self.input
        for processor in self.preprocessors:
            current = processor(current)
        self.pre = current

    def process_markdown(self):
        """
            Convert to HTML and extract metadata.
        """
        self.html = self.md.convert(self.input)
        self.meta_raw = self.md.Meta if hasattr(self.md, 'Meta') else {}

    def split_raw(self):
        if 'meta' in self.input:
            self.meta_raw = self.input['meta']
            self.markdown = self.input.get('content')

    def process_meta(self):
        """
        Processes the metadata from the Markdown processor.
        """
        self.meta = OrderedDict()
        if isinstance(self.meta_raw, dict):
            for key, value in self.meta_raw.items():
                self.meta[key.lower()] = '\n'.join(value) if isinstance(value, list) else value

    def process_post(self):
        """
            Content postprocessor.
        """
        current = self.html
        for processor in self.postprocessors:
            current = processor(current)
        self.final = current

    def process(self):
        """
            Runs the full suite of processing on the given text, all
            pre and post processing, markdown rendering, and metadata handling.
        """
        self.process_pre()
        self.process_markdown()
        self.process_meta()
        self.process_post()

        return self.final, self.markdown, self.meta


# in this class commented code is original code provided
class Page(object):
    """
    Represents a single page in the wiki.

    Attributes:
        db (pymongo.MongoClient): The database client used to interact with MongoDB.
        url (str): The URL of the wiki page, used as a unique identifier.
        collection (pymongo.collection.Collection): The MongoDB collection storing the wiki pages.
        _meta (OrderedDict): Metadata associated with the wiki page.
        new (bool): Indicates whether the page is new and not yet saved in the database.
    """

    def __init__(self, db, url, new_flag=False):
        """
            Initializes a new instance of the Page class.
           Parameters:
               db (pymongo.MongoClient): The database client.
               url (str): The URL of the wiki page.
               new (bool): True if the page is new, False otherwise. Default is False.
        """
        self.url = url
        self.collection = db.pages  # 'pages' is the MongoDB collection name
        self._meta = OrderedDict()
        self.new = new_flag
        self.content = ""
        self._html = ""
        self._tags = ""
        if not self.new:
            self.load()
            self.render()

    def __repr__(self):
        """
            Returns a string representation of the Page object.
            Returns:str: A string representation of the Page.
        """
        return "<Page: {}@{}>".format(self.url, self.path)

    # won't change as it is just processing pages
    def render(self):
        """
        Renders the page content from markdown to HTML if not already processed.
        """
        if not self._html:  # Only process if HTML content is not available
            processor = Processor(self.content)
            self._html, _, self._meta = processor.process()

    def load(self):
        """
        Loads the page content, metadata, processed HTML, and tags from the MongoDB database.
        """
        page_data = self.collection.find_one({"url": self.url})
        if page_data:
            self.content = page_data.get("content", "")
            self._html = page_data.get("html", "")
            self._meta = page_data.get("meta", {})
            self._tags = page_data.get("tags", "")  # Load tags
        else:
            self.content = ""
            self._html = ""
            self._meta = OrderedDict()
            self._tags = ""  # Initialize tags

    def save(self, update=True):
        """
        Saves the page content, metadata, processed HTML, and tags to the MongoDB database.
        """
        current_time = datetime.utcnow()
        page_data = {
            "url": self.url,
            "content": self.content,
            "meta": dict(self._meta),
            "tags": self._tags,  # Save tags
            "author": session.get('unique_id') or "",
            "updated_at": current_time
        }
        if self.new:
            page_data["created_at"] = current_time

        self.collection.update_one({"url": self.url}, {"$set": page_data}, upsert=True)
        if update:
            self.load()
            self.render()

    @property
    def tags(self):
        """
        Gets the tags associated with the page.
        Returns: str: The tags of the page.
        """
        return self._tags

    @tags.setter
    def tags(self, value):
        """
        Sets the tags for the page.
        Parameters:value (str): The tags to set for the page.
        """
        self._tags = value

    @property
    def meta(self):
        """
        Returns the metadata of the page.
        Returns:OrderedDict: The metadata of the page.
        """
        return self._meta

    def __getitem__(self, name):
        return self._meta.get(name, None)

    def __setitem__(self, name, value):
        self._meta[name] = value

    @property
    def html(self):
        return self._html

    def __html__(self):
        return self.html

    @property
    def title(self):
        """
        Gets the title of the page from its metadata.
        Returns:str: The title of the page.
        """
        # self.url is default value to return
        return self._meta.get('title', self.url)

    @title.setter
    def title(self, value):
        """
        Sets the title of the page in its metadata.
        Parameters:value (str): The title to set for the page.
        """
        self._meta['title'] = value


class Wiki(object):
    """
        Wiki class manages the interactions with the wiki pages stored in MongoDB.
        It provides methods to perform CRUD operations on wiki pages, as well as to search and index them.
        Attributes:
            collection (pymongo.collection.Collection): A MongoDB collection that stores the wiki pages.
        """

    def __init__(self):
        """
                Initializes the Wiki object by setting up the MongoDB collection.
        """
        self.collection = DataAccessObject.db.pages  # Use your MongoDB collection name

    def exists(self, url):
        """
        Checks if a wiki page exists in the database.
        Parameters:url (str): The URL of the wiki page to check.
        Returns:bool: True if the page exists, False otherwise.
        """
        return self.collection.count_documents({"url": url}) > 0

    def get(self, url):
        """
        Retrieves a wiki page by its URL if it exists.
        Parameters:url (str): The URL of the wiki page.
        Returns:Page: The Page object corresponding to the URL, or None if not found.
        """
        if self.exists(url):
            return Page(DataAccessObject.db, url)
        return None

    # to get all the pages by author
    def get_all(self):
        """
        Retrieves all wiki pages from the database that belong to an author.
        Returns:list[Page]: A list of all Page objects.
        """
        cursor = self.collection.find({"author": session.get('unique_id')})
        return [Page(DataAccessObject.db, doc['url']) for doc in cursor]

    def get_or_404(self, url):
        """
        Retrieves a wiki page by its URL or aborts with a 404 error if not found.
        Parameters:url (str): The URL of the wiki page.
        Returns:Page: The Page object corresponding to the URL.
        Raises:HTTPException: A 404 error if the page is not found.
        """
        page = self.get(url)
        if page:
            return page
        abort(404)

    def get_bare(self, url):
        """
        Retrieves a new Page object with a given URL if it does not exist in the database.
        Parameters:url (str): The URL of the wiki page.
        Returns:Page: A new Page object if the URL does not exist, False otherwise.
        """
        if not self.exists(url):
            return Page(DataAccessObject.db, url, new_flag=True)
        return False

    def move(self, old_url, new_url):
        """
        Moves a wiki page from an old URL to a new URL.
        Parameters:
            old_url (str): The current URL of the wiki page.
            new_url (str): The new URL for the wiki page
        Raises:RuntimeError: If a page with the new URL already exists.
        """
        if self.exists(new_url):
            raise RuntimeError('Target URL already exists: %s' % new_url)
        self.collection.update_one({"url": old_url}, {"$set": {"url": new_url}})

    def delete(self, url):
        """
        Deletes a wiki page from the database
        Parameters:url (str): The URL of the wiki page to delete.
        Returns:bool: True if the page was successfully deleted, False otherwise.
        """
        result = self.collection.delete_one({"url": url})
        return result.deleted_count > 0

    def index(self):
        """
        Retrieves an index of all wiki pages.
        Returns:list[Page]: A list of all Page objects in the database.
        """
        cursor = self.collection.find({})
        return [Page(DataAccessObject.db, doc['url']) for doc in cursor]

    def index_by(self, key):
        """
          Retrieves an index of wiki pages, organized by a specified attribute.
          Parameters:key (str): The attribute by which to organize pages.

          Returns:dict: A dictionary where keys are attribute values and values are lists of Page objects.
          """
        pages = {}
        for page in self.index():
            value = getattr(page, key, None)
            if value:
                pages.setdefault(value, []).append(page)
        return pages

    def get_by_title(self, title):
        """
        Retrieves a wiki page by its title.
        Parameters:title (str): The title of the wiki page.
        Returns:dict: The MongoDB document for the page, or None if not found.
        """
        # META IS WHERE EVERYTHING IS STORED INSIDE OUR COLLECTION (EXCEPT URL)
        return self.collection.find_one({"meta.title": title})

    def get_tags(self):
        """
        Retrieves a dictionary of all tags and the pages associated with each tag.
        """
        cursor = self.collection.find({})
        tags = {}
        for doc in cursor:
            page_tags = doc.get("tags", "").split(',')
            for tag in page_tags:
                tag = tag.strip()
                if tag:
                    tags.setdefault(tag, []).append(Page(DataAccessObject.db, doc['url']))
        return tags

    def index_by_tag(self, tag):
        """
        Retrieves a list of pages that have a specific tag.
        """
        cursor = self.collection.find({"tags": {"$regex": tag, "$options": "i"}})
        return [Page(DataAccessObject.db, doc['url']) for doc in cursor]

    def search(self, term, ignore_case=True, attrs=['title', 'tags', 'body']):
        regex = re.compile(term, re.IGNORECASE if ignore_case else 0)
        matched = []
        for attr in attrs:
            query = {"$regex": regex.pattern, "$options": "i"} if ignore_case else regex.pattern
            cursor = self.collection.find({f"meta.{attr}": query})
            for doc in cursor:
                page = Page(DataAccessObject.db, doc['url'])
                if page not in matched:
                    matched.append(page)
        return matched

    def search_by_author(self, term, ignore_case=True):
        matched = []
        query = {"author": session.get('unique_id')}
        cursor = self.collection.find(query)

        for doc in cursor:
            page = Page(DataAccessObject.db, doc['url'])
            if page not in matched:
                matched.append(page)

        return matched
