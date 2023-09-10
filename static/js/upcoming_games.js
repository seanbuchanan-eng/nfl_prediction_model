const weeksHeader = document.getElementById("week_header");
const gameCards = document.getElementById("game_cards");


async function updateGames() {
    const gamesPromise = await fetch("http://127.0.0.1:5000/get-upcoming-games")
    const gamesData = await gamesPromise.json();
    
    let cardHTML = ``;
    for (let game of gamesData.values()) {
        if (game["home"] == "winner") {
            homeTeam = game["winner"]
            awayTeam = game["loser"]
            homePoints = game["pts_win"]
            awayPoints = game["pts_lose"]
        } else {
            homeTeam = game["loser"]
            awayTeam = game["winner"]
            homePoints = game["pts_lose"]
            awayPoints = game["pts_win"]
        }
        if (game["home_spread"] <= 0) {
            homeSpread = "- " + Math.abs(game["home_spread"]).toFixed(1)
            awaySpread = "+" + Math.abs(game["away_spread"]).toFixed(1)
        } else {
            homeSpread = "+" + Math.abs(game["home_spread"]).toFixed(1)
            awaySpread = "- " + Math.abs(game["away_spread"]).toFixed(1)
        }
        cardHTML += `<div class="game_card">
                        <div class="card_container">
                            <h4 class="team_name1"><b>${homeTeam}</b></h4>
                            <h4 class="score1"><b>${homePoints}</b></h4>
                            <h4 class="elo1"><b>${homeSpread}</b></h4>
                            <h4 class="team_name2"><b>${awayTeam}</b></h4>
                            <h4 class="score2"><b>${awayPoints}</b></h4>
                            <h4 class="elo2"><b>${awaySpread}</b></h4>
                        </div>
                    </div>`;  
    }

    week = gamesData[0]["week"]
    if (week <= 18) { weeksHeader.innerText = "Week " + week; }
    else { weeksHeader.innerText = week; }
    gameCards.innerHTML = cardHTML;
}

updateGames()