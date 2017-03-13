# encoding: utf-8

"""
Script scraping the Mozilla careers webpage, storing interesting
job offfers in "database" (a JSON file), and sends daily email digest
containing the new job offers, if any.

"""
import sys
py_version = sys.version_info

import logging
import argparse
import requests
import json

if py_version.major == 3:
    from urllib.parse import urljoin
else:
    from urlparse import urljoin
from os.path import exists, join, abspath, dirname
from bs4 import BeautifulSoup


# http://careers.mozilla.org/en-US/listings redirects to https://careers.mozilla.org/en-US/listings
# and a requests.get on https://careers.mozilla.org/en-US/listings when verigying the certificate
# will raise a requests.exceptions.SSLError exception, but only when using Python2
SSL_VERIFY = py_version.major == 3

BASE_URL = 'http://careers.mozilla.org/en-US/listings'
JOB_OFFERS_FILEPATH = abspath(join(dirname(__file__), 'offers.json'))
SELECTORS = {
    'team': ['Engineering', 'IT'],
}
LOG = logging.getLogger(__name__)
LOG.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
ch = logging.StreamHandler(stream=sys.stdout)
ch.setLevel(logging.INFO)
ch.setFormatter(formatter)
LOG.addHandler(ch)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--api-key', '-k', help='The mailgun API_KEY', required=True)
    parser.add_argument('--api-url', '-u', help='The mailgun API URL', required=True)
    parser.add_argument('--send-to', '-t', help='The email address new positions will be sent to', required=True)
    parser.add_argument('--send-from', '-f', help='The email address new positions will be sent from', required=True)
    return parser.parse_args()


def include_job_offer(job_offer):
    """Return True if the job_offer is of interest, else False."""
    for k, v in job_offer.items():
        if k in SELECTORS and v in SELECTORS[k]:
            return True
    return False


def extract_job_offers():
    """Scrape job offers and associated details from the Mozilla carrer
    page.

    Job offers are returned as a list of dict..

    """
    job_offers = []
    html = requests.get(BASE_URL, verify=SSL_VERIFY).text
    soup = BeautifulSoup(html)
    table = soup.find('table', id='listings-positions')
    for tr in table('tr', class_='position')[2:-1]:  # last one is hidden ans displays an error message
        job_offer = {
            'title': tr.find('td', class_='title').text.strip(),
            'location': tr.find('td', class_='location').text.strip(),
            'position': tr.find('td', class_='type').text.strip(),
            'team': tr.find('td', class_='name').text.strip(),
            'link': tr.find('td', class_='title').find('a').attrs['href'],
        }
        if include_job_offer(job_offer):
            job_offer['link'] = urljoin(BASE_URL, job_offer['link'])
            job_html = requests.get(job_offer['link'], verify=SSL_VERIFY).text
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


def send_mail(new_job_offers, api_key, api_url, send_to, send_from):
    """Send an HTML formatted email digest, listing current open job
    offers of interest.

    """
    if not new_job_offers:
        return

    formatted_offers = ''.join([format_job_offer(offer) for offer in new_job_offers])
    text = u"""
<p>Here are new job offers found on <a href="{base_url}">{base_url}</a>.</p>
{offers}""".format(base_url=BASE_URL, offers=formatted_offers)
    r = requests.post(
        api_url,
        auth=("api", api_key),
        data = {
            "from": send_from,
            "to": send_to,
            "subject": "[Mojo] - %d new position%s found" % (
                len(new_job_offers), 's' if len(new_job_offers) > 1 else ''),
            "html": text
        })
    r.raise_for_status()
    return r


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
    """Where all the magic happens"""
    args = parse_args()
    LOG.info('Scraping for new job offers...')
    job_offers = extract_job_offers()
    new_job_offers = store_offers(job_offers)
    LOG.info('%d new job offers found', len(new_job_offers))
    try:
        send_mail(
            new_job_offers,
            api_key=args.api_key,
            api_url=args.api_url,
            send_to=args.send_to,
            send_from=args.send_from)
    except Exception as exc:
        LOG.exception(exc)


if __name__ == '__main__':
    main()
