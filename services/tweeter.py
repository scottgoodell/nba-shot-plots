import tweepy

from static.twitter_accounts import twitter_accounts

class Tweeter:

   def __init__(self, account_type) -> None:
      self.access_token = twitter_accounts[account_type]["ACCESS_TOKEN"]
      self.access_token_secret = twitter_accounts[account_type]["ACCESS_TOKEN_SECRET"]
      self.consumer_key = twitter_accounts[account_type]["CONSUMER_KEY"]
      self.consumer_secret = twitter_accounts[account_type]["CONSUMER_SECRET"]

      self.auth = tweepy.OAuth1UserHandler(
         self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret
      )
      self.api = tweepy.API(self.auth, wait_on_rate_limit=True)

   def send_tweet(self, media_link, tweet_text):
      media = self.api.media_upload(media_link)
      self.api.update_status(tweet_text, media_ids=[media.media_id_string])

      print("Sent tweet!")
