import json
from flask import current_app as app
from bs4 import BeautifulSoup, Comment

from itviec.helpers import fetch_url


class EmployerFeed:

    def __init__(self, **kwargs):
        self.url = app.config["EMPLOYERS_JSON_URL"]
        # self.json = fetch_url(self.url).json()
        self.response = fetch_url(self.url)
        self.json = self.response.json()
        # print(self.json)
        # self.json = json.load(json_string)

    def __len__(self):
        return len(self.json)

    def __repr__(self):
        return "<EmployerFeed>"

    def __iter__(self):
        return self.json.__iter__()


class EmployerParser:

    def __init__(self, code):
        self.code = code
        self.emp = None
        self.reviews = None

    def get_url(self):
        return app.config["TEMPLATE_EMPLOYER_URL"].format(self.code)

    def fetch_and_parse(self):
        url = self.get_url()
        print("Fetching url: {}".format(url))
        response = fetch_url(url)
        self.emp = self.parse_employer_page(response.text)

    def digest(self):
        self.emp["overview"] = "<overview len={}>".format(len(self.emp["overview"]))

        jobs = []
        for job in self.emp["jobs"]:
            jobs.append("<Job:{}>".format(job["url"]))
        self.emp["jobs"] = jobs

    def fetch_and_parse_reviews(self):
        self.reviews = []
        feed = ReviewsFeed(self.code)
        for review_tag in feed.reviews():
            try:
                self.reviews.append(ReviewParser(review_tag))
            except:
                print(review_tag)

    def parse_employer_page(self, html):
        '''
        - Div: company-page
            - Div::cover-images-desktop
            - Div::headers hidden-xs: Info
            - Div::row company-container
                - Div::col-md-8 col-left
                    - UL::navigation
                    - Last update comment
                    - Div::panel panel-default: Description
                    - Jobs comment
                    - Div::panel panel-default jobs: Jobs
                    - Last update comment
                    - Div::panel panel-default: Why
                    - Our people comment
                    - Location comment
                    - Div::panel panel-default: Location
                - Div::col-md-4 col-right: Reviews info
        '''
        bs = BeautifulSoup(html, "html.parser")

        emp = {'code': self.code, "jobs": [], "why": {}, "locations": [], "our_people": None}

        company_tag = bs.div.find(class_="company-page")

        # ############################# #
        # Company general info / Header #
        # ############################# #
        header_tag = company_tag.select("div.headers.hidden-xs")[0]

        def _parse_header(header_tag):
            emp = {}

            # Logo: div::logo-container
            logo_container_tag = header_tag.find("div", class_="logo-container")
            logo_tag = logo_container_tag.find("img")
            emp["logo"] = logo_tag["data-src"]

            # c name-and-info
            # name: h1::title
            name_tag = header_tag.find("h1")
            emp["name"] = name_tag.string.strip()

            # location: location
            nni_tag = header_tag.find("div", class_="name-and-info")
            location_tag = nni_tag.find("span")
            emp["location"] = location_tag.contents[2].strip()

            # Industry: span::gear-icon
            industry_tag = header_tag.find("span", class_="gear-icon")
            if industry_tag:
                emp["industry"] = industry_tag.string.strip()
            else:
                emp["industry"] = None

            # Employees: span::group-icon
            employees_tag = header_tag.find("span", class_="group-icon")
            if employees_tag:
                emp["employees"] = employees_tag.string.strip()
            else:
                emp["employees"] = None

            # Country: div::country span::name
            country_div = header_tag.find("div", class_="country")
            if country_div:
                country_span = country_div.find("span")
                emp["country"] = country_span.string.strip()
            else:
                emp["country"] = None

            # Working days: div::working-date span
            w_days_div = header_tag.find("div", class_="working-date")
            if w_days_div:
                w_days_span = w_days_div.find("span")
                emp["working_days"] = w_days_span.string.strip()
            else:
                emp["working_days"] = None

            # Overtime: div::overtime
            overtime_div = header_tag.find("div", class_="overtime")
            if overtime_div:
                overtime_span = overtime_div.find("span")
                emp["overtime"] = overtime_span.string.strip()
            else:
                emp["overtime"] = None

            return emp

        emp.update(_parse_header(header_tag))

        # ###################### #
        # Container Left Columnn #
        # ###################### #

        left_column = company_tag.find(class_="col-md-8 col-left")
        for child in left_column.children:
            if child.__class__.__name__ is 'Comment':
                if child.string.startswith(" Last updated:"):
                    last_upd = child.string
                    emp["last_updated"] = last_upd[last_upd.find('"') + 1:-1]
                    break

        # ############## #
        # Overview Panel #
        # ############## #

        # Navigation
        nav = left_column.find("ul", class_="navigation")
        reviews_count = nav.select("li.review-tab")[0].find("a").string
        emp["review_count"] = int(reviews_count[:reviews_count.find("Review")] or 0)
        emp["website"] = nav.find("a", class_="ion-android-open")["href"]

        emp["review_rate"] = None
        emp["review_recommend"] = None

        try:
            ratings_panel = company_tag.select("div.company-ratings")[0]

            ratings_tag = ratings_panel.find("span", "company-ratings__star-point")
            emp["review_ratings"] = float(ratings_tag.string)

            recommend_tag = ratings_panel.find("td", "chart")
            emp["review_recommend"] = int(recommend_tag["data-rate"])
        except (AttributeError, IndexError):
            pass

        # Overview panel
        overview_div = left_column.find("div", class_="panel panel-default")
        emp["overview"] = str(overview_div)
        skills_tag = overview_div.find("ul", class_="employer-skills")
        emp["tags"] = []
        for skill_link in skills_tag.find_all("a"):
            emp["tags"].append(skill_link.string)

        for panel_tag in left_column.select("div.panel-default"):
            header_tag = panel_tag.select("div.panel-heading")[0]
            panel_header_text = header_tag.text.strip()

            # Jobs panel
            if panel_header_text == "Jobs":
                jobtag_iterator = JobTagIterator(panel_tag)
                for job_tag in jobtag_iterator:
                    emp["jobs"].append(JobTagParser(job_tag).get_dict())

            # Why panel
            if panel_header_text == "Why You'll Love Working Here":

                def _parse_why_panel(panel_tag):

                    why = {"reasons": [], "environment": [], "paragraph": []}

                    panel_body_tag = panel_tag.find("div", class_="panel-body")

                    # Reasons
                    reasons_tag = panel_body_tag.find("ul", class_="reasons numbered list")
                    for li_tag in reasons_tag.find_all("li", class_="item"):
                        span_tag = li_tag.find("span", class_="content paragraph")
                        why["reasons"].append(span_tag.text)

                    # Environment
                    carousel_tag = panel_body_tag.find("div", class_="carousel-inner")
                    if carousel_tag:
                        for img_div in carousel_tag.find_all("div", class_="img"):
                            if img_div.__class__.__name__ != "Tag":
                                continue
                            if "style" in img_div.attrs:
                                # get img
                                style = img_div["style"]
                                url = style[style.find("(") + 1:style.find(")")]
                                img_url = url[0:url.find("?")]

                                # get caption
                                caption = ""
                                for sibling_tag in img_div.next_siblings:
                                    if sibling_tag.__class__.__name__ != "Tag":
                                        continue
                                    caption = sibling_tag.text
                                    break

                                why["environment"].append({"img": img_url, "caption": caption})
                            else:
                                why["environment"].append({"tag": str(img_div.contents[1])})

                    # Paragraph
                    paragraph_tag = panel_body_tag.find("div", class_="paragraph")
                    why["paragraph"] = str(paragraph_tag)
                    # why["paragraph"] = "".join(str(paragraph_tag.contents))

                    return why

                emp["why"] = _parse_why_panel(panel_tag)

            # Locations panel
            if panel_header_text == "Our People":
                emp["our_people"] = str(panel_tag.find("div", class_="panel-body our-people"))

            # Locations panel
            if panel_header_text.startswith("Location"):
                location_column = panel_tag.find("div", class_="col-md-3 hidden-xs")

                for address_tag in location_column.select("div.full-address"):
                    addr_parts = [addr_part for addr_part in address_tag.strings]
                    full_address = ", ".join(addr_parts).strip()

                    emp["locations"].append(full_address)

        return emp

    def get_dict(self):
        return self.emp

    def get_full_dict(self):
        temp = {}
        temp.update(self.emp)
        temp["reviews"] = self.reviews
        return temp

    def get_json(self):
        return json.dumps(self.emp, sort_keys=True, indent=4)

    def save_json(self):
        filename = "{}/employers/{}.json".format(app.instance_path, self.emp["code"])
        with open(filename, 'w') as json_file:
            json.dump(self.emp, json_file, sort_keys=True, indent=4)


class ReviewsFeed:

    def __init__(self, code):
        self.code = code

    def url(self):
        return app.config["TEMPLATE_EMPLOYER_REVIEW_URL"].format(self.code)

    def __iter__(self):
        return ReviewPageIterator(self.url())

    def reviews(self):
        for page in ReviewPageIterator(self.url()):
            print(page)
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

        print(self.url)
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

        self.panel_tag = panel_tag
        self.next_block = self.panel_tag.find_next(class_="content-of-review")

    def __iter__(self):
        return self

    def __next__(self):
        if self.next_block is None:
            raise StopIteration("No more blocks in page")

        block = self.next_block
        self.next_block = self.next_block.find_next(class_="content-of-review")
        return block


class ReviewParser:

    def __init__(self, review_tag):
        self.review = {}

        # print(review_tag.previous_sibling.__class__.__name__)
        # print(review_tag.previous_sibling.previous_sibling.__class__.__name__)

        is_full_review = False
        previous_tag = review_tag.previous_sibling.previous_sibling
        if previous_tag.__class__.__name__ is "Comment":
            is_full_review = True
            self.review["last_update"] = previous_tag.string.split('"')[1]

        # print("Is full review: {}".format(is_full_review))
        # short summary tag
        short_summary_tag = review_tag.find("div", class_="short-summary row")

        # r.title: h3 short-title
        title = short_summary_tag.find("h3", class_="short-title").string.strip()
        self.review["title"] = title

        # div: stars-and-recommend
        # r.stars
        stars_tag = short_summary_tag.find("div", class_="stars")

        # general rating
        round_tag = stars_tag.find("span", class_="round-rate-rating-stars-box")
        unchecked = len(round_tag.find_all("span", class_="fa-stack unchecked"))
        self.review["stars_total"] = 5 - unchecked

        # specific rating
        stars_ul = stars_tag.find("ul", class_="hidden-sm hidden-xs detail-rating-tooltip")
        # print(stars_ul)
        categories = ["salary", "training", "management", "culture", "workspace"]
        for li_tag in stars_ul.find_all("li"):
            for span in li_tag.find_all("span", class_="round-rate-rating-bar"):
                unchecked = len(span.find_all("span", class_="fa fa-square unchecked"))
                self.review["stars_" + categories.pop(0)] = 5 - unchecked

        # r.recommend
        recomend_tag = short_summary_tag.find("div", class_="recommend")
        recomend_span = recomend_tag.find("span")
        self.review["recommend"] = recomend_span["class"][0] == "yes"

        # r.date
        date = short_summary_tag.find("div", class_="date").string.strip()
        self.review["date"] = date

        # details review
        details_review_tag = review_tag.find("div", class_="details-review")

        is_blurred = False
        if "blur" in details_review_tag["class"]:
            is_blurred = True
        # print("Is blurred: {}".format(is_blurred))

        if not is_blurred:
            # Liked
            liked_tag = details_review_tag.find("div", class_="what-you-liked")
            liked_paragraph = ""
            if liked_tag:
                for item in liked_tag.p.contents:
                    if item.__class__.__name__ is "NavigableString":
                        liked_paragraph = "".join((liked_paragraph, item))

            self.review["liked"] = liked_paragraph

            # Hated
            hated_tag = details_review_tag.find("div", class_="feedback")
            hated_paragraph = ""
            if hated_tag:
                for item in hated_tag.p.contents:
                    if item.__class__.__name__ is "NavigableString":
                        hated_paragraph = "".join((hated_paragraph, item))

            self.review["hated"] = hated_paragraph

    def employer_reviews_parser(html):
        bs = BeautifulSoup(html, "html.parser")

        # cr_div = bs.find('div',class_="company-review")
        # print(first_line(cr_div))
        # msg('')
        # for t in cr_div.children:
        # msg(first_line(t))
        # msg('')
        # cc_div = bs.find('div',class_="row company-container")

        # Left column
        left_column = bs.find("div", class_="col-md-8 col-left")
        # print(first_line(col_left))

        # ratings and reviews
        r_n_r = {}

        # number of reviews
        nav = left_column.find("ul", class_="navigation")
        count_tag = nav.find_all("a", limit=2)[1]
        count_tag
        # msg("count_tag: " + str(count_tag))
        reviews_count = count_tag.string.split(" ")[0]
        try:
            r_n_r["reviews_count"] = int(reviews_count)
            # msg("reviews: " + str(r_n_r["reviews_count"]))

            # stars: panel panel-default
            panel_div = left_column.find("div", class_="panel panel-default")
            rate_div = panel_div.find("p", class_="start-point")
            if rate_div:
                r_n_r['ratings']['overall'] = float(rate_div.string.split(" ")[0])
                # msg("Rating overall: " + str(r_n_r['ratings']['overall']))

                # recommended
                r_n_r['ratings']['recommended'] = int(panel_div.find("td")["data-rate"])
                # msg("Recommended: " + str(r_n_r['ratings']['recommended']))

                # ratings: table: ratings-specific
                ratings_tbl = left_column.find("table", class_="ratings-specific")

                for row in ratings_tbl.find_all("tr"):
                    # msg(first_line(row))
                    row.contents
                    # msg("row.contents: " + str(row.contents) )

                    td_name = row.contents[1].span.string
                    td_rate = row.contents[5].string.split()[0]

                    # msg("td_name: " + str(td_name) )
                    # msg("td_rate: " + str(td_rate) )

                    r_n_r['ratings'][td_name] = td_rate
            else:
                r_n_r['ratings']['overall'] = None
                r_n_r['ratings']['recommended'] = None
        except:
            pass

        # reviews: panel-body content-review disable-user-select
        review_panel_div = left_column.find(
            "div", class_="panel-body content-review disable-user-select"
        )

        r_n_r['reviews'] = []

        # div: company-review
        # - Headline Photo comment
        # - Header Information comment
        # - div: headers hidden-xs
        # - div: row company-container
        #   - div: col-md-8 col-left
        #     - Navigation comment
        #     - ul: navigation
        #     - Details Review Calculation comment
        #     - panel panel-default
        #     - Have you worked? comment
        #     - Details Content of Review comment
        #     - div: panel panel-default
        #       - div: panel-body content-review disable-user-select
        #         - First review comment

        #         - Last updated comment
        #         - div: content-of-review

        #         - Last updated comment
        #         - div: content-of-review

        #         - ...

        # div: content-of-review
        # - div: short-summary row
        # - div: details-review (blur)
        #   - div: what-you-liked
        #   - div: feedback

        if review_panel_div:
            for review_tag in review_panel_div.find_all("div", class_="content-of-review"):
                current_review = {}

                # print(review_tag.previous_sibling.__class__.__name__)
                # print(review_tag.previous_sibling.previous_sibling.__class__.__name__)

                is_full_review = False
                previous_tag = review_tag.previous_sibling.previous_sibling
                if previous_tag.__class__.__name__ is "Comment":
                    is_full_review = True
                    current_review["last_update"] = previous_tag.string.split('"')[1]

                # print("Is full review: {}".format(is_full_review))
                # short summary tag
                short_summary_tag = review_tag.find("div", class_="short-summary row")

                # r.title: h3 short-title
                title = short_summary_tag.find("h3", class_="short-title").string.strip()
                current_review["title"] = title

                # div: stars-and-recommend
                # r.stars
                stars_tag = short_summary_tag.find("div", class_="stars")

                # general rating
                round_tag = stars_tag.find("span", class_="round-rate-rating-stars-box")
                unchecked = len(round_tag.find_all("span", class_="fa-stack unchecked"))
                current_review["stars_total"] = 5 - unchecked

                # specific rating
                stars_ul = stars_tag.find("ul", class_="hidden-sm hidden-xs detail-rating-tooltip")
                # print(stars_ul)
                categories = ["salary", "training", "management", "culture", "workspace"]
                for li_tag in stars_ul.find_all("li"):
                    for span in li_tag.find_all("span", class_="round-rate-rating-bar"):
                        unchecked = len(span.find_all("span", class_="fa fa-square unchecked"))
                        current_review["stars_" + categories.pop(0)] = 5 - unchecked

                # r.recommend
                recomend_tag = short_summary_tag.find("div", class_="recommend")
                recomend_span = recomend_tag.find("span")
                current_review["recommend"] = recomend_span["class"][0] == "yes"

                # r.date
                date = short_summary_tag.find("div", class_="date").string.strip()
                current_review["date"] = date

                # details review
                details_review_tag = review_tag.find("div", class_="details-review")

                is_blurred = False
                if "blur" in details_review_tag["class"]:
                    is_blurred = True
                # print("Is blurred: {}".format(is_blurred))

                if not is_blurred:
                    # Liked
                    liked_tag = details_review_tag.find("div", class_="what-you-liked")
                    liked_paragraph = ""
                    if liked_tag:
                        for item in liked_tag.p.contents:
                            if item.__class__.__name__ is "NavigableString":
                                liked_paragraph = "".join((liked_paragraph, item))

                    current_review["liked"] = liked_paragraph

                    # Hated
                    hated_tag = details_review_tag.find("div", class_="feedback")
                    hated_paragraph = ""
                    if hated_tag:
                        for item in hated_tag.p.contents:
                            if item.__class__.__name__ is "NavigableString":
                                hated_paragraph = "".join((hated_paragraph, item))

                    current_review["hated"] = hated_paragraph

                r_n_r['reviews'].append(current_review)

        # print(r_n_r)
        return r_n_r

    def __repr__(self):
        return "<ReviewParser rec:{} rating:{} next:{}>".format(self.review["recommend"], self.review["stars_total"], self.review["title"])


# Job #########################################################################
class JobTagParser:
    def __init__(self, job_tag):
        self.tag = job_tag

        self.job = {}
        self.job["id"] = job_tag["id"][4:]
        self.job["last_update"] = (
            job_tag.find_next(string=lambda text: isinstance(text, Comment))
            .extract()
            .split('"')[1]
        )
        self.job["title"] = job_tag.find_all("a")[1].text.strip()
        self.job["employer_code"] = job_tag.find_all("a", {"target": "_blank"})[0]["href"].split("/")[-1]
        self.job["url"] = job_tag.find("div", class_="details").a["href"]
        self.job["salary"] = job_tag.find_all("span", class_="salary-text")[0].text.strip()
        self.job["address"] = (
            job_tag.find_all("div", class_="address")[0].text.strip().split("\n\n\n")
        )
        self.job["tags"] = (
            job_tag.find_all("div", class_="tag-list")[0].text.strip().split("\n\n\n")
        )
        self.job["description"] = job_tag.find_all("div", class_="description")[0].text.strip()

    def get_dict(self):
        return self.job

    def get_json(self):
        return json.dumps(self.job, sort_keys=True, indent=4)

    def save_json(self):
        filename = "{}/jobs/{}.json".format(app.instance_path, self.job["id"])
        with open(filename, 'w') as json_file:
            json.dump(self.job, json_file, sort_keys=True, indent=4)


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
        # print( type(a).__name__ )
        next_url = a["href"] if type(a).__name__ is "Tag" else ""
        # print("Next URL: " + next_url)

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
        elif content.__class__.__name__ is "Tag":
            self.job_panel_tag = content
        else:
            self.job_panel_tag = BeautifulSoup(content, "html.parser")

        self.next_block = self.job_panel_tag.find_next(class_="job")

    def __next__(self):
        if self.next_block is None:
            raise StopIteration("No more blocks in page")

        job_block = self.next_block
        self.next_block = self.next_block.find_next(class_="job")
        return job_block

    def __iter__(self):
        return self


class ReviewPage(JobPage):
    def __iter__(self):
        return ReviewIterator(self.content)

    def __repr__(self):
        return "<ReviewPage url:{} next:{}>".format(self.url, self.next_p)
