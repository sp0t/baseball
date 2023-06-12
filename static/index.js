function openCard(buttonId){ 
    var gameId = buttonId.replace("game_button_", "");
    $.ajax({
        type: 'POST', 
        url: '/get_game_info', 
        data: {'data' : gameId},
        beforeSend: function(){ 
            $('.large-card').show();
            $('#large-card-wrapper').hide();
            $('#loader').show();

            if (!!$('#calc')){ 
                $('#calc').hide()
            }

        },
        success: function (data){ 
            // Away Form
            var awayRoster = data['rosters']['away']; 
            var position = data['rosters']['position']
            var pitcher = data['rosters']['pitcher']
            var newCard = document.getElementsByClassName('.large-card');
            var playerId;

            newCard.id = buttonId;
            for (i = 1; i < 10; i++){
                var newSelect = document.getElementsByName('ab_' + i)[0]; 
                for (n = 0; n < awayRoster.length; n++){
                    var newOption = document.createElement('option');
                    newOption.value = awayRoster[n]['id']; 
                    newOption.className = 'option'
                    newOption.innerHTML = awayRoster[n]['fullName'];

                    playerId = awayRoster[n]['id'];

                    if(position['away'][playerId] == i)
                        newOption.setAttribute('selected', true);
                    newSelect.append(newOption)
                }
            }
            var newSelect = document.getElementsByName('away_starter')[0]; 
            for (n = 0; n < awayRoster.length; n++){
                var newOption = document.createElement('option');
                newOption.value = awayRoster[n]['id'];
                newOption.className = 'option' 
                newOption.innerHTML = awayRoster[n]['fullName'];
                
                playerId = awayRoster[n]['id'];

                if(pitcher['away'][playerId] == 'starter')
                    newOption.setAttribute('selected', true);

                newSelect.append(newOption)
            }


            // Home Form
            var homeRoster = data['rosters']['home']; 
            for (i = 1; i < 10; i++){
                var newSelect = document.getElementsByName('hb_' + i)[0]; 
                for (n = 0; n < homeRoster.length; n++){
                    var newOption = document.createElement('option');
                    newOption.value = homeRoster[n]['id']; 
                    newOption.className = 'option'
                    newOption.innerHTML = homeRoster[n]['fullName'];

                    playerId = homeRoster[n]['id']; 

                    if(position['home'][playerId] == i)
                        newOption.setAttribute('selected', true);

                    newSelect.append(newOption)
                }
            }
            var newSelect = document.getElementsByName('home_starter')[0]; 
            for (n = 0; n < homeRoster.length; n++){
                var newOption = document.createElement('option');
                newOption.value = homeRoster[n]['id']; 
                newOption.className = 'option'
                newOption.innerHTML = homeRoster[n]['fullName'];

                playerId = homeRoster[n]['id']; 

                if(pitcher['home'][playerId] == 'starter')
                    newOption.setAttribute('selected', true);

                newSelect.append(newOption)
            }

            $('#loader').hide(); 


            if (!!$('#form')){ 
                $('#form').show()
            }

            if (!!$('#large-card-wrapper')){ 
                $('#large-card-wrapper').show()
            }
            console.log("Request Success!")
            document.getElementById('large-card-title').textContent = data['matchup'];
            document.getElementById('large-game-date').textContent = data['time'];

        }, 
    })
}

function closeCard(){ 
    
    var allOptions = document.querySelectorAll('.option');
    allOptions.forEach(option => {
        option.remove();
    });


    $('.large-card').hide(); 

}

function makePrediction(){ 

    gameId = document.getElementsByClassName('.large-card').id.replace('game_button_', '');

    // Get Form Data
    var awayBatters = []
    document.querySelectorAll('select[name^=ab]').forEach(function (node, idx){
        awayBatters.push(node.value)
    })

    var homeBatters = []
    document.querySelectorAll('select[name^=hb]').forEach(function (node, idx){
        homeBatters.push(node.value)
    })

    var awayStarter = document.getElementsByName('away_starter')[0].value
    var homeStarter = document.getElementsByName('home_starter')[0].value
    var matchup = document.getElementById('large-card-title').textContent

    var formData = {
        'away_batters': awayBatters, 
        'home_batters': homeBatters, 
        'away_starter': awayStarter, 
        'home_starter': homeStarter,
        'matchup': matchup,
        'game_id': gameId,
    }


    $.ajax({
        type: 'POST', 
        url: '/make_prediction', 
        data: { 'data' : JSON.stringify(formData)},
        beforeSend: function(){
            $('#large-card-wrapper').hide();
            $('#loader').show();
        }, 
        success: function(data){
            $('#loader').hide();
            $('#large-card-wrapper').show();
            $('#form').hide();
            $('#calc').show();

            document.getElementsByName('away_prob')[0].textContent = data['1a']['away_prob'] + '%'
            document.getElementsByName('away_prob_1')[0].textContent = data['1a']['away_prob'] + '%'
            document.getElementsByName('away_prob_2')[0].textContent = data['1b']['away_prob'] + '%'

            document.getElementsByName('home_prob')[0].textContent = data['1a']['home_prob'] + '%'
            document.getElementsByName('home_prob_1')[0].textContent = data['1a']['home_prob'] + '%'
            document.getElementsByName('home_prob_2')[0].textContent = data['1b']['home_prob'] + '%'

        }

    })

}

function getAwayBet(){ 

    gameId = document.getElementsByClassName('.large-card').id.replace('game_button_', '');

    // Get Which Model 
    var awayModelType = document.querySelector('input[name="away_model_type"]:checked').value;
    if (awayModelType == 'away_model_1a'){ 
        document.getElementsByName('away_prob')[0].textContent = document.getElementsByName('away_prob_1')[0].textContent

    }
    else{ 
        document.getElementsByName('away_prob')[0].textContent = document.getElementsByName('away_prob_2')[0].textContent

    }



    // Get Data
    var awayProbValue = document.getElementsByName('away_prob')[0].textContent
    var awayAdjustment = document.getElementsByName('away_adjustment')[0].value
    var awayOdds = parseFloat(document.getElementsByName('away_odds')[0].value)



    awayProbValue = parseFloat(awayProbValue.replace("%",""))/100
    awayAdjustment = parseFloat(awayAdjustment.replace("%",""))/100
    awayProbValue = awayProbValue + awayAdjustment

    var awayMinEdge = document.getElementsByName('away_min_edge')[0].value
    var awayMinProb = document.getElementsByName('away_min_prob')[0].value
    awayMinEdge = parseFloat(awayMinEdge.replace("%", ""))/100
    awayMinProb = parseFloat(awayMinProb.replace("%", ""))/100

    // Convert Odds 
    if (awayOdds > 0) { 
        var awayOddsDecimal = (awayOdds/100)+1
    }
    else { 
        var awayOddsDecimal = (-100/awayOdds)+1
    }

    // Calculate EV
    awayEV = (awayProbValue)*(awayOddsDecimal-1) - (1-awayProbValue)
    awayEV = awayEV.toFixed(3)

    if (awayEV > 0.03 && awayProbValue > 0.48){ 

        var awayBetSize = 0.05*(((awayOddsDecimal*awayProbValue)-(1-awayProbValue))/awayProbValue)
        awayBetSize = awayBetSize.toFixed(3)

        var data;

        if(awayModelType == 'away_model_1a')
            data = {'game_id':gameId, 'team':'away', 'modal':'A', 'Ev': awayEV * 100, 'betSize': awayBetSize * 100}
        else
            data = {'game_id':gameId, 'team':'away', 'modal':'B', 'Ev': awayEV * 100, 'betSize': awayBetSize * 100}
    }
    else{ 
        var awayBetSize = 'No Bet!'
    }

    // Fill in new values 
    document.getElementsByName('away_edge')[0].textContent = awayEV; 
    document.getElementsByName('away_bet_size')[0].textContent = awayBetSize

    $.ajax({
        url: '/update_predicdata', 
        type: 'POST', 
        data: { 'data' : JSON.stringify(data)},
        error: function (error) {
            alert('error; ' + eval(error));
        }
    })

    // Change Color 
    if (awayBetSize != 'No Bet!'){ 
        document.getElementsByName('away_bet_size')[0].style.color = 'green'
    }
    else{ 
        document.getElementsByName('away_bet_size')[0].style.color = 'red'
    }

}

function getHomeBet(){ 
    gameId = document.getElementsByClassName('.large-card').id.replace('game_button_', '');

    var homeModelType = document.querySelector('input[name="home_model_type"]:checked').value;
    if (homeModelType == 'home_model_1a'){ 
        document.getElementsByName('home_prob')[0].textContent = document.getElementsByName('home_prob_1')[0].textContent

    }
    else{ 
        document.getElementsByName('home_prob')[0].textContent = 'boobs1b'
        document.getElementsByName('home_prob')[0].textContent = document.getElementsByName('home_prob_2')[0].textContent

    }



    // Get Data
    var homeProbValue = document.getElementsByName('home_prob')[0].textContent
    var homeAdjustment = document.getElementsByName('home_adjustment')[0].value
    var homeOdds = parseFloat(document.getElementsByName('home_odds')[0].value)

    homeProbValue = parseFloat(homeProbValue.replace("%",""))/100
    homeAdjustment = parseFloat(homeAdjustment.replace("%",""))/100
    homeProbValue = homeProbValue + homeAdjustment

    var homeMinEdge = document.getElementsByName('home_min_edge')[0].value
    var homeMinProb = document.getElementsByName('home_min_prob')[0].value
    homeMinEdge = parseFloat(homeMinEdge.replace("%", ""))/100
    homeMinProb = parseFloat(homeMinProb.replace("%", ""))/100

    // Convert Odds 
    if (homeOdds > 0) { 
        var homeOddsDecimal = (homeOdds/100)+1
    }
    else { 
        var homeOddsDecimal = (-100/homeOdds)+1
    }

    // Calculate EV
    homeEV = (homeProbValue)*(homeOddsDecimal-1) - (1-homeProbValue)
    homeEV = homeEV.toFixed(3)

    if (homeEV > 0.03 && homeProbValue > 0.48){ 

        var homeBetSize = 0.05*(((homeOddsDecimal*homeProbValue)-(1-homeProbValue))/homeProbValue)
        homeBetSize = homeBetSize.toFixed(3)

        var data;

        if(homeModelType == 'home_model_1a')
            data = {'game_id':gameId, 'team':'home', 'modal':'A','Ev': homeEV * 100, 'betSize': homeBetSize * 100}
        else
            data = {'game_id':gameId, 'team':'home', 'modal':'B','Ev': homeEV * 100, 'betSize': homeBetSize * 100}
    }
    else{ 
        var homeBetSize = 'No Bet!'
    }

    // Fill in new values 
    document.getElementsByName('home_edge')[0].textContent = homeEV; 
    document.getElementsByName('home_bet_size')[0].textContent = homeBetSize

    $.ajax({
        url: '/update_predicdata', 
        type: 'POST', 
        data: { 'data' : JSON.stringify(data)},
        error: function (error) {
            alert('error; ' + eval(error));
        }
    })


    // Change Color 
    if (homeBetSize != 'No Bet!'){ 
        document.getElementsByName('home_bet_size')[0].style.color = 'green'
    }
    else{ 
        document.getElementsByName('home_bet_size')[0].style.color = 'red'
    }

}

$(document).ready(function() {
    // Toggle menu on click
    $("#menu-toggler").click(function() {
      toggleBodyClass("menu-active");
    });
  
    function toggleBodyClass(className) {
      document.body.classList.toggle(className);
    }
  
   });

function queryDatabase(){ 

    // Get Data
    var playerId = document.getElementsByName('player')[0].value; 
    var queryDate = document.getElementsByName('date')[0].value; 
    var queryLength = document.getElementsByName('length')[0].value; 
    var statType = document.getElementsByName('type')[0].value; 

    queryData = {'playerId': playerId, 'queryDate': queryDate, 'statType': statType,'queryLength': queryLength}

    $.ajax({ 
        type: 'POST', 
        url: '/query', 
        data: { 'data' : JSON.stringify(queryData)},
        beforeSend: function(){ 
            $('#loader').show();
            alert('gang')
        }, 
        success: function(data){
            $('#loader').hide();
            alert('all done!'); 
            
            if (data == "Sorry, no data found!"){ 
                var response = document.createElement('div'); 
                response.textContent = data; 
                
            }

            else{ 
                var response = document.createElement('div'); 
                response.textContent = data; 
            }
            document.getElementById('query-container').appendChild(response)
        }
    })
}

function updateDatabase(){ 

    $.ajax({
        url: '/update_data', 
        type: 'POST', 
        beforeSend: function (){ 
            alert('Updating Database. This should take < 30 seconds. Press Enter or click OK.'); 
            document.getElementById('update-loader').style.display = 'block';
        },
        success: function (data){ 
            document.getElementById('update-loader').style.display = 'none';
            alert('Update Complete! Page will refresh now.')
            document.location.reload()
            // document.getElementById('last-record').textContent = 'Last Record: ' + data['update_data']['record']
            // document.getElementById('last-time').textContent = 'Last Updated ' + data['update_data']['time']
        }
    })
}

function updateTeam(){ 
    $.ajax({
        url: '/updateTeam', 
        type: 'POST', 
        beforeSend: function (){ 
            alert('Updating Teamtable. This should take < 30 seconds. Press Enter or click OK.'); 
        },
        success: function (data){ 
            alert('Update Complete!')
            document.location.reload()
            // document.getElementById('last-record').textContent = 'Last Record: ' + data['update_data']['record']
            // document.getElementById('last-time').textContent = 'Last Updated ' + data['update_data']['time']
        }
    })
}

function  downLoadBatterData(id){
    gameId = ''
    
    if(id == 0)
        gameId = document.getElementsByClassName('.large-card').id.replace('game_button_', '');
    else
        gameId = id.replace('load_batter_', '');
        
    $.ajax({
        type: 'POST', 
        url: '/download_batter_data', 
        data: {'data' : gameId},
        beforeSend: function(){ 
            console.log('before sending');
        },
        success: function (data){ 
            if (data == 'OK')
                alert('Success')
            else if (data == 'NO')
                alert('No data')
            // var a = document.createElement('a');
            // a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(data);
            // a.download = `BatterData_${gameId}.csv`;
            // document.body.append(a);
            // a.click();
            // a.remove();
        }
    })
}

function  downLoadPitcherData(id){
    gameId = ''

    if(id == 0)
        gameId = document.getElementsByClassName('.large-card').id.replace('game_button_', '');        
    else
        gameId = id.replace('load_pitcher_', '');
    
    $.ajax({
        type: 'POST', 
        url: '/download_pitcher_data', 
        data: {'data' : gameId},
        beforeSend: function(){ 
            console.log('before sending');
        },
        success: function (data){ 
            if (data == 'OK')
                alert('Success')
            else if (data == 'NO')
                alert('No data')
            // var a = document.createElement('a');
            // a.href = 'data:text/csv;charset=utf-8,' + encodeURIComponent(data);
            // a.download = `PitcherData_${gameId}.csv`;
            // document.body.append(a);
            // a.click();
            // a.remove();
        }
    })
}


