"""
This module is used for scaping https://www.pro-football-reference.com/
and getting upcoming game data.
"""

import requests
from bs4 import BeautifulSoup

URL = "https://www.pro-football-reference.com/"

def get_upcoming_games_page(year):
    """
    Get HTML from the football reference schedule page.

    Parameters
    ----------
    year : int
        Year that data is to be scraped from (e.g. 2023)
    
    Returns
    -------
    str
        HTML of the page at https://www.pro-football-reference.com/years/'year'/games.htm
    """
    return requests.get(URL + f"years/{year}/games.htm")

def get_local_soup(filepath):
    """
    Get BeautifulSoup object from locally saved HMTL page.

    Parameters
    ----------
    filepath : str
        Path to local HMTL page.
    
    Returns
    -------
    BeautifulSoup object
        Object from reading the stored page.
    """
    with open(filepath, 'rb') as f:
        page = f.read()
    return BeautifulSoup(page, "html.parser")

def get_table_body(soup):
    """
    Returns
    -------
        HTML within the season schedule table.
    """
    return soup.find("table", id="games").find("tbody")

def get_table_rows(table):
    """
    Returns
    -------
        All of the elements with the tr tag.
    """
    return table.find_all("tr")

def get_week(rows, week_num):
    """
    Get all of the rows in the week week_num

    Parameters
    ----------
    rows : iter
        Iterable of HTML table row data
    week_num : int
        Week number chosen to be returned

    Returns
    -------
    list
        All table rows for week_num
    """
    week = []
    for row in rows:
        try:
            if row.th["csk"] == str(week_num):
                week.append(row)
        except KeyError:
            pass
    return week

def get_games(week):
    """
    Get the data for each game in a week.

    Parameters
    ----------
    week : iter
        Iterable of rows in a HTML table.

    Returns
    -------
    dict
        Dictionary of game data for each game in week.
    """
    games = []
    for game in week:
        game_data = {}
        for data in game.find_all("td"):
            game_data[data["data-stat"]] = data.text
        games.append(game_data)
    return games

def get_week_games(week_num, year=2023, local_path=None):
    """
    Get data for all of the games within a certian week of a year.

    Parameters
    ----------
    week_num : str
        Week to scrape (e.g. "1" or "SuperBowl")
    year : int
        First year in the season (e.g. 2023 for the 2023-2024 season)
    local_path : str
        Path to a locally stored HTML file to be used when developing/debugging. 
        Default is None.

    Returns
    -------
    list
        List of dictionaries where the dictionary contains the game data
        of each game in the week from 
        https://www.pro-football-reference.com/years/'year'/games.htm. 
    """
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
    pass
    # page = get_upcoming_games_page(2023)
    # with open('test_page.html', 'wb') as f:
    #     f.write(page.content)
    # soup = BeautifulSoup(page.content, "html.parser")
    soup = get_local_soup("test_page.html")
    games = get_week_games(6, 2023, 'test_page.html')
    print(games)