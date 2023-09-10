"""
This module is used for scaping https://www.pro-football-reference.com/
and get upcoming game data.
"""

import requests
from bs4 import BeautifulSoup

URL = "https://www.pro-football-reference.com/"

def get_upcoming_games_page(year):
    """
    year -> year that data is to be scraped from (e.g. 2023)
    """
    return requests.get(URL + f"years/{year}/games.htm")

def get_local_soup(filepath):
    with open(filepath, 'rb') as f:
        page = f.read()
    return BeautifulSoup(page, "html.parser")

def get_table_body(soup):
    return soup.find("table", id="games").find("tbody")

def get_table_rows(table):
    return table.find_all("tr")

def get_week(rows, week_num):
    weeks = []
    for row in rows:
        try:
            if row.th["csk"] == str(week_num):
                weeks.append(row)
        except KeyError:
            pass
    return weeks

def get_games(week):
    games = []
    for game in week:
        game_data = {}
        for data in game.find_all("td"):
            game_data[data["data-stat"]] = data.text
        games.append(game_data)
    return games

def get_week_games(week_num, year=2023, local_path=None):
    if local_path:
        soup = get_local_soup(local_path)
    else:
        page = get_upcoming_games_page(year)
        soup = BeautifulSoup(page.content, "html.parser")

    table = get_table_body(soup)
    rows = get_table_rows(table)
    week = get_week(rows, week_num)
    return get_games(week)


if __name__ == '__main__':
    # page = get_upcoming_games_page(2023)
    # with open('test_page.html', 'wb') as f:
    #     f.write(page.content)
    # soup = BeautifulSoup(page.content, "html.parser")
    games = get_week_games(1, 2023, 'test_page.html')
    print(games)