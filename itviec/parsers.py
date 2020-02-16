import os
import json
from datetime import datetime, timedelta

from flask import current_app as app
from bs4 import BeautifulSoup, Comment

from itviec.feeds import ReviewsFeed
from itviec.helpers import fetch_url, to_json_file, to_json
from itviec.time import str_to_datetime
from itviec.feeds import JobTagIterator


def is_last_updated(tag):
    return tag.__class__.__name__ is 'Comment' \
        and tag.string.startswith(" Last updated:")


def get_last_updated(tag):
    _ = tag.string
    return _[_.find('"') + 1:-1]


def _get_employer_last_post(emp):
    if not len(emp["jobs"]):
        return emp["last_update"]
    return max([jt["last_post"] for jt in emp["jobs"]])


class EmployerParser:

    def __init__(self, code):
        self.code = code
        self.emp = {"reviews": []}

    def get_url(self):
        return app.config["TEMPLATE_EMPLOYER_URL"].format(self.code)

    def run(self):
        self.fetch_and_parse()
        self.fetch_and_parse_reviews()

    def fetch_and_parse(self):
        url = self.get_url()
        response = fetch_url(url)

        if response.text.find('employers_show') is -1:
            raise KeyError("Employer '{}' not found at {}".format(self.code, url))

        self.emp.update(self.parse_employer_page(response.text))

    def digest(self):
        self.emp["overview"] = "<overview len={}>".format(len(self.emp["overview"]))

        jobs = []
        for job in self.emp["jobs"]:
            jobs.append("<Job:{}>".format(job["url"]))
        self.emp["jobs"] = jobs

    def fetch_and_parse_reviews(self):
        feed = ReviewsFeed(self.code)
        for review_tag in feed.reviews():
            try:
                rev_p = ReviewParser(review_tag)
                self.emp["reviews"].append(rev_p.get_dict())
            except KeyError:
                print(review_tag)
                raise

    def parse_employer_page(self, html):
        '''Div: company-page
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
        emp = {
            'code': self.code,
            "jobs": [],
            "why": {},
            "addresses": [],
            "our_people": None
        }

        try:
            soup = BeautifulSoup(html, "html.parser")
            company_tag = soup.find("div", class_="company-page")
            header_tag = company_tag.select("div.headers.hidden-xs")[0]
        except AttributeError as e:
            print("Could not find 'company-page': {}".format(e))
            return None

        # ############################# #
        # Company general info / Header #
        # ############################# #
        emp.update(self._parse_header(header_tag))

        # ###################### #
        # Container Left Columnn #
        # ###################### #
        left_column = company_tag.find(class_="col-md-8 col-left")
        emp["last_update"] = self._parse_last_update(company_tag)

        # Navigation
        nav = left_column.find("ul", class_="navigation")
        emp["website"] = nav.find("a", class_="ion-android-open")["href"]

        # Review stats
        emp.update(self._parse_review_stats(company_tag))

        # ############## #
        # Overview Panel #
        # ############## #
        overview_div = left_column.find("div", class_="panel panel-default")
        emp["overview"] = str(overview_div)
        emp["tags"] = self._parse_employer_tags(overview_div)

        for panel_tag in left_column.select("div.panel-default"):
            header_tag = panel_tag.select("div.panel-heading")[0]
            panel_header_text = header_tag.text.strip()

            # Jobs panel
            if panel_header_text == "Jobs":
                emp["jobs"] = self._parse_jobs_panel(panel_tag)

            # Why panel
            if panel_header_text == "Why You'll Love Working Here":
                emp["why"] = self._parse_why_panel(panel_tag)

            # Locations panel
            if panel_header_text == "Our People":
                emp["our_people"] = str(panel_tag.find("div", class_="panel-body our-people"))

            # Locations panel
            if panel_header_text.startswith("Location"):
                emp["addresses"] = self._parse_location_panel(panel_tag)

        emp["last_post"] = _get_employer_last_post(emp)

        return emp

    def _parse_last_update(self, company_tag):
        left_column = company_tag.find(class_="col-md-8 col-left")
        for child in left_column.children:
            if is_last_updated(child):
                return get_last_updated(child)

    def _parse_header(self, header_tag):
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

    def _parse_review_stats(self, company_tag):
        emp = {}
        left_column = company_tag.find(class_="col-md-8 col-left")
        nav = left_column.find("ul", class_="navigation")

        # Review stats
        reviews_count = nav.select("li.review-tab")[0].find("a").string
        emp["review_count"] = int(reviews_count[:reviews_count.find("Review")] or 0)
        emp["review_ratings"] = None
        emp["review_recommend"] = None

        try:
            ratings_panel = company_tag.select("div.company-ratings")[0]

            ratings_tag = ratings_panel.find("span", "company-ratings__star-point")
            emp["review_ratings"] = float(ratings_tag.string)

            recommend_tag = ratings_panel.find("td", "chart")
            emp["review_recommend"] = int(recommend_tag["data-rate"])
        except (AttributeError, IndexError):
            if "VERBOSE" in app.config and app.config["VERBOSE"]:
                print("Ratings panel is missing")

        return emp

    def _parse_employer_tags(self, panel_tag):
        tags = []
        skills_tag = panel_tag.find("ul", class_="employer-skills")
        for skill_link in skills_tag.find_all("a"):
            tags.append(skill_link.string)
        return tags

    def _parse_jobs_panel(self, panel_tag):
        jobs = []
        panel_body_tag = panel_tag.find(class_="panel-body")
        for job_tag in JobTagIterator(panel_body_tag):
            job_d = JobTagParser(job_tag).get_dict()
            jobs.append(job_d)

        return jobs

    def _parse_why_panel(self, panel_tag):

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

        return why

    def _parse_location_panel(self, panel_tag):
        locations = []
        location_column = panel_tag.find("div", class_="col-md-3 hidden-xs")

        for address_tag in location_column.select("div.full-address"):
            addr_parts = [addr_part for addr_part in address_tag.strings]
            full_address = ", ".join(addr_parts).strip()
            locations.append(full_address)

        return locations

    def get_dict(self):
        return self.emp

    def get_json(self):
        return to_json(self.emp)

    def save_json(self):
        filename = "{}.json".format(self.emp["code"])
        filepath = os.path.join(app.config["EMPLOYERS_CACHE_DIR"], filename)
        to_json_file(self.get_dict(), filepath)


class ReviewParser:

    def __init__(self, review_tag):
        '''Parse content of review'''

        self.review = {}

        previous_tag = review_tag.previous_sibling.previous_sibling
        if previous_tag.__class__.__name__ is "Comment":
            self.review["last_update"] = previous_tag.string.split('"')[1]

        # short summary tag
        short_summary_tag = review_tag.find("div", class_="short-summary row")

        # title: h3 short-title
        title = short_summary_tag.find("h3", class_="short-title").string.strip()
        self.review["title"] = title

        # div: stars-and-recommend
        stars_tag = short_summary_tag.find("div", class_="stars")

        # general rating
        round_tag = stars_tag.find("span", class_="round-rate-rating-stars-box")
        unchecked = len(round_tag.find_all("span", class_="fa-stack unchecked"))
        self.review["stars_total"] = 5 - unchecked

        # specific rating
        stars_ul = stars_tag.find("ul", class_="hidden-sm hidden-xs detail-rating-tooltip")
        categories = ["salary", "training", "management", "culture", "workspace"]
        for li_tag in stars_ul.find_all("li"):
            for span in li_tag.find_all("span", class_="round-rate-rating-bar"):
                unchecked = len(span.find_all("span", class_="fa fa-square unchecked"))
                self.review["stars_" + categories.pop(0)] = 5 - unchecked

        # recommend
        recomend_tag = short_summary_tag.find("div", class_="recommend")
        recomend_span = recomend_tag.find("span")
        self.review["recommend"] = recomend_span["class"][0] == "yes"

        # date
        date = short_summary_tag.find("div", class_="date").string.strip()
        self.review["date"] = date

        # details review
        details_review_tag = review_tag.find("div", class_="details-review")

        is_blurred = False
        if "blur" in details_review_tag["class"]:
            is_blurred = True

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

    def get_dict(self):
        return self.review

    def employer_reviews_parser(self, html):
        soup = BeautifulSoup(html, "html.parser")

        # Left column
        left_column = soup.find("div", class_="col-md-8 col-left")

        # ratings and reviews
        r_n_r = {}

        # number of reviews
        nav = left_column.find("ul", class_="navigation")
        count_tag = nav.find_all("a", limit=2)[1]
        reviews_count = count_tag.string.split(" ")[0]
        try:
            r_n_r["reviews_count"] = int(reviews_count)

            # stars: panel panel-default
            panel_div = left_column.find("div", class_="panel panel-default")
            rate_div = panel_div.find("p", class_="start-point")
            if rate_div:
                r_n_r['ratings']['overall'] = float(rate_div.string.split(" ")[0])

                # recommended
                r_n_r['ratings']['recommended'] = int(panel_div.find("td")["data-rate"])

                # ratings: table: ratings-specific
                ratings_tbl = left_column.find("table", class_="ratings-specific")

                for row in ratings_tbl.find_all("tr"):
                    td_name = row.contents[1].span.string
                    td_rate = row.contents[5].string.split()[0]

                    r_n_r['ratings'][td_name] = td_rate
            else:
                r_n_r['ratings']['overall'] = None
                r_n_r['ratings']['recommended'] = None
        except TypeError as e:
            print("No reviews were found: {}".format(e))

        return r_n_r

    def __repr__(self):
        return "<ReviewParser rec:{} rating:{} next:{}>".format(self.review["recommend"], self.review["stars_total"], self.review["title"])


# Job #########################################################################
class JobParser:
    def __init__(self, job_code):
        self.code = job_code
        self.job = None

    def get_url(self):
        return "/".join((app.config["JOBS_URL"], self.code))

    def run(self):
        self.fetch_and_parse()

    def fetch_and_parse(self):
        url = self.get_url()
        response = fetch_url(url)

        if response.text.find('jobs_show') is -1:
            raise KeyError("Job '{}' not found at {}".format(self.code, url))

        self.job = self.parse_job_page(response.text)

    def parse_job_page(self, html):
        '''div: content
            - Comment: last updated
            - div: main-entity
              - div: side_bar
              - div: job-detail
                - div: header
                - div: job_reason_to_join_us
                - div: job_description
                - div: skills_experience
                - div: love_working_here
        '''
        job = {"code": self.code}

        soup = BeautifulSoup(html, "html.parser")
        div_content = soup.find("div", class_="content")

        side_bar = soup.find("div", class_="side_bar")
        _ = side_bar.find("a")["href"]
        job["employer_code"] = _[_.rfind("/") + 1:]

        job_detail = div_content.find("div", class_="job-detail")
        last_upd = div_content.contents[1].string
        _ = last_upd[last_upd.find('"') + 1:-1]
        job["last_update"] = _[:_.rfind(' ')]
        # Header
        # - job_info
        #   - h1: job_title
        #   - tag-list
        #   - salary
        #   - address
        header = job_detail.find("div", class_="header")
        job["title"] = header.find("h1", class_="job_title").string.strip()
        tag_list = header.find("div", class_="tag-list")
        job["tags"] = [tag.string.strip() for tag in tag_list.find_all("span")]
        job["salary"] = header.find("span", class_="salary-text").string.strip()
        job["distance"] = header.find("div", class_="distance-time-job-posted").contents[-1].strip()
        job["reasons"] = str(job_detail.find("div", class_="job_reason_to_join_us"))
        job["description"] = str(job_detail.find("div", class_="job_description"))
        job["skills_experience"] = str(job_detail.find("div", class_="skills_experience"))
        job["why"] = str(job_detail.find("div", class_="love_working_here"))
        job["addresses"] = self._get_locations(job_detail)
        job["last_post"] = get_post_date(job["last_update"], job["distance"])

        return job

    def _get_locations(self, job_detail_tag):
        header = job_detail_tag.find("div", class_="header")

        locations = []
        for address_tag in header.find_all("div", class_="address"):
            address_span = address_tag.span
            if address_span:
                full_address = "".join(address_tag.span.strings).strip()
                locations.append(full_address)
        return locations

    def digest(self):
        temp = {}
        temp.update(self.job)
        for key in temp:
            if temp[key].__class__.__name__ == "str":
                value_len = len(temp[key])
                if value_len > 100:
                    temp[key] = "<{} len:{}>".format(key, value_len)
        return temp

    def get_dict(self):
        return self.job

    def get_json(self):
        return to_json(self.job)

    def save_json(self):
        filename = "{}.json".format(self.job["code"])
        filepath = os.path.join(app.config["JOBS_CACHE_DIR"], filename)
        to_json_file(self.get_dict(), filepath)
        file_size = os.path.getsize(filepath)
        if "VERBOSE" in app.config and app.config["VERBOSE"]:
            print("Saved file {} [{} bytes]".format(filename, file_size))


class JobTagParser:
    def __init__(self, job_tag):
        self.tag = job_tag

        self.job = {}
        comment = job_tag.find_next(string=lambda text: isinstance(text, Comment))
        _last_update = comment.extract().split('"')[1]
        self.job["last_update"] = _last_update[:_last_update.rfind(" ")]
        self.job["title"] = job_tag.find_all("a")[1].text.strip()
        self.job["employer_code"] = job_tag.find("a", {"target": "_blank"})["href"].split("/")[-1]
        _url = job_tag.find("div", class_="details").a["href"]
        self.job["code"] = _url.split("/")[-1]
        self.job["salary"] = job_tag.find("span", class_="salary-text").text.strip()
        self.job["address"] = (
            job_tag.find("div", class_="address").text.strip().split("\n\n\n")
        )
        self.job["tags"] = (
            job_tag.find("div", class_="tag-list").text.strip().split("\n\n\n")
        )
        self.job["description"] = job_tag.find("div", class_="description").text.strip()
        _posted_tag = job_tag.find("span", class_="distance-time").text.strip()
        self.job["distance"] = _posted_tag
        self.job["last_post"] = get_post_date(self.job["last_update"], _posted_tag)

    def __repr__(self):
        return "<JobTagParser {}>".format(self.job["code"])

    def get_dict(self):
        return self.job

    def get_json(self):
        return json.dumps(self.job, sort_keys=True, indent=2, ensure_ascii=False)

    def save_json(self):
        filename = "{}/jobs/{}.json".format(app.instance_path, self.job["code"])
        to_json_file(self.job, filename)


def get_post_date(last_update, distance):
    last_dt = str_to_datetime(last_update)
    delta = get_time_distance_delta(distance)
    post_dt = last_dt - delta
    return post_dt.strftime(app.config["DATETIME_FORMAT"])


def get_time_distance_delta(time_distance):
    (count, unit, _) = time_distance.split(" ")
    if unit.startswith("minute"):
        return timedelta(minutes=int(count))
    elif unit.startswith("hour"):
        return timedelta(hours=int(count))
    elif unit.startswith("day"):
        return timedelta(days=int(count))
