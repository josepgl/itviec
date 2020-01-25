from bs4 import BeautifulSoup
from flask import current_app as app

from itviec.helpers import fetch_url


# Employers feed
class EmployersFeed:

    def __init__(self, **kwargs):
        self.url = app.config["EMPLOYERS_JSON_URL"]
        self.response = fetch_url(self.url)
        self.json = self.response.json()

    def __len__(self):
        return len(self.json)

    def __repr__(self):
        return "<EmployerFeed>"

    def __iter__(self):
        return self.json.__iter__()


# Jobs Feed
class JobsFeed:
    '''JobsFeed can iterate over pages or over all job blocks over all pages.

    pages() is the page iterator returns Page objects on iterations:

    feed = JobsFeed()
    for page in feed.pages():
        print(page)

    job_tags() is the job iterator, returns BeautifulSoup Tag objects

    feed = JobsFeed()
    for job_tag in feed.job_tags():
        print(job_tag)

    The default iterator is over pages:

    feed = JobsFeed()
    for page in feed:
        print(page)
    '''

    def __init__(self, **kwargs):
        self.location = ''
        self.tags = ''

        if 'location' in kwargs:
            self.location = kwargs['location']

        if 'tags' in kwargs:
            self.tags = kwargs['tags']

    def url(self):
        feed_url = app.config["JOBS_URL"]
        if self.tags:
            feed_url = feed_url + '/' + '-'.join(self.tags)
        if self.location:
            feed_url = feed_url + '/' + self.location
        return feed_url

    def __repr__(self):
        return "<Feed location='{}' tags='{}'>".format(self.location, self.tags)

    def __iter__(self):
        return JobPageIterator(self.url())

    def pages(self):
        return JobPageIterator(self.url())

    def job_tags(self):
        for page in JobPageIterator(self.url()):
            for job_tag in page:
                yield job_tag


class JobPageIterator:
    def __init__(self, url):
        self.url = url

    def __iter__(self):
        return self

    def __next__(self):
        if self.url is None or self.url is "":
            raise StopIteration("Error: No URL for current iteration")

        response = fetch_url(self.url)
        resp_json = response.json()

        # Key:  suggestion
        # Key:  show_more_html
        # Key:  jobs_html

        # 1.- Next URL
        next_url_block = resp_json["show_more_html"]
        soup = BeautifulSoup(next_url_block, "html.parser")

        # Define the local variable
        next_url = None
        prev_url = None

        # Get next page url if exists
        a = soup.find("a", href=True, rel="next")
        next_url = a["href"] if type(a).__name__ is "Tag" else ""

        # Get previous page url if exists
        for a in soup.find_all("a", href=True, rel="prev"):
            prev_url = a["href"]
            break

        # Build page
        page = JobPage(self.url, resp_json["jobs_html"], prev_url, next_url)

        self.url = next_url

        return page


class JobPage:
    def __init__(self, url, content, prev_p, next_p):
        self.url = url
        self.content = content
        self.prev_p = prev_p
        self.next_p = next_p

    def __iter__(self):
        return JobTagIterator(self.content)

    def __repr__(self):
        return "<Page url:{} prev:{} next:{}>".format(self.url, self.prev_p, self.next_p)


class JobTagIterator:

    def __init__(self, content):
        if content is None:
            raise Exception("Page is empty")
        elif content.__class__.__name__ == "Tag":
            self.job_panel_tag = content
        else:
            self.job_panel_tag = BeautifulSoup(content, "html.parser")

        self.next_block = self.job_panel_tag.div

    def __next__(self):
        if self.next_block is None:
            raise StopIteration("No more blocks in page")

        job_block = self.next_block
        self.next_block = self.next_block.find_next(class_="job")
        return job_block

    def __iter__(self):
        return self


# Reviews Feed
class ReviewsFeed:

    def __init__(self, code):
        self.code = code

    def url(self):
        return app.config["TEMPLATE_EMPLOYER_REVIEW_URL"].format(self.code)

    def __iter__(self):
        return ReviewPageIterator(self.url())

    def reviews(self):
        for page in ReviewPageIterator(self.url()):
            for review_tag in page:
                yield review_tag


class ReviewPageIterator:

    def __init__(self, url):
        self.url = url

    def __iter__(self):
        return self

    def __next__(self):
        if self.url is None or self.url is "":
            raise StopIteration("Error: No URL for current iteration")

        response = fetch_url(self.url)
        prev_url = None
        next_url = None

        soup = BeautifulSoup(response.text, "html.parser")
        review_panel_tag = soup.find("div", class_="panel-body content-review disable-user-select")
        pagination_tag = soup.find("ul", class_="pagination")

        if pagination_tag:
            a_tag = pagination_tag.find("a", rel="next")
            if a_tag:
                next_url = app.config["BASE_URL"] + a_tag["href"]

        page = ReviewPage(self.url, review_panel_tag, prev_url, next_url)

        self.url = next_url

        return page


class ReviewIterator:

    def __init__(self, panel_tag):
        self.next_block = panel_tag

    def __iter__(self):
        return self

    def __next__(self):
        try:
            self.next_block = self.next_block.find_next(class_="content-of-review")
        except AttributeError:
            raise StopIteration

        if self.next_block.__class__.__name__ != "Tag":
            raise StopIteration

        return self.next_block


class ReviewPage(JobPage):
    def __iter__(self):
        return ReviewIterator(self.content)

    def __repr__(self):
        return "<ReviewPage url:{} next:{}>".format(self.url, self.next_p)
