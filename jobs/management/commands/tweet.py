import tweepy 

from django.conf import settings
from django.core.management.base import BaseCommand

class Command(BaseCommand):

    def handle(self, msg, **kwargs):
        """tweet something as the jobs site
        """
        auth = tweepy.OAuthHandler(settings.CODE4LIB_TWITTER_OAUTH_CONSUMER_KEY, settings.CODE4LIB_TWITTER_OAUTH_CONSUMER_SECRET)
        auth.set_access_token(settings.CODE4LIB_TWITTER_OAUTH_ACCESS_TOKEN_KEY, settings.CODE4LIB_TWITTER_OAUTH_ACCESS_TOKEN_SECRET)
        twitter = tweepy.API(auth)
        twitter.update_status(msg)
