# NFL Prediction Model

This repository contains the source code for a website that predicts NFL game spreads. The model uses 
an Elo model and a neural network to perform it's predictions. All data is scraped from https://www.pro-football-reference.com/,
processed, and then stored in an sqlite database. The website uses the Flask, Pytorch, and BeautifulSoup frameworks
and vanilla Javascript, HTML, and CSS on the frontend.

The website is currently up and hosted at: https://nfl-prediction.azurewebsites.net/home.html

## Installation

**Step 1:** Clone this repository.

**Step 2:** Create a virtual environment running Python 3.10 or greater.

**Step 3:** Run ``pip install -r requirements.txt``.

You should now be up and running.
