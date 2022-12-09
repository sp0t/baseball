function openCard(buttonId){ 
    var gameId = buttonId.replace("game_button_", ""); 
    $.ajax({
        type: 'POST', 
        url: '/get_game_info', 
        data: {'data' : gameId},
        beforeSend: function(){ 
            $('#large-card').show();
            $('#large-card-wrapper').hide();
            $('#loader').show();

            if (!!$('#calc')){ 
                $('#calc').hide()
            }

        },
        success: function (data){ 
            
            // Away Form
            var awayRoster = data['rosters']['away']; 
            for (i = 1; i < 10; i++){
                var newSelect = document.getElementsByName('ab_' + i)[0]; 
                for (n = 0; n < awayRoster.length; n++){
                    var newOption = document.createElement('option');
                    newOption.value = awayRoster[n]['id']; 
                    newOption.className = 'option'
                    newOption.innerHTML = awayRoster[n]['fullName'];
                    newSelect.append(newOption)
                }
            }
            var newSelect = document.getElementsByName('away_starter')[0]; 
            for (n = 0; n < awayRoster.length; n++){
                var newOption = document.createElement('option');
                newOption.value = awayRoster[n]['id'];
                newOption.className = 'option' 
                newOption.innerHTML = awayRoster[n]['fullName'];
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
                    newSelect.append(newOption)
                }
            }
            var newSelect = document.getElementsByName('home_starter')[0]; 
            for (n = 0; n < homeRoster.length; n++){
                var newOption = document.createElement('option');
                newOption.value = homeRoster[n]['id']; 
                newOption.className = 'option'
                newOption.innerHTML = homeRoster[n]['fullName'];
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


    $('#large-card').hide(); 

}

function makePrediction(){ 

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
    }
    else{ 
        var awayBetSize = 'No Bet!'
    }

    // Fill in new values 
    document.getElementsByName('away_edge')[0].textContent = awayEV; 
    document.getElementsByName('away_bet_size')[0].textContent = awayBetSize

    // Change Color 
    if (awayBetSize != 'No Bet!'){ 
        document.getElementsByName('away_bet_size')[0].style.color = 'green'
    }
    else{ 
        document.getElementsByName('away_bet_size')[0].style.color = 'red'
    }

}

function getHomeBet(){ 

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
    }
    else{ 
        var homeBetSize = 'No Bet!'
    }

    // Fill in new values 
    document.getElementsByName('home_edge')[0].textContent = homeEV; 
    document.getElementsByName('home_bet_size')[0].textContent = homeBetSize

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


