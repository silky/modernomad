from celery.task.schedules import crontab
from celery.task import periodic_task
from core.models import Location, Subscription, Use
from core.emails import guests_residents_daily_update, admin_daily_update, guest_welcome, goodbye_email
from modernomad.backup import BackupManager
from django.contrib.sites.models import Site
import datetime
from django.utils import timezone
import requests
import json
from django.core import urlresolvers

import logging
logger = logging.getLogger(__name__)

#@periodic_task(run_every=crontab(hour=22, minute=53, day_of_week="*"))  
#def test():      
#    print "HELLO WORLD"                    

@periodic_task(run_every=crontab(hour=5, minute=30))
def send_guests_residents_daily_update():
    locations = Location.objects.all()
    for location in locations:
        guests_residents_daily_update(location)

@periodic_task(run_every=crontab(hour=4, minute=30))
def send_admin_daily_update():
    locations = Location.objects.all()
    for location in locations:
        admin_daily_update(location)

#@periodic_task(run_every=crontab(minute="*")) # <-- for testing
@periodic_task(run_every=crontab(hour=5, minute=0))
def send_guest_welcome():
    # get all bookings WELCOME_EMAIL_DAYS_AHEAD from now. 
    locations = Location.objects.all()
    for location in locations:
        soon = datetime.datetime.today() + datetime.timedelta(days=location.welcome_email_days_ahead)
        upcoming = Use.objects.filter(location=location).filter(arrive=soon).filter(status='confirmed')
        for booking in upcoming:
            guest_welcome(booking)

@periodic_task(run_every=crontab(hour=4, minute=30))
def send_departure_email():
    # get all bookings departing today
    locations = Location.objects.all()
    for location in locations:
        today = timezone.localtime(timezone.now())
        departing = Use.objects.filter(location=location).filter(depart=today).filter(status='confirmed')
        for use in departing:
            goodbye_email(use)

@periodic_task(run_every=crontab(hour=2, minute=0))
def make_backup():
    manager = BackupManager()
    manager.make_backup()


@periodic_task(run_every=crontab(hour=1, minute=0))
def generate_subscription_bills():
    today = timezone.localtime(timezone.now()).date()
    # using the exclude is an easier way to filter for subscriptions with an
    # end date of None *or* in the future.
    locations = Location.objects.all()
    for l in locations:
        subscriptions_ready = Subscription.objects.ready_for_billing(location=l, target_date=today)
        if len(subscriptions_ready) == 0:
            logger.debug('no subscriptions are ready for billing at %s today.' % l.name)
        for s in subscriptions_ready:
            logger.debug('')
            logger.debug('automatically generating bill for subscription %d' % s.id)
            # JKS - we *could* double check to see whether there is already a
            # bill for this date. but, i'm worried about edge cases, and the
            # re-generation is non-destructive, so I just call generate_bill
            # regardless. if we end up with a lot of subscriptions we'll need
            # to revisit this)
            s.generate_bill(target_date=today)


def _format_attachment(use, color):
    domain = "https://" + Site.objects.get_current().domain
    if use.user.profile.image:
        profile_img_url = domain+use.user.profile.image.url
    else:
        profile_img_url = domain+"/static/img/default.jpg"
    booking_url = '<%s%s|%s - %s in %s>\n%s' % (domain, use.booking.get_absolute_url(), use.arrive.strftime("%B %d"), use.depart.strftime("%B %d"), use.resource.name, use.user.profile.bio)
    profile_url = domain + urlresolvers.reverse('user_detail', args=(use.user.username,)),
    item = {
            'color': color,
            'fallback' : use.user.get_full_name(),
            'title': use.user.get_full_name(),
            'title_link': profile_url[0], 
            'text': booking_url, 
            'thumb_url': profile_img_url,
    }
    return item

@periodic_task(run_every=crontab(hour=5, minute=10))
def slack_embassysf_daily():
    ''' post daily arrivals and departures to slack. to enable, add an incoming
    web hook to the specific channel you want this to post to. grab the webhook
    url and put it in the webhook variable below.'''
    webhook = "https://hooks.slack.com/services/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"
    today = timezone.localtime(timezone.now())
    location = Location.objects.get(slug="embassysf")
    arriving_today = Use.objects.filter(location=location).filter(arrive=today).filter(status='confirmed')
    departing_today = Use.objects.filter(location=location).filter(depart=today).filter(status='confirmed')

    payload = {
            'text': 'Arrivals and Departures for %s' % today.strftime("%B %d, %Y"),
            'attachments': []
    }
    for a in arriving_today:
        item = _format_attachment(a, "good")
        payload['attachments'].append(item)
    for d in departing_today:
        item = _format_attachment(d, "danger")
        payload['attachments'].append(item)
    if len(arriving_today) == 0 and len(departing_today) == 0:
        payload['attachments'].append({
            'fallback': 'No arrivals or departures today',
            'text': 'No arrivals or departures today'
            })

    js = json.dumps(payload)
    print js
    resp = requests.post(webhook, data=js)
    logger.debug("Slack response: %s" % resp.text)


@periodic_task(run_every=crontab(hour=0, minute=11))
def slack_ams_daily():
    ''' post daily arrivals and departures to slack. to enable, add an incoming
    web hook to the specific channel you want this to post to. grab the webhook
    url and put it in the webhook variable below.'''
    webhook = "https://hooks.slack.com/services/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"
    today = timezone.localtime(timezone.now())
    location = Location.objects.get(slug="amsterdam")
    arriving_today = Use.objects.filter(location=location).filter(arrive=today).filter(status='confirmed')
    departing_today = Use.objects.filter(location=location).filter(depart=today).filter(status='confirmed')

    payload = {
            'text': 'Arrivals and Departures for %s' % today.strftime("%B %d, %Y"),
            'attachments': []
    }
    for a in arriving_today:
        item = _format_attachment(a, "good")
        payload['attachments'].append(item)
    for d in departing_today:
        item = _format_attachment(d, "danger")
        payload['attachments'].append(item)
    if len(arriving_today) == 0 and len(departing_today) == 0:
        payload['attachments'].append({
            'fallback': 'No arrivals or departures today',
            'text': 'No arrivals or departures today'
            })

    js = json.dumps(payload)
    print js
    resp = requests.post(webhook, data=js)
    logger.debug("Slack response: %s" % resp.text)


@periodic_task(run_every=crontab(hour=5, minute=12))
def slack_redvic_daily():
    ''' post daily arrivals and departures to slack. to enable, add an incoming
    web hook to the specific channel you want this to post to. grab the webhook
    url and put it in the webhook variable below.'''
    webhook = "https://hooks.slack.com/services/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"
    today = timezone.localtime(timezone.now())
    location = Location.objects.get(slug="redvic")
    arriving_today = Use.objects.filter(location=location).filter(arrive=today).filter(status='confirmed')
    departing_today = Use.objects.filter(location=location).filter(depart=today).filter(status='confirmed')

    payload = {
            'text': 'Arrivals and Departures for %s' % today.strftime("%B %d, %Y"),
            'attachments': []
    }
    for a in arriving_today:
        item = _format_attachment(a, "good")
        payload['attachments'].append(item)
    for d in departing_today:
        item = _format_attachment(d, "danger")
        payload['attachments'].append(item)
    if len(arriving_today) == 0 and len(departing_today) == 0:
        payload['attachments'].append({
            'fallback': 'No arrivals or departures today',
            'text': 'No arrivals or departures today'
            })

    js = json.dumps(payload)
    print js
    resp = requests.post(webhook, data=js)
    logger.debug("Slack response: %s" % resp.text)




