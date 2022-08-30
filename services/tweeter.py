from dotenv import load_dotenv
import os
import tweepy


class Tweeter():

   def __init__(self) -> None:
      
      load_dotenv()
      self.access_token = os.environ["TWITTER_ACCESS_TOKEN"]
      self.access_token_secret = os.environ["TWITTER_ACCESS_TOKEN_SECRET"]
      self.consumer_key = os.environ["TWITTER_CONSUMER_KEY"]
      self.consumer_secret = os.environ["TWITTER_CONSUMER_SECRET"]

      self.auth = tweepy.OAuth1UserHandler(
         self.consumer_key, self.consumer_secret, self.access_token, self.access_token_secret
      )
      self.api = tweepy.API(self.auth, wait_on_rate_limit=True)

   def send_tweet(self, media_link, tweet_text = "hello loon"):
      media = self.api.media_upload(media_link)
      self.api.update_status(tweet_text, media_ids=[media.media_id_string])

      print("Sent tweet!")
