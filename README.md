## Mojo: Mozilla Jobs

Get notified by email when new positions of interest open up at Mozilla.

This script scrapes job offers details from the [Mozilla career page](http://careers.mozilla.org/en-US/listings), and alerts by email you when a new position opens.

## How do I use it?

This is very alpha, so you need to manually edit the ``SELECTORS`` global variable in ``mojo.py``, and add the required selection rules. To be selectable, a job offer needs to have at least one target value for a specific field.

Example: ``SELECTORS = {'team': ['Engineering', 'IT']}`` will only select positions which team field is either "Engineering" or "IT". The available fields are:

- title
- location
- position
- team
- link
- description

```
usage: mojo.py [-h] --api-key API_KEY --api-url API_URL --send-to SEND_TO

optional arguments:
  -h, --help            show this help message and exit
  --api-key API_KEY, -k API_KEY
                        The mailgun API_KEY
  --api-url API_URL, -u API_URL
                        The mailgun API URL
  --send-to SEND_TO, -t SEND_TO
                        The email address new positions will be sent to
```

I run this script daily using a cron job, but you're free to do it however you fancy.

## Email sending

This script relies on Mailgun to actually send the email, because I'm lazy and I initially hacked this in a train.

## License

THE BEER-WARE LICENSE" (Revision 42):
Balthazar Rouberol wrote this file.  As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return.

## TODO

Get hired.
