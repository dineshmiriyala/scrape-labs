from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta
import pandas as pd
import matplotlib

# Helper functions

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


def scraper(url):
    """
    Scrape wework site and return a pandas dataframe
    :param url: url to scrape
    :return: dataframe
    """
    response = requests.get(url)
    if response.status_code == 200:
        print("Successfully retrieved page")
        soup = BeautifulSoup(response.text, "html.parser")

        # new jobs are wrapped inside the new-listing-container
        jobs = soup.find_all("li",
                             class_ = "new-listing-container")

    else:
        print("Failed to scrape")
        print("status code: " + str(response.status_code))
        return None

    job_data = []

    for job in jobs:
        title = job.find("h3", class_ = "new-listing__header__title")
        company = job.find("p", class_ = "new-listing__company-name")
        location = job.find("p", class_ =
                            "new-listing__company-headquarters")
        links = job.find_all("a", href = True)
        date = (job.find("p",
                        class_ = "new-listing__header__icons__date")
                .text.strip())
        date_new = parse_relative_date(date)

        if title or company or links:
            job_data.append({
                "title": title.text.strip(),
                "company": company.text.strip(),
                "location": location.text.strip() if location else None,
                "date": date_new,
                "url": "https://www.weworkremotely.com"
                       + links[1]["href"] if links[1] else None,
                "date_posted": date_new
            })
    print("Successfully scraped, Number of jobs: " +
          str(len(job_data)))
    return pd.DataFrame(job_data)

def plot_date_wise_postings(df):
    """
    Plot posting dates
    :param df:
    :return: None
    """
    df["date_posted"] = pd.to_datetime(df["date_posted"],
                                       errors="coerce")
    df["date_posted"].dt.date.value_counts().sort_index().plot(kind = "bar")


if __name__ == "__main__":
    url = "https://weworkremotely.com/remote-jobs"
    try:
        df = scraper(url)
        print("preview data: ")
        print(df.head())
        # call this for plot, plot_date_wise_postings(df)
    except Exception as error:
        None


