import fire

from services.tweeter import Tweeter
from src.game_shot_plot import GameShotPlot


class ShotPlotCli:

  def __init__(self, game_id, player_id, team_id, category, tweet_context = None) -> None:
    self.game_id = game_id
    self.player_id = player_id
    self.team_id = team_id
    self.category = category
    self.tweet_context = tweet_context

    self.shot_plot = GameShotPlot(
      game_id = self.game_id,
      player_id = self.player_id,
      team_id = self.team_id,
      category = self.category
    )

  def execute(self):
    self.shot_plot.build()
    image_link = self.shot_plot.image_link
    if self.tweet_context:
      tweet_text = tweet_text = self.shot_plot.tweet_text + f"\n\n{self.tweet_context}"
    else:
      tweet_text = tweet_text = self.shot_plot.tweet_text

    tweeter = Tweeter()
    tweeter.send_tweet(media_link = image_link, tweet_text = tweet_text)


if __name__ == "__main__":
  # game_id = "0022101154"
  # player_id = 1630224 # jalen green
  # team_id = 1610612745
  # category = "sophomores"

  # game_id = "0022100584"
  # player_id = 1627832 # fred vanvleet
  # team_id = 1610612761
  # category = "veterans"

  fire.Fire(ShotPlotCli)