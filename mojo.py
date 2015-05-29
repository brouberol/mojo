# encoding: utf-8

"""
Script scraping the Mozilla careers webpage, storing interesting
job offfers in database, and sends daily email digest for new job
offers.

"""

import requests
import json
from urlparse import urljoin

from os.path import exists, join, abspath, dirname
from bs4 import BeautifulSoup


API_KEY = 'key-24ca5cd44ab8f098e2db81f44c486f1d'
MAILGUN_URL = 'https://api.mailgun.net/v3/mg.balthazar-rouberol.com/messages'
BASE_URL = 'http://careers.mozilla.org/en-US/listings'
JOB_OFFERS_FILEPATH = abspath(join(dirname(__file__), 'offers.json'))
SELECTORS = {
    'team': ['Engineering', 'IT'],
}


def include_job_offer(job_offer):
    """Return True if the job_offer is of interest, else False."""
    for k, v in job_offer.iteritems():
        if k in SELECTORS and v in SELECTORS[k]:
            return True
    return False


def extract_job_offers():
    """Scrape job offers and associated details from the Mozilla carrer
    page.

    Job offers are returned as a list of dict..

    """
    job_offers = []
    html = requests.get(BASE_URL, verify=False).text
    soup = BeautifulSoup(html)
    table = soup.find('table',   id='listings-positions')
    for tr in table('tr', class_='position')[2:-1]:  # lasr one is hidden ans displays an error message
        job_offer = {
            'title': tr.find('td', class_='title').text.strip(),
            'location': tr.find('td', class_='location').text.strip(),
            'position': tr.find('td', class_='type').text.strip(),
            'team': tr.find('td', class_='name').text.strip(),
            'link': tr.find('td', class_='title').find('a').attrs['href'],
        }
        if include_job_offer(job_offer):
            job_offer['link'] = urljoin(BASE_URL, job_offer['link'])
            job_html = requests.get(job_offer['link'], verify=False).text
            job_soup = BeautifulSoup(job_html)
            job_offer['description'] = job_soup.find('div', class_='job-post-description').text
            job_offers.append(job_offer)

    return job_offers


def format_job_offer(job_offer):
    return u"""
<hr/>
<p><a href="{link}">{title}</a></p>

<p>
    <ul>
        <li>TEAM: {team}</li>
        <li>LOCATIONS: {location}</li>
        <li>POSITION: {position}</li>
    </ul>
</p>
<p>
    DESCRIPTION: {description}
</p>
""".format(
        link=job_offer['link'],
        title=job_offer['title'],
        team=job_offer['team'],
        location=job_offer['location'],
        position=job_offer['position'],
        description=' '.join(job_offer['description'].split(' ')[:150]) + '...')


def send_mail(new_job_offers):
    """Send an HTML formatted email digest, listing current open job
    offers of interest.

    """
    if not new_job_offers:
        return

    formatted_offers = ''.join([format_job_offer(offer) for offer in new_job_offers])
    text = u"""
<p>Here are new job offers found on <a href="{base_url}">{base_url}</a>.</p>
{offers}""".format(base_url=BASE_URL, offers=formatted_offers)
    return requests.post(
        MAILGUN_URL,
        auth=("api", API_KEY),
        data = {
            "from": "mojo@imap.cc",
            "to": "br@imap.cc",
            "subject": "[Mojo] - %d new positon%s found" % (
                len(new_job_offers), 's' if len(new_job_offers) > 1 else ''),
            "html": text
        })


def store_offers(job_offers):
    """Add the argument job offers into the seen job offers database."""
    new_job_offers = []
    if not exists(JOB_OFFERS_FILEPATH):
        seen_offers = {}
    else:
        seen_offers = json.load(open(JOB_OFFERS_FILEPATH))

    for job_offer in job_offers:
        if job_offer['link'] not in seen_offers:
            new_job_offers.append(job_offer)
            seen_offers[job_offer['link']] = job_offer
    json.dump(seen_offers, open(JOB_OFFERS_FILEPATH, 'w'), indent=2)
    return new_job_offers


def main():
    """Do the magic. \o/"""
    job_offers = extract_job_offers()
    new_job_offers = store_offers(job_offers)
    send_mail(new_job_offers)


if __name__ == '__main__':
    main()

# TODO: get hired
