import importlib
import nba_api.stats.static.players as players

from datetime import datetime
import os
import matplotlib as mpl
import matplotlib.pyplot as plt
import re

from helpers.data_pulls import get_game_boxscore, get_game_summary, player_game_shot_data
from services.google_storage_handler import GoogleStorageHandler
from static.colors import colors
from static.defaults import Defaults
from static.player_categories import player_categories
from static.teams import teams

class GameShotPlot:

  image_link = None
  tweet_text = None

  def __init__(self, game_id, player_id, team_id, category, shot_type = Defaults.SHOT_TYPE, season = Defaults.SEASON, season_part = Defaults.SEASON_PART) -> None:
    self.game_id            = game_id
    self.player_id          = player_id
    self.team_id            = team_id
    self.category           = category
    self.shot_type          = shot_type
    self.season             = season
    self.season_part        = season_part
    self.local_img_location = "/tmp"

  def build(self):
    court_color = colors["court_color"]
    background_color = colors["chart_background"]
    chart_text_color = colors["chart_text"]
    lines_width = 1.5 # const?
    lines_opacity = 0.85 # const?

    game_boxscore_data = get_game_boxscore(self.game_id)
    team_player_boxscore_data, team_team_boxscore_data = self._get_team_stats(game_boxscore_data)
    top_stats, bottom_stats = self._get_player_game_stats(team_player_boxscore_data, team_team_boxscore_data)

    if top_stats is None:
      return

    if "DNP" in top_stats["status"] or top_stats["minutes"] == 0:
      return

    font_dir = ["./static/fonts/Lato", "./static/fonts/McLaren"]
    for font in mpl.font_manager.findSystemFonts(font_dir):
      mpl.font_manager.fontManager.addfont(font)

    plt.switch_backend('Agg')

    storage_client = GoogleStorageHandler()

    team_context = [t for t in teams if t["id"] == self.team_id][0]
    court_color = court_color
    lines_color = team_context["lines_color"] if team_context.get("lines_color") else "black"

    mpl.rcParams['axes.linewidth'] = lines_width
    mpl.rcParams['figure.facecolor'] = background_color
    mpl.rcParams['font.weight'] = "bold"
    mpl.rcParams['font.family'] = "McLaren"

    shot_values = player_game_shot_data(
      team_id = self.team_id,
      player_id = self.player_id,
      game_id = self.game_id,
      shot_type = self.shot_type,
      season = self.season,
      season_part = self.season_part
    )
    game_shot_values = [[s[1], s[10], s[12], s[17], s[18]] for s in shot_values]

    player_context = players.find_player_by_id(self.player_id)
    player_full_name = player_context["full_name"]
    player_slug = self._player_slug(player_full_name)

    storage_client.download_object("nba-shot-plot-player-images", f"{player_slug}.png", self.local_img_location)
    storage_client.download_object("nba-shot-plot-team-images", f"{team_context['abbreviation']}.png", self.local_img_location)
    player_img = plt.imread(f"{self.local_img_location}/{player_slug}.png")
    team_img = plt.imread(f"{self.local_img_location}/{team_context['abbreviation']}.png")

    fig = plt.figure(num=1, clear=True)
    court_ax = fig.add_subplot()

    fig.set_figheight(9)
    fig.set_figwidth(5.5)
    court_ax.set_facecolor(court_color)

    SIDES = ["top", "bottom", "right", "left"]
    for side in SIDES:
      court_ax.spines[side].set_color(lines_color)

    # Team logo court
    team_logo_coords = team_context["coordinates"] if team_context.get("coordinates") else [-260, 260, -20, 480]
    team_logo_opacity = team_context["logo_opacity"] if team_context.get("logo_opacity") else 0.1
    court_ax.imshow(team_img, extent=team_logo_coords, alpha=team_logo_opacity)

    # Short corner 3PT lines
    court_ax.plot([-214, -214], [0, 140], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([214, 214], [0, 140], linewidth=lines_width, color=lines_color, alpha=lines_opacity)

    # 3PT Arc
    court_ax.add_artist(mpl.patches.Arc((0, 125), 430, 320, theta1=4, theta2=176, facecolor='none', edgecolor=lines_color, lw=lines_width, snap=True, alpha=lines_opacity))

    # Lane and Key
    court_ax.plot([-80, -80], [0, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([80, 80], [0, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([-60, -60], [0, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([60, 60], [0, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.plot([-80, 80], [190, 190], linewidth=lines_width, color=lines_color, alpha=lines_opacity)
    court_ax.add_artist(mpl.patches.Arc((0, 190), 120, 120, theta1=0, theta2=180, facecolor='none', edgecolor=lines_color, lw=lines_width, snap=True, alpha=lines_opacity))

    starting_angles = [-5, -35, -65, -95, -125, -155]
    for a in starting_angles:
      court_ax.add_artist(mpl.patches.Arc((0, 190), 120, 120, angle=a, theta1=-20, theta2=0, facecolor='none', edgecolor=lines_color, lw=lines_width, snap=True, alpha=lines_opacity))

    # Restricted Area
    court_ax.add_artist(mpl.patches.Arc((0, 40), 80, 80, theta1=0, theta2=180, facecolor='none', lw=lines_width, alpha=0.2))

    # Rim
    court_ax.add_artist(mpl.patches.Circle((0, 40), 10, facecolor='none', edgecolor=colors["rim"], lw=lines_width, alpha=0.6))

    # Backboard
    court_ax.plot([-25, 25], [29, 29], linewidth=lines_width, color=lines_color, alpha=0.2)

    # Halfcourt
    court_ax.add_artist(mpl.patches.Circle((0, 470), 60, facecolor='none', edgecolor=lines_color, lw=lines_width, alpha=lines_opacity))
    court_ax.add_artist(mpl.patches.Circle((0, 470), 20, facecolor='none', edgecolor=lines_color, lw=lines_width, alpha=lines_opacity))

    shot_marker_colors = {
      "3PT Field Goal": {
        "Made Shot": colors["made_shot"],
        "Missed Shot": colors["missed_shot"],
      },
      "2PT Field Goal": {
        "Made Shot": colors["made_shot"],
        "Missed Shot": colors["missed_shot"],
      }
    }

    for shot in game_shot_values:
      mark_color = shot_marker_colors[shot[2]][shot[1]]
      court_ax.plot(-shot[3], shot[4]+45, marker='o', color=mark_color, markersize=12, markeredgecolor=colors["marker_edge"])

    # Remove ticks
    court_ax.set_xticks([])
    court_ax.set_yticks([])

    # Set axis limits
    court_ax.set_xlim(-250, 250)
    court_ax.set_ylim(0, 470)

    stat_count = 0
    for c in [0.34, 0.58, 0.79]:
      for r in [0.106, 0.072, 0.038, 0.004]:
        a = fig.add_axes([c, r, 0.16, 0.05], anchor='SW', zorder=-1)
        a.set_xticks([])
        a.set_yticks([])
        stat_box_props = dict(facecolor=background_color, edgecolor="none")
        a.text(
          0.0, 0.5,
          bottom_stats[stat_count],
          fontsize=15,
          color=chart_text_color,
          ha="left",
          va="center",
          bbox=stat_box_props
        )
        a.axis('off')
        stat_count += 1

    name_title_txt_ax = fig.add_axes([0.30, 0.87, 0.4, 0.1], anchor='SW', zorder=-1)
    name_title_txt_ax.set_xticks([])
    name_title_txt_ax.set_yticks([])

    name_title_txt_box_props = dict(facecolor=background_color, edgecolor="none")
    name_title_team_txt = self._name_title_txt_by_category(team_context)

    name_title_txt_box_text = \
      f"{player_full_name}\n" + name_title_team_txt

    name_title_txt_ax.text(
      0.5, 0.5,
      name_title_txt_box_text,
      fontsize=24,
      color=chart_text_color,
      ha="center",
      va="center",
      bbox=name_title_txt_box_props,
      linespacing=1.2,
    )
    name_title_txt_ax.set_facecolor(background_color)
    name_title_txt_ax.axis('off')

    game_title_txt_ax = fig.add_axes([0.30, 0.74, 0.4, 0.1], anchor='SW', zorder=-1)
    game_title_txt_ax.set_xticks([])
    game_title_txt_ax.set_yticks([])

    game_info = self._get_game_info()

    game_title_txt_box_props = dict(facecolor=background_color, edgecolor="none")
    game_title_txt_box_text = \
      f"{game_info['game_date']}\n" + \
      f"{game_info['away_team_abbr']}  ({game_info['away_score']})  vs.  {game_info['home_team_abbr']}  ({game_info['home_score']})\n" + \
      f"Mins: {top_stats['minutes']},  Pts: {top_stats['points']},  +/-: {top_stats['plus_minus']},  Starting: {top_stats['starting']}\n" + \
      f"{player_categories[self.category]['twitter_handle']}"

    game_title_txt_ax.text(
      0.5, 0.5,
      game_title_txt_box_text,
      fontsize=14,
      color=chart_text_color,
      ha="center",
      va="center",
      bbox=game_title_txt_box_props,
      linespacing=1.5,
    )
    game_title_txt_ax.set_facecolor(background_color)
    game_title_txt_ax.axis('off')

    player_img_ax = fig.add_axes([0.0, 0.0, 0.34, 0.18], anchor='SW', zorder=-1)
    player_img_ax.imshow(player_img)
    player_img_ax.axis('off')

    export_filename = f"{player_slug}-{team_context['abbreviation']}-{self.game_id}.png"

    plt.subplots_adjust(left=0.02, right=0.98, top=0.72, bottom=0.16)
    plt.savefig(f"{self.local_img_location}/{export_filename}")
    storage_client.upload_object("nba-shot-plot-shot-plots", export_filename, self.local_img_location)

    for file in [f"{self.local_img_location}/{player_slug}.png", f"{self.local_img_location}/{team_context['abbreviation']}.png"]:
      try:
        os.remove(file)
      except:
        pass

    self.image_link = f"{self.local_img_location}/{export_filename}"
    self.tweet_text = self._build_tweet_text(
      player_game_stats = {
        "top_stats": top_stats,
        "bottom_stats": bottom_stats
      },
      player_context = player_context,
      team_context = team_context,
      game_info = game_info
    )

  def _build_court(self):
    # i feel like i should be able to pass around the figure somehow and the plt
    pass

  def _build_tweet_text(self, player_game_stats: dict, player_context, team_context, game_info):

    return f"{player_context['full_name']} #{player_context['full_name'].replace(' ', '')}\n" \
      f"{team_context['name']} #{team_context['mascot']} {team_context['social_hashtag']}\n\n" \
      f"Final: {game_info['away_team_name']} {game_info['away_score']} // {game_info['home_team_name']} {game_info['home_score']}\n" \
      f"#{game_info['away_team_abbr']}vs{game_info['home_team_abbr']} // #{game_info['home_team_abbr']}vs{game_info['away_team_abbr']}\n\n" \
      f"Minutes: {player_game_stats['top_stats']['minutes']}\n" \
      f"Points: {player_game_stats['top_stats']['points']}\n" \
      f"Shots: {player_game_stats['bottom_stats'][0].split(':')[-1].strip()}\n" \
      f"Threes: {player_game_stats['bottom_stats'][1].split(':')[-1].strip()}\n" \
      f"Frees: {player_game_stats['bottom_stats'][2].split(':')[-1].strip()}\n"

  def _player_slug(self, full_name):
    return re.sub(r'[^a-z-]', '', full_name.lower().replace(" ", "-"))

  def _get_game_info(self):
    game_summary = get_game_summary(self.game_id)
    game_info = [game_info for game_info in game_summary if game_info["name"] == "LineScore"][0]
    away_game_info = dict(zip(game_info["headers"], game_info["rowSet"][0]))
    home_game_info = dict(zip(game_info["headers"], game_info["rowSet"][1]))

    return {
      "game_date": datetime.strptime(home_game_info["GAME_DATE_EST"], '%Y-%m-%dT%H:%M:%S').strftime("%A, %m/%d/%Y"),
      "away_team_abbr": away_game_info["TEAM_ABBREVIATION"],
      "away_team_name": away_game_info["TEAM_NICKNAME"],
      "away_score": away_game_info["PTS"],
      "home_team_abbr": home_game_info["TEAM_ABBREVIATION"],
      "home_team_name": home_game_info["TEAM_NICKNAME"],
      "home_score": home_game_info["PTS"],
    }

  def _get_team_stats(self, boxscore_data):
    player_data = [stat_set for stat_set in boxscore_data if stat_set["name"] == "PlayerStats"][0]
    player_headers = player_data["headers"]
    team_data = [stat_set for stat_set in boxscore_data if stat_set["name"] == "TeamStats"][0]
    team_headers = team_data["headers"]

    player_records = [dict(zip(player_headers, player)) for player in player_data["rowSet"]]
    team_records = [dict(zip(team_headers, team)) for team in team_data["rowSet"]]

    player_return_records = [records for records in player_records if records["TEAM_ID"] == self.team_id]
    team_return_records = [records for records in team_records if records["TEAM_ID"] == self.team_id][0]

    return [player_return_records, team_return_records]

  def _get_player_game_stats(self, team_player_stats, team_team_stats):
    player_stats = [player for player in team_player_stats if player['PLAYER_ID'] == self.player_id]
    if len(player_stats) == 0:
      return [None, None]
    else:
      player_stats = player_stats[0]

    plus_minus = int(player_stats["PLUS_MINUS"]) if player_stats["PLUS_MINUS"] else 0
    if plus_minus > 0:
      str_plus_minus = f"+{str(plus_minus)}"
    else:
      str_plus_minus = str(plus_minus)

    top_stats = {
      "minutes": int(player_stats["MIN"][0:player_stats["MIN"].index(":")]) if player_stats["MIN"] else 0,
      "starting": 'Yes' if player_stats["START_POSITION"] != "" else "No",
      "plus_minus": str_plus_minus,
      "points": player_stats["PTS"],
      "status": player_stats["COMMENT"]
    }

    bottom_stats = [
      f"FGs: {player_stats['FGM']}/{player_stats['FGA']}",
      f"3FGs: {player_stats['FG3M']}/{player_stats['FG3A']}",
      f"FTs: {player_stats['FTM']}/{player_stats['FTA']}",
      f"EFG%: {self._calc_efg(player_stats)}",
      f"ASTs: {player_stats['AST']}",
      f"TOs: {player_stats['TO']}",
      f"REBs: {player_stats['REB']}",
      f"OREBs: {player_stats['OREB']}",
      f"STLs: {player_stats['STL']}",
      f"BLKs: {player_stats['BLK']}",
      f"PFs: {player_stats['PF']}",
      f"USG%: {self._calc_usage_rate(team_team_stats, player_stats)}",
    ]

    return [top_stats, bottom_stats]

  def _calc_efg(self, player_data):
    if player_data["MIN"] is None:
      return "0"

    player_fgs_made     = player_data["FGM"]
    player_fgs_attempts = player_data["FGA"]
    player_3fgs_made    = player_data["FG3M"]

    effective_field_goal_perc = (player_fgs_made + 0.5 * player_3fgs_made) / player_fgs_attempts if player_fgs_attempts > 0 else 0.0

    return str(int(round(effective_field_goal_perc * 100, 0)))

  def _calc_usage_rate(self, team_data, player_data):
    if player_data["MIN"] is None:
      return "0"

    player_fgs  = int(player_data["FGA"])
    player_fts  = int(player_data["FTA"])
    player_tos  = int(player_data["TO"])
    player_mins = int(player_data["MIN"][0:player_data["MIN"].index(":")]) if player_data["MIN"] else 0

    team_fgs  = int(team_data["FGA"])
    team_fts  = int(team_data["FTA"])
    team_tos  = int(team_data["TO"])
    team_mins = int(team_data["MIN"][0:team_data["MIN"].index(":")]) if team_data["MIN"] else 0

    usage_percentage = ((player_fgs + (0.44 * player_fts) + player_tos) * (team_mins / 5)) \
    / (player_mins * (team_fgs + (.44 * team_fts) + team_tos))

    return str(int(round(usage_percentage * 100, 0)))

  def _name_title_txt_by_category(self, team_context):
    if self.category in ["rookies", "sophomores"]:
      category_context_module = getattr(importlib.import_module(f"static.{self.category}"), self.category)
      category_context = [p for p in category_context_module if p["id"] == self.player_id][0]

      return f"Drafted: {category_context['draft_year']} #{category_context['draft_pick']} ({team_context['abbreviation'].upper()})"
    else:
      return f"{team_context['name']}"


# should i have a helper class to isolate player's stats for a specific game? GameStats (player_id, game_id)
# maybe? if i feel like it's going to be reused; but right now it's not

# class for font handling.. again if you are going to repeat it then separate it FontHandler

# make player.json so you don't have to make a request

# GameShotPlot < ShotPlot
# build shouldn't know about the shot_values - this should be a separate method?
