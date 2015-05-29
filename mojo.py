# encoding: utf-8

"""
Script scraping the Mozilla careers webpage, storing interesting
job offfers in database, and sends daily email digest for new job
offers.

"""

import requests
import json
import os
from urlparse import urljoin

from os.path import exists, join, abspath, dirname
from bs4 import BeautifulSoup


API_KEY = os.environ['MAILGUN_API_KEY']
MAILGUN_DOMAIN = os.environ['MAILGUN_DOMAIN']
MAILGUN_URL = "https://api.mailgun.net/v2/%s/messages" % (MAILGUN_DOMAIN)
BASE_URL = 'https://careers.mozilla.org/en-US/listings/'
JOB_OFFERS_FILEPATH = abspath(join(dirname(__file__), 'offers.json'))
SELECTORS = ['Engineering', 'IT']


def extract_job_offers():
    """Scrape job offers and associated details from the Mozilla carrer
    page.

    Job offers are returned as a list of dict..

    """
    job_offers = []
    html = requests.get(BASE_URL).text
    soup = BeautifulSoup(html)
    table = soup.find('table', id='listings-positions')
    for tr in table('tr', class_='position')[2:-1]:  # lasr one is hidden ans displays an error message
        job_offer = {
            'title': tr.find('td', class_='title').text,
            'location': tr.find('td', class_='location').text,
            'position': tr.find('td', class_='type').text,
            'team': tr.find('td', class_='name').text,
            'link': tr.find('td', class_='title').find('a').attrs['href'],
        }
        if job_offer['team'] in SELECTORS:
            job_offer['link'] = urljoin(BASE_URL, job_offer['link'])
            job_html = requests.get(job_offer['link']).text
            job_soup = BeautifulSoup(job_html)
            job_offer['description'] = job_soup.find('div', class_='job-post-description').text
            job_offers.append(job_offer)

    return job_offers


def format_job_offer(job_offer):
    return u"""
<p><a href="{link}>{title}</a></p>

 <p>
    TEAM: {team}
    LOCATIONS: {location}
    POSITION: {position}
</p>
<p>
    DESCRIPTION: {description}
</p>
""".format(
        link=job_offer['link'],
        title=job_offer['title'],
        team=job_offer['team'],
        location=job_offer['locatione'],
        position=job_offer['position'],
        description=' '.join(job_offer['description'].split(' ')[:150]))


def send_mail(job_offers):
    """Send an HTML formatted email digest, listing current open job
    offers of interest.

    """
    formatted_offers = ''.join([format_job_offer(offer) for offer in job_offers])
    text = u"""
Here are new job offers found on {base_url}:
{offers}""".format(base_url=BASE_URL, offers=formatted_offers)
    return requests.post(
        MAILGUN_URL,
        auth=("api", API_KEY),
        data = {
            "from": "mojo@imap.cc",
            "to": "br@imap.cc",
            "subject": "[Mojo] - %d new positon%s found" % (len(job_offers), 's' if len(job_offers) > 1 else ''),
            "text": text
        })


def store_offers(job_offers):
    """Add the argument job offers into the seen job offers database."""
    if not exists(JOB_OFFERS_FILEPATH):
        seen_offers = {}
    else:
        seen_offers = json.load(open(JOB_OFFERS_FILEPATH))

    for job_offer in job_offers:
        if job_offer['link'] not in seen_offers:
            seen_offers[job_offer['link']] = job_offer
    json.dump(seen_offers, open(JOB_OFFERS_FILEPATH, 'w'))


def main():
    job_offers = extract_job_offers()
    store_offers(job_offers)
    send_mail(job_offers)


if __name__ == '__main__':
    main()


# TODO: fix mailgun DNS and MX records
# TODO: let it propagate
# TODO: add this in a crontab on pi
# TODO: get hired
