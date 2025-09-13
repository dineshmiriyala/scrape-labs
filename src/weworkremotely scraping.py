from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib
import os
import re
import html
import json
import time
import random


# Helper functions

def rotate_header():
    USER_AGENTS = [
        # Chrome (Windows)
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",

        # Chrome (Mac)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.0 Chrome/125.0.6422.76 Safari/537.36",

        # Firefox
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:128.0) Gecko/20100101 Firefox/128.0",

        # Safari (Mac)
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_0) AppleWebKit/605.1.15 "
        "(KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]

    return {
        "User-Agent": random.choice(USER_AGENTS),
        "Accept-Language": "en-US,en;q=0.9",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Connection": "keep-alive",
    }


def robust_response(url, max_retries=3):
    """
    This function is to basically deal with number of
    requests sent for a particular url before moving
    to the next one
    :param url:
    :param max_retries:
    :return: gives the response from url after successful request
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(url, headers=rotate_header(), timeout=10)

            if response.status_code == 200:
                return response

            print(f"Attempt {attempt}: got status {response.status_code}")

        except Exception as e:
            print(f'got exception {e}')

        sleep_time = min(60, 2 ** attempt) + random.uniform(0, 1)
        print(f'Sleeping for {sleep_time} and retrying')
        time.sleep(sleep_time)
    print(f"Failed to get response from {url} after {max_retries} attempts")
    return None


def parse_relative_date(date_string):
    """
    In weworkremotely site the instead of date posted
    how many days ago the job posted was used, so
    this function is used to convert back to date
    :param date_string: how many days ago the job posted
    :return: date (%Y-%m-%d)
    """
    now = datetime.now()
    if "d" in date_string:
        days = int(date_string.replace("d", ""))
        return (now - timedelta(days=days)).strftime("%Y-%m-%d")
    else:
        return now.strftime("%Y-%m-%d")


def scraper_main_page(url):
    """
    This function will be used to scrape only the URL's of the jobs
    :param url: URL
    :return: csv with urls
    """

    response = robust_response(url)
    soup = BeautifulSoup(response.text, "html.parser")
    # only using the new-listing-container class
    jobs = soup.find_all("li",
                         class_="new-listing-container")

    jobs_links = []
    for job in jobs:
        links = job.find_all("a", href=True)

        if links[1] and links[1]["href"][:5] != "https":
            jobs_links.append("https://www.weworkremotely.com"
                              + links[1]["href"] if links[1] else None)

    print(f"Found {len(jobs_links)} links")
    return jobs_links


def description_parser(description):
    """
    This function will parse the description of the job
    :param description: Takes in html of description
    :return: Clean text
    """
    soup = BeautifulSoup(description, "html.parser")

    clean_text = soup.get_text(separator= " ", strip=True )

    clean_text = html.unescape(clean_text)

    return clean_text

def scrape_job_pages(url):
    response = robust_response(url)
    soup = BeautifulSoup(response.text, "html.parser")
    script = soup.find("script", type="application/ld+json")

    try:
        raw = html.unescape(script.string)

        """
        This was the bottleneck/problem I have solved
        inside the script there are some HTML tags so
        the ',' are causing to break the process, 
        so I used regex to remove all the ',' after
        description (it was only present there). 
        """
        raw = re.sub(
            r'("description"\s*:\s*")([\s\S]*?)(",$)',
            lambda m: m.group(1) + m.group(2).replace('"', '\\"').replace("\n", " ") + m.group(3),
            raw,
            flags=re.MULTILINE
        )

        # remove control characters
        raw = re.sub(r'[\x00-\x1f\x7f]', '', raw)

        try:
            job_data = json.loads(raw)
            return ({
                "title": job_data["title"],
                "description": description_parser(job_data["description"]),
                "job_url": url,
                "datePosted": job_data["datePosted"],
                "validThrough": job_data["validThrough"],
                "occupationalCategory": job_data["occupationalCategory"],
                "salary_min": job_data["baseSalary"]["value"]["minValue"],
                "salary_max": job_data["baseSalary"]["value"]["maxValue"],
                "salary_currency": job_data["baseSalary"]["currency"],
                "companyName": job_data["hiringOrganization"]["name"],
                "companyAddress": job_data["hiringOrganization"]["address"]
            })
        except Exception as error:
            print(f"Couldn't scrape jobs page {url}: {error}")
            return None

    except Exception as error:
        print(f"Couldn't scrape jobs page {url}: {error}")
        return None


def plot_date_wise_postings(df):
    """
    Plot posting dates
    :param df: Only the dataframe with date column should be passed
    :return: None
    """
    df = pd.to_datetime(df,
                        errors="coerce")
    df.dt.date.value_counts().sort_index().plot(kind="bar")


def scraped_data_parser(job_data):
    """
    This takes in the jsonloads data of urls we scraped from the weworkremotely site (using scraper_main_page)
    function
    :param url_list: df of urls to scrape
    :return: returns json containing job details like description, skills, salary
    """


def save_to_excel(df):
    today = datetime.now().strftime("%Y-%m-%d")
    # going to desired folder root/data/we_work
    base_path = os.path.join(os.path.dirname(__file__), "..", "data", "we_work", today)
    # create folder if it doesn't exist
    os.makedirs(base_path, exist_ok=True)

    # Full File path
    csv_path = os.path.join(base_path, f"we_work_{today}.csv")

    # save files
    df.to_csv(csv_path, index=True)
    print(f"Wrote CSV to {csv_path}")
    return None


if __name__ == "__main__":
    start_time = time.perf_counter()

    base_url = "https://www.weworkremotely.com/remote-jobs"

    try:
        scraped_data = []
        for link in scraper_main_page(base_url):
            scraped_data.append(scrape_job_pages(link))

        df = pd.DataFrame(scraped_data)
        print(f"Stats of scraped data: rows={len(df)}, cols={len(df.columns)}")
        save_to_excel(df)
    except Exception as error:
        print(f"{error}")

    elapsed_time = time.perf_counter() - start_time
    minutes, seconds = divmod(elapsed_time, 60)
    print(f"Scraped completed in {int(minutes)} minutes, {seconds:.2f} seconds")
