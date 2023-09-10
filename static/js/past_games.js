const seasonsDropdown = document.getElementById("seasons_dropdown");
const weeksDropdown = document.getElementById("weeks_dropdown");
const weeksHeader = document.getElementById("week_header");
const gameCards = document.getElementById("game_cards");

async function populateDropdowns() {
    const seasonResponse = await fetch("http://127.0.0.1:5000/seasons");
    const seasonData = await seasonResponse.json();

    let seasonHTML = ``;
    for (let i=seasonData.length-1; i>=0; i--) {
        seasonHTML += `<option value=${seasonData[i][0]}>${seasonData[i][0]}</option>`;
    }

    let weekHTML = ``;
    let weeks = [...Array(18).keys(), "WildCard", "Division", "ConfChamp", "SuperBowl"];
    console.log(weeks);
    for (const week of weeks.values()) {
        if (week <= 2) { 
            weekHTML += `<option value=${week+1}>${week+1}</option>`;
        }
        else {
            weekHTML += `<option value=${week}>${week}</option>`;
        }
        
    }
    console.log("dropdown populated");
    seasonsDropdown.innerHTML = seasonHTML;
    weeksDropdown.innerHTML = weekHTML;
}

async function populateGameCards(season="2022-2023", week=1) {
    const gameResponse = await fetch(`http://127.0.0.1:5000/games/${season}/${week}`);
    const gameData = await gameResponse.json();

    let cardHTML = ``;
    let homeSpread = 0;
    let awaySpread = 0;
    for (let game of gameData.values()) {
        let homeElo = game[7];
        let awayElo = game[8];
        let homePoints = game[5];
        let awayPoints = game[6];
        let predictionResult = "delete-2-16.png";

        //calculate spread from elo
        const spread = Math.abs((homeElo - awayElo)/25);
        if (homeElo > awayElo) { 
            homeSpread = "- " + spread.toFixed(1);
            awaySpread = "+" + spread.toFixed(1);

            //check if spread prediction was right
            if ((homePoints - awayPoints) > spread) { predictionResult = "checkmark-16.png"; }
        }
        else { 
            homeSpread = "+" + spread.toFixed(1); 
            awaySpread = "- " + spread.toFixed(1);

            //check if spread prediction was right
            if ((awayPoints - homePoints) > spread) { predictionResult = "checkmark-16.png"; }
        }

        cardHTML += `<div class="game_card">
                        <div class="card_container">
                            <h4 class="team_name1"><b>${game[3]}</b></h4>
                            <h4 class="score1"><b>${game[5]}</b></h4>
                            <h4 class="elo1"><b>${homeSpread}</b></h4>
                            <img src="../assets/${predictionResult}" class="result"></icon>
                            <h4 class="team_name2"><b>${game[4]}</b></h4>
                            <h4 class="score2"><b>${game[6]}</b></h4>
                            <h4 class="elo2"><b>${awaySpread}</b></h4>
                        </div>
                    </div>`;  
    }

    //make header
    if (week <= 18) { weeksHeader.innerText = "Week " + week + " - " + season; }
    else { weeksHeader.innerText = week + " - " + season; }
    
    gameCards.innerHTML = cardHTML;
}

function updatePastGamesPage() {
    const season = seasonsDropdown.value;
    const week = weeksDropdown.value;
    populateGameCards(season, week);
}

populateDropdowns();
populateGameCards();