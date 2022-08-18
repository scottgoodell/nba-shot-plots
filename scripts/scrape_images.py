from bs4 import BeautifulSoup
import requests
import json
from os.path import exists


def get_player_images():
  url = "https://www.nba.com/players"

  r = requests.get(url)
  data = r.text
  players_string = data[data.index('"players":[')+10:data.index(',"region":"united-states"}')]
  players_list = json.loads(players_string)

  missing_players = []
  failed_players = []
  for player in players_list:
    player_slug = player['PLAYER_SLUG']
    print(player_slug)
    player_file_path = f"./player_images/{player_slug}.png"

    if not exists(player_file_path):
      player_url = f"https://www.nba.com/player/{player['PERSON_ID']}/{player_slug}"

      r = requests.get(player_url)
      data = r.text
      soup = BeautifulSoup(data,'html.parser')
      headshot_img = soup.find('img', {"alt": f"{player['PLAYER_FIRST_NAME']} {player['PLAYER_LAST_NAME']} Headshot"})
      if headshot_img:
        headshot_img_src = headshot_img.get("src")
      else:
        missing_players.append(player_slug)

      img_response = requests.get(headshot_img_src)
      if "<Code>AccessDenied</Code>" not in str(img_response.content):
        with open(f"./images/players/{player_slug}.png", "wb") as f:
          f.write(img_response.content)
      else:
        failed_players.append(player_slug)

  print("Finished!")

  if len(missing_players) > 0:
    print("\nMissing Headshots:")
    for p in missing_players:
      print(p)

  if len(failed_players) > 0:
    print("\nFailed Headshots:")
    for p in failed_players:
      print(p)
