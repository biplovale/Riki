"""
    Wiki core
    ~~~~~~~~~
"""
import re
from collections import OrderedDict
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
        r"((?<!\<code\>)\[\[([^<].+?) \s*([|] \s* (.+?) \s*)?]])",
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
            Convert to HTML.
        """
        self.html = self.md.convert(self.pre)

    def split_raw(self):
        """
            Split text into raw meta and content.
        """
        self.meta_raw, self.markdown = self.pre.split('\n\n', 1)

    def split_raw(self):
        split_result = self.pre.split('\n\n', 1)
        if len(split_result) == 2:
            self.meta_raw, self.markdown = split_result
        else:
            self.meta_raw = split_result[0]
            self.markdown = ""  # or some default value

    def process_meta(self):
        self.meta = OrderedDict()
        for line in self.meta_raw.split('\n'):
            key = line.split(':', 1)[0].lower()
            if key in self.md.Meta:
                self.meta[key] = '\n'.join(self.md.Meta[key])
            else:
                # Handle the missing key, perhaps log a warning or set a default value
                print(f"Warning: Metadata key '{key}' not found.")

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
            pre and post processing, markdown rendering and meta data
            handling.
        """
        self.process_pre()
        self.process_markdown()
        self.split_raw()
        self.process_meta()
        self.process_post()

        return self.final, self.markdown, self.meta

# in this class commented code is original code provided
class Page(object):

    def __init__(self, db, url, new=False):
        # MongoDB setup
        # instead of path(where page is stored we have database)
        self.db = DataAccessObject.db  # same as one in DataAccess class
        self.url = url
        self.collection = self.db.pages  # 'pages' is the MongoDB collection name
        self._meta = OrderedDict()
        self.new = new
        if not new:
            self.load()
            self.render()

    def __repr__(self):
        return "<Page: {}@{}>".format(self.url, self.path)


    def load(self):
        # Fetch page from MongoDB
        # collection name is page, initialized in constructor
        # url is like primary key. It is part of the collections schema
        page_data = self.collection.find_one({"url": self.url})
        if page_data:
            self.content = page_data.get("content", "")
            self._meta = page_data.get("meta", {})
        else:
            self.content = ""
            self._meta = OrderedDict()

    # won't change as it is just processing pages
    def render(self):
        processor = Processor(self.content)
        self._html, self.body, self._meta = processor.process()


    def save(self, update=True):
        # Prepare data for MongoDB storage
        page_data = {
            "url": self.url,
            "content": self.body,
            "meta": dict(self._meta),
            # session.get('unique_id') is basically authors name
            "author": session.get('unique_id') or ""
        }
        # Save or update page in MongoDB
        self.collection.update_one({"url": self.url}, {"$set": page_data}, upsert=True)
        if update:
            self.load()
            self.render()

    @property
    def meta(self):
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
        # self.url is default value to return
        return self._meta.get('title', self.url)

    @title.setter
    def title(self, value):
        # self['title'] = value
        self._meta['title'] = value

    @property
    def tags(self):
        return self._meta.get('tags', '')

    @tags.setter
    def tags(self, value):
        self._meta['tags'] = value


# in this class commented code is original code provided
class Wiki(object):
    def __init__(self):
        self.collection = DataAccessObject.db.pages  # Use your MongoDB collection name


    def exists(self, url):
        return self.collection.count_documents({"url": url}) > 0

    def get(self, url):
        if self.exists(url):
            return Page(DataAccessObject.db, url)
        return None

    # to get all the pages by author
    def get_all(self):
        pass

    def get_or_404(self, url):
        page = self.get(url)
        if page:
            return page
        abort(404)

    def get_bare(self, url):
        if not self.exists(url):
            return Page(DataAccessObject.db, url, new=True)
        return False


    def move(self, old_url, new_url):
        if self.exists(new_url):
            raise RuntimeError('Target URL already exists: %s' % new_url)
        self.collection.update_one({"url": old_url}, {"$set": {"url": new_url}})

    def delete(self, url):
        result = self.collection.delete_one({"url": url})
        return result.deleted_count > 0

    '''def index(self): 
        """
            Builds up a list of all the available pages.

            :returns: a list of all the wiki pages
            :rtype: list
        """
        # make sure we always have the absolute path for fixing the
        # walk path
        pages = []
        root = os.path.abspath(self.root)
        for cur_dir, _, files in os.walk(root):
            # get the url of the current directory
            cur_dir_url = cur_dir[len(root)+1:]
            for cur_file in files:
                path = os.path.join(cur_dir, cur_file)
                if cur_file.endswith('.md'):
                    url = clean_url(os.path.join(cur_dir_url, cur_file[:-3]))
                    page = Page(path, url)
                    pages.append(page)
        return sorted(pages, key=lambda x: x.title.lower()) '''

    '''def index_by(self, key):
        """
            Get an index based on the given key.

            Will use the metadata value of the given key to group
            the existing pages.

            :param str key: the attribute to group the index on.

            :returns: Will return a dictionary where each entry holds
                a list of pages that share the given attribute.
            :rtype: dict
        """
        pages = {}
        for page in self.index():
            value = getattr(page, key)
            pre = pages.get(value, [])
            pages[value] = pre.append(page)
        return pages
        '''

    def index(self):
        cursor = self.collection.find({})
        return [Page(DataAccessObject.db, doc['url']) for doc in cursor]

    def index_by(self, key):
        pages = {}
        for page in self.index():
            value = getattr(page, key, None)
            if value:
                pages.setdefault(value, []).append(page)
        return pages

    def get_by_title(self, title):
        # META IS WHERE EVERYTHING IS STORED INSIDE OUR COLLECTION (EXCEPT URL)
        return self.collection.find_one({"meta.title": title})

    def get_tags(self):
        cursor = self.collection.find({})
        tags = {}
        for doc in cursor:
            pagetags = doc.get("meta", {}).get("tags", "").split(',')
            for tag in pagetags:
                tag = tag.strip()
                if tag:
                    tags.setdefault(tag, []).append(Page(DataAccessObject.db, doc['url']))
        return tags

    def index_by_tag(self, tag):
        cursor = self.collection.find({"meta.tags": {"$regex": tag, "$options": "i"}})
        return [Page(DataAccessObject.db, doc['url']) for doc in cursor]

    def search(self, term, ignore_case=True, attrs=['title', 'tags', 'body']):
        regex = re.compile(term, re.IGNORECASE if ignore_case else 0)
        matched = []

        for attr in attrs:
            query = {"$regex": regex.pattern, "$options": "i"} if ignore_case else regex.pattern
            # cursor IS an iterable
            # THERE ARE sub document 'title', 'tags', 'body IN meta
            cursor = self.collection.find({f"meta.{attr}": query})

            for doc in cursor:
                page = Page(DataAccessObject.db, doc['url'])
                if page not in matched:
                    matched.append(page)

        return matched
