import json
from bs4 import BeautifulSoup, Comment
from flask import current_app as app

from itviec.helpers import fetch_url, first_line
import config

from pprint import pprint


def parse_employer(html, code):
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

    emp = {
        'code': code,
        # 'url': Config.TEMPLATE_EMPLOYER_URL.format(code)
    }

    company_tag = bs.div.find(class_="company-page")

    # ############################# #
    # Company general info / Header #
    # ############################# #
    header_tag = company_tag.find("div", class_="headers hidden-xs")

    # Logo: div::logo-container
    logo_container_tag = header_tag.find("div", class_="logo-container")
    logo_tag = logo_container_tag.find("img")
    emp["logo"] = logo_tag["data-src"]
    # msg("Logo: '{}'".format(emp["logo"]))

    # c name-and-info
    # name: h1::title
    name_tag = header_tag.find("h1")
    emp["name"] = name_tag.string.strip()
    # msg("Company name: '{}'".format(emp["name"]))

    # location: location
    nni_tag = header_tag.find("div", class_="name-and-info")
    location_tag = nni_tag.find("span")
    emp["location"] = location_tag.contents[2].strip()
    # msg("Company location: '{}'".format(emp["location"]))

    # Industry: span::gear-icon
    industry_tag = header_tag.find("span", class_="gear-icon")
    emp["industry"] = industry_tag.string.strip()
    # msg("Company industry: '{}'".format(emp["industry"]))

    # Employees: span::group-icon
    employees_tag = header_tag.find("span", class_="group-icon")
    emp["employees"] = employees_tag.string.strip()
    # msg("Company employees: '{}'".format(emp["employees"]))

    # Country: div::country span::name
    country_div = header_tag.find("div", class_="country")
    country_span = country_div.find("span")
    emp["country"] = country_span.string.strip()
    # msg("Company country: '{}'".format(emp["country"]))

    # Working days: div::working-date span
    w_days_div = header_tag.find("div", class_="working-date")
    # print(header_tag)
    # print(first_line(w_days_div))
    if w_days_div:
        w_days_span = w_days_div.find("span")
        emp["working_days"] = w_days_span.string.strip()
    else:
        emp["working_days"] = None
    # msg("Company working days: '{}'".format(emp["working_days"]))

    # Overtime: div::overtime
    overtime_div = header_tag.find("div", class_="overtime")
    # print(first_line(overtime_div))
    if overtime_div:
        overtime_span = overtime_div.find("span")
        emp["overtime"] = overtime_span.string.strip()
    else:
        emp["overtime"] = None
    # msg("Overtime: '{}'".format(emp["overtime"]))

    # ###################### #
    # Container Left Columnn #
    # ###################### #

    left_column = company_tag.find(class_="col-md-8 col-left")
    # print(first_line(col_left))

    # Panel description
    # Navigation
    # website
    nav = left_column.find("ul", class_="navigation")
    emp["website"] = nav.find("a", class_="ion-android-open")["href"]
    # msg("Website: " + emp["website"])

    # TODO: facebook

    # Panel header
    panel_div = left_column.find("div", class_="panel panel-default")
    emp["panel"] = panel_div
    # msg("Panel: " + str(emp["panel"]))
    # emp["header"] = panel_div.find("h3", class_="panel-title headline")\
    #     .string.strip()
    # msg("Header: " + emp["header"])

    # Panel body
    # panel_b_div = col_left.find("div", class_="panel-body")
    # paragraph1 = panel_b_div.find("div", class_="paragraph")\
    #     .contents[1].contents[0]
    # paragraph2 = paragraph1.contents[0]
    # msg("Paragraph class: " + class_name(paragraph2))
    # msg("Paragraph: " + str(paragraph2))

    # Panel jobs: panel panel-default jobs
    panel_jobs_div = left_column.find("div", class_="panel panel-default jobs")
    jobs_iterator = JobIteratorInPage(panel_jobs_div)
    emp["jobs"] = []
    # for job_tag in JobIteratorInPage(panel_jobs_div):
    for job_tag in jobs_iterator:
        # print(job_tag)
        job_parser = JobSummaryParser(job_tag)
        job_dictionary = job_parser.get_dict()
        pprint(job_dictionary)
        emp["jobs"].append(job_dictionary)
    # msg("Jobs: " + str(panel_jobs_div))

    # emp["job_ids"] = []
    # if panel_jobs_div is not None:
    #     panel_body_div = panel_jobs_div.find("div", class_="panel-body")
    #     for div in panel_body_div.find_all("div", class_="job"):
    #         if class_name(div) != "Tag":
    #             continue
    #         jid = int(div["id"][4:])
    #         emp["job_ids"].append(jid)

    # msg("Jobs: " + str(jobs))

    # TODO: Panel why
    # TODO: Panel location

    # Ratings Stats ###########
    # Right col

    # Panel ratings
    # Stars
    # Recommended
    # #########################
    # emp["reviews"] = None

    return emp


def parse_employer_review(html):
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


class JobSummaryParser():
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
        filename = "{}/jobs/{}.json".format(config.Config.INSTANCE_DIR, self.job["id"])
        with open(filename, 'w') as json_file:
            json.dump(self.job, json_file, sort_keys=True, indent=4)


# EmployerFeed #################################################
class EmployerFeed():

    def __init__(self, **kwargs):
        self.url = current_app.config["EMPLOYERS_JSON_URL"]
        # self.json = fetch_url(self.url).json()
        self.response = fetch_url(self.url)
        self.json = self.response.json()
        # print(self.json)
        # self.json = json.load(json_string)

    def __len__(self):
        return len(self.json)

    def __repr__(self):
        return "<EmployerFeed>"


# JobsFeed #################################################
class JobsFeed():

    def __init__(self, **kwargs):
        self.location = ''
        self.tags = ''

        if 'location' in kwargs:
            self.location = kwargs['location']

        if 'tags' in kwargs:
            self.tags = kwargs['tags']

    def url(self):
        feed_url = current_app.config["URL"]
        if self.tags:
            feed_url = feed_url + '/' + '-'.join(self.tags)
        if self.location:
            feed_url = feed_url + '/' + self.location
        return feed_url

    def __repr__(self):
        return "<Feed location='{}' tags='{}'>".format(self.location, self.tags)

    def __iter__(self):
        return PageIterator(self.url())

    def pages(self):
        return PageIterator(self.url())

    def job_tags(self):
        for page in PageIterator(self.url()):
            for job_tag in page:
                yield job_tag


# PageIterator #################################################
class PageIterator:
    def __init__(self, url):
        self.url = url

    def __iter__(self):
        return self

    def __next__(self):
        # Check if there is a url
        if self.url is None or self.url is "":
            raise StopIteration("Error: No URL for current iteration")

        # Fetch page
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
        page = Page(self.url, resp_json["jobs_html"], prev_url, next_url)
        # print("Page in It: " + str(page))

        self.url = next_url

        # Return html page
        return page


# Page ####################################################
class Page:
    def __init__(self, url, content, prev_p, next_p):
        self.url = url
        self.content = content
        self.prev_p = prev_p
        self.next_p = next_p

    def __iter__(self):
        return JobIteratorInPage(self.content)

    def __repr__(self):
        return "<Page url:{} prev:{} next:{}>".format(self.url, self.prev_p, self.next_p)


class JobIteratorInPage:
    def __init__(self, content):
        if content is None:
            raise Exception("Page is empty")
        elif content.__class__.__name__ is "str":
            self.job_panel_tag = BeautifulSoup(content, "html.parser")
        elif content.__class__.__name__ is "Tag":
            self.job_panel_tag = content
        # print( "Soup class: " + str(type(self.soup)) )

        # self.div = self.soup.div
        # print( "div tag class: " + str(type(self.div)) )

        # self.next_block = self.div.find_next(class_="job")
        self.next_block = self.job_panel_tag.find_next(class_="job")
        # print( "self.next_block class: " + str(type(self.next_block)) )
        # print("Next block: " + str(self.next_block).splitlines()[0])

    def __next__(self):
        # Check if there is a block
        if self.next_block is None:
            raise StopIteration("No more blocks in page")

        # job = Job.from_summary(self.next_block)
        job_block = self.next_block

        self.next_block = self.next_block.find_next(class_="job")
        # ~ print("Next block: "+str(self.next_block).splitlines()[0])

        return job_block
        # return job

    def __iter__(self):
        return self
