from dotenv import load_dotenv
import os

load_dotenv()

twitter_accounts = {
  "league": {
    "ACCESS_TOKEN": os.environ["LEAGUE_TWITTER_ACCESS_TOKEN"],
    "ACCESS_TOKEN_SECRET": os.environ["LEAGUE_TWITTER_ACCESS_TOKEN_SECRET"],
    "CONSUMER_KEY": os.environ["LEAGUE_TWITTER_CONSUMER_KEY"],
    "CONSUMER_SECRET": os.environ["LEAGUE_TWITTER_CONSUMER_SECRET"],
  },
  "rookies": {
    "ACCESS_TOKEN": os.environ["ROOKIE_TWITTER_ACCESS_TOKEN"],
    "ACCESS_TOKEN_SECRET": os.environ["ROOKIE_TWITTER_ACCESS_TOKEN_SECRET"],
    "CONSUMER_KEY": os.environ["ROOKIE_TWITTER_CONSUMER_KEY"],
    "CONSUMER_SECRET": os.environ["ROOKIE_TWITTER_CONSUMER_SECRET"],
  },
  "sophomores": {
    "ACCESS_TOKEN": os.environ["SOPHOMORE_TWITTER_ACCESS_TOKEN"],
    "ACCESS_TOKEN_SECRET": os.environ["SOPHOMORE_TWITTER_ACCESS_TOKEN_SECRET"],
    "CONSUMER_KEY": os.environ["SOPHOMORE_TWITTER_CONSUMER_KEY"],
    "CONSUMER_SECRET": os.environ["SOPHOMORE_TWITTER_CONSUMER_SECRET"],
  },
  "westbrook": {
    "ACCESS_TOKEN": os.environ["RUSS_TWITTER_ACCESS_TOKEN"],
    "ACCESS_TOKEN_SECRET": os.environ["RUSS_TWITTER_ACCESS_TOKEN_SECRET"],
    "CONSUMER_KEY": os.environ["RUSS_TWITTER_CONSUMER_KEY"],
    "CONSUMER_SECRET": os.environ["RUSS_TWITTER_CONSUMER_SECRET"],
  },
}