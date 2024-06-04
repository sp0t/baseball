$(document).ready(function(){

    $('#darkModeToggle').click(function(){
        if (localStorage.getItem("darkMode") === "enabled") {
            toggleDarkMode(0);
            localStorage.setItem("darkMode", "disabled");
        } else {
            toggleDarkMode(1);
            localStorage.setItem("darkMode", "enabled");
        }
    });
})

function openCard(buttonId){ 
    var gameId = buttonId.replace("game_button_", "");
    $.ajax({
        type: 'POST', 
        url: '/get_game_info', 
        data: {'data' : gameId},
        beforeSend: function(){ 
            $('.large-card').css('width', '50%').css('height', '670px').show();
            $('#large-card-wrapper').hide();
            $('#loader').show();

            if (!!$('#calc')){ 
                $('#calc').hide()
            }

            $('#betform').hide();

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

            for (var j=1; j <6; j++) {
                var newSelect = document.getElementsByName('as_' + j)[0]; 
                for (n = 0; n < awayRoster.length; n++){
                    var newOption = document.createElement('option');
                    newOption.value = awayRoster[n]['id'];
                    newOption.className = 'option' 
                    newOption.innerHTML = awayRoster[n]['fullName'];
                    
                    playerId = awayRoster[n]['id'];
    
                    if(j == 1 && pitcher['away'][playerId] == 'starter')
                        newOption.setAttribute('selected', true);
    
                    newSelect.append(newOption)
                }
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

            for (var j=1; j <6; j++) {
                var newSelect = document.getElementsByName('hs_' + j)[0]; 
                for (n = 0; n < homeRoster.length; n++){
                    var newOption = document.createElement('option');
                    newOption.value = homeRoster[n]['id']; 
                    newOption.className = 'option'
                    newOption.innerHTML = homeRoster[n]['fullName'];
    
                    playerId = homeRoster[n]['id']; 
    
                    if(j == 1 && pitcher['home'][playerId] == 'starter')
                        newOption.setAttribute('selected', true);
    
                    newSelect.append(newOption)
                }
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


function openBetModal(gameid){ 
    data = {}
    data['gameid'] = gameid
    data['site'] = 'NOSITE'
    $.ajax({
        type: 'POST', 
        url: '/get_bet_info', 
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        beforeSend: function(){ 
            $('.large-card').css('width', '350px').css('height', '430px').show();
            $('#large-card-wrapper').hide();
            $('#loader').show();

        },
        success: function (data){ 
            $('#loader').hide();
            $('#large-card-wrapper').show();
            $('#form').hide();
            $('#calc').hide();
            $('#betform').show();
            $("#modal_game_id").val(gameid);

            var betdate = document.getElementById('betdate');
            betdate.innerHTML = data['date'];

            var away = document.getElementById('awayname');
            away.value = data['away'];

            var home = document.getElementById('homename');
            home.value = data['home'];

            var teams = document.getElementById('teams'); 

            var newOption = document.createElement('option');
            newOption.value = ''; 
            newOption.className = 'bet-input-form'
            newOption.innerHTML = '-';
            teams.append(newOption);

            var awayOption = document.createElement('option');
            awayOption.value = data['away']; 
            awayOption.className = 'bet-input-form'
            awayOption.innerHTML = data['away'];
            if(data['away'] == data['place'])
                awayOption.setAttribute('selected', true);

            teams.append(awayOption);

            var homeOption = document.createElement('option');
            homeOption.value = data['home']; 
            homeOption.className = 'bet-input-form'
            homeOption.innerHTML = data['home'];

            if(data['home'] == data['place'])
                homeOption.setAttribute('selected', true);

            teams.append(homeOption);

            var sites = document.getElementById('sites'); 

            var newOption = document.createElement('option');
            newOption.value = ''; 
            newOption.className = 'bet-input-form'
            newOption.innerHTML = '-';
            sites.append(newOption);

            for (var i = 0; i<data['site_list'].length; i++) {
                newOption = document.createElement('option');
                newOption.value = data['site_list'][i]; 
                newOption.className = 'bet-input-form'
                newOption.innerHTML = data['site_list'][i];
                if (data['site_list'][i] == data['site'])
                    newOption.setAttribute('selected', true);
                sites.append(newOption);
            }

            if (data['state'] == 1) {
                var oddvalue = document.getElementById('oddvalue');
                oddvalue.value = data['odds'];

                var stakevalue = document.getElementById('stakevalue');
                stakevalue.value = data['stake'];

                var winvalue = document.getElementById('winvalue');
                winvalue.value = data['wins'];
            }

        }, 
    })
}


function changeBetSite(site) {
    var gameid = $("#modal_game_id").val();

    data = {}
    data['gameid'] = gameid
    data['site'] = site

    $.ajax({
        type: 'POST', 
        url: '/get_bet_info', 
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        beforeSend: function(){ 
        },
        success: function (data){ 
            var oddvalue = document.getElementById('oddvalue');
            oddvalue.value = data['odds'];

            var stakevalue = document.getElementById('stakevalue');
            stakevalue.value = data['stake'];

            var winvalue = document.getElementById('winvalue');
            winvalue.value = data['wins'];
        }, 
    })
}

function changeStakeSize() {
    var stake = $("#autobet-stake").val();

    $.ajax({
        type: 'POST', 
        url: '/set_autoStake_size', 
        data: {
            'stake' : stake,
        },
        beforeSend: function(){ 

        },
        success: function (data){

         }, 
    })
}

function roundToNearestInteger(value) {
    const threshold = 0.04;
    const multiplier = 1 / threshold;
    const floatValue = Math.round(value * multiplier);
    return floatValue / multiplier;
}

function calWinsWithOdds(value) {
    var stake = document.getElementById('stakevalue').value;
    if(stake == 0)
        return;

    if(value == '' || value == '+' || value == '-')
        return;
    var intodd = parseInt(value)

    var decodd = intodd > 0 ? intodd / 100: 1 - 100 / intodd;

    var wins = intodd > 0 ? decodd * stake: (decodd - 1) * stake;

    var winvalue = document.getElementById('winvalue');
    winvalue.value = roundToNearestInteger(wins);
}

function calWinsWithStake(value) {
    var odds = document.getElementById('oddvalue').value;
    if(odds == '' || odds == '+' || odds == '-')
        return;

    if(value == 0)
        return;

    var intodd = parseInt(odds)
    var decodd = intodd > 0 ? intodd / 100: 1 - 100 / intodd;

    var wins = intodd > 0 ? decodd * value: (decodd - 1) * value;

    var winvalue = document.getElementById('winvalue');
    winvalue.value = roundToNearestInteger(wins);
}

function closeCard(){ 
    
    var allOptions = document.querySelectorAll('.option');
    allOptions.forEach(option => {
        option.remove();
    });

    var selectElement = document.getElementById('teams');
    var options = selectElement.querySelectorAll('.bet-input-form');

    options.forEach(option => {
        option.remove();
    });

    selectElement = document.getElementById('sites');
    var options = selectElement.querySelectorAll('.bet-input-form');

    options.forEach(option => {
        option.remove();
    });


    $('.large-card').hide(); 

}


function updateBetInformation(value) {
    var data = {};
    var betdate = document.getElementById('betdate').textContent;
    var away = document.getElementById('awayname').value;
    var home = document.getElementById('homename').value;
    var place = document.getElementById('teams').value;
    var odds = document.getElementById('oddvalue').value;
    var stake = document.getElementById('stakevalue').value;
    var wins = document.getElementById('winvalue').value;
    var site = document.getElementById('sites').value;

    // if(site == 'sports411.ag'){
    //     wins = (wins * 0.9).toString();
    //     stake = (stake * 0.9).toString();
    // }

    if (betdate == '') {
        alert('invalid betdate!');
        return;
    }

    if (away == '') {
        alert('Please input away team!');
        return;
    }

    if (home == '') {
        alert('Please input home team!');
        return;
    }

    if (place == '') {
        alert('Please select betplace!');
        return;
    }

    if (odds == '') {
        alert('Please input Odd value!');
        return;
    }

    if (stake == 0) {
        alert('Please input stake amount!');
        return;
    }

    if (wins == 0) {
        alert('Please input win amount!');
        return;
    }

    if (site == '') {
        alert('Please select betting site!');
        return;
    }
    
    data['betdate'] = betdate;
    data['away'] = away;
    data['home'] = home;
    data['place'] = place;
    data['odds'] = odds;
    data['stake'] = stake;
    data['wins'] = wins;
    data['flag'] = value;
    data['site'] = site;

    $.ajax({
        type: 'POST', 
        url: '/betting', 
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        beforeSend: function(){ 
        },
        success: function (data){ 
            closeCard();
        }
    })
}


function makePrediction(model){ 

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

    // var awayStarter = document.getElementsByName('away_starter')[0].value
    var awayStarters = []
    document.querySelectorAll('select[name^=as]').forEach(function (node, idx){
        awayStarters.push(node.value)
    })

    // var homeStarter = document.getElementsByName('home_starter')[0].value

    var homeStarters = []
    document.querySelectorAll('select[name^=hs]').forEach(function (node, idx){
        homeStarters.push(node.value)
    })
    var matchup = document.getElementById('large-card-title').textContent

    var formData = {
        'away_batters': awayBatters, 
        'home_batters': homeBatters, 
        'away_starters': awayStarters, 
        'home_starters': homeStarters,
        'matchup': matchup,
        'game_id': gameId,
        'model': model
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
            $('#betform').hide();
            $('#calc').show();

            document.getElementById('stake_size').textContent = 'Today Bet Size is ' + data['1a']['stake'];

            if(data['model'] == 'a') {
                document.getElementsByName('away_prob')[0].textContent = data['1a']['away_prob'] + '%'
                document.getElementsByName('away_prob_1')[0].textContent = data['1a']['away_prob'] + '%'
                document.getElementsByName('away_prob_2')[0].textContent = data['1b']['away_prob'] + '%'
                document.getElementsByName('away_prob_1')[0].setAttribute('odd-value', data['1a']['away_odd']);
                document.getElementsByName('away_prob_2')[0].setAttribute('odd-value', data['1b']['away_odd']);
                document.getElementsByName('away_odds')[0].value = data['1a']['away_odd'];
    
                document.getElementsByName('home_prob')[0].textContent = data['1a']['home_prob'] + '%'
                document.getElementsByName('home_prob_1')[0].textContent = data['1a']['home_prob'] + '%'
                document.getElementsByName('home_prob_2')[0].textContent = data['1b']['home_prob'] + '%'
                document.getElementsByName('home_prob_1')[0].setAttribute('odd-value', data['1a']['home_odd']);
                document.getElementsByName('home_prob_2')[0].setAttribute('odd-value', data['1b']['home_odd']);
                document.getElementsByName('home_odds')[0].value = data['1a']['home_odd'];

            } else if (data['model'] == 'c') {
                document.getElementsByName('away_prob')[0].textContent = data['1c']['away_prob'] + '%'
                document.getElementsByName('away_prob_3')[0].textContent = data['1c']['away_prob'] + '%'
                document.getElementsByName('away_prob_3')[0].setAttribute('odd-value', data['1c']['away_odd']);
                document.getElementsByName('away_odds')[0].value = data['1c']['away_odd'];
    
                document.getElementsByName('home_prob')[0].textContent = data['1c']['home_prob'] + '%'
                document.getElementsByName('home_prob_3')[0].textContent = data['1c']['home_prob'] + '%'
                document.getElementsByName('home_prob_3')[0].setAttribute('odd-value', data['1c']['home_odd']);
                document.getElementsByName('home_odds')[0].value = data['1c']['home_odd'];
            }

        }

    })

}

function getAwayBet(){ 

    gameId = document.getElementsByClassName('.large-card').id.replace('game_button_', '');

    // Get Which Model 
    var awayModelType = document.querySelector('input[name="away_model_type"]:checked').value;
    if (awayModelType == 'away_model_1a'){ 
        document.getElementsByName('away_prob')[0].textContent = document.getElementsByName('away_prob_1')[0].textContent
        document.getElementsByName('away_odds')[0].value = parseInt(document.getElementsByName('away_prob_1')[0].getAttribute('odd-value'), 10)
    }
    else if (awayModelType == 'away_model_1b'){ 
        document.getElementsByName('away_prob')[0].textContent = document.getElementsByName('away_prob_2')[0].textContent
        document.getElementsByName('away_odds')[0].value = parseInt(document.getElementsByName('away_prob_2')[0].getAttribute('odd-value'), 10)
    } else {
        document.getElementsByName('away_prob')[0].textContent = document.getElementsByName('away_prob_3')[0].textContent
        document.getElementsByName('away_odds')[0].value = parseInt(document.getElementsByName('away_prob_3')[0].getAttribute('odd-value'), 10)
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

    // if (awayEV > 0.03 && awayProbValue > 0.48){ 

    //     var awayBetSize = 0.05*(((awayOddsDecimal*awayProbValue)-(1-awayProbValue))/awayProbValue)
    //     awayBetSize = awayBetSize.toFixed(3)

    //     var data;

    //     if(awayModelType == 'away_model_1a')
    //         data = {'game_id':gameId, 'team':'away', 'modal':'A', 'Ev': awayEV * 100, 'betSize': awayBetSize * 100}
    //     else
    //         data = {'game_id':gameId, 'team':'away', 'modal':'B', 'Ev': awayEV * 100, 'betSize': awayBetSize * 100}
    // }
    // else{ 
    //     var awayBetSize = 'No Bet!'
    // }

    // Fill in new values 
    document.getElementsByName('away_edge')[0].textContent = awayEV; 
    // document.getElementsByName('away_bet_size')[0].textContent = awayBetSize

    // $.ajax({
    //     url: '/update_predicdata', 
    //     type: 'POST', 
    //     data: { 'data' : JSON.stringify(data)},
    //     error: function (error) {
    //         alert('error; ' + eval(error));
    //     }
    // })

    // Change Color 
    // if (awayBetSize != 'No Bet!'){ 
    //     document.getElementsByName('away_bet_size')[0].style.color = 'green'
    // }
    // else{ 
    //     document.getElementsByName('away_bet_size')[0].style.color = 'red'
    // }

}

function getHomeBet(){ 
    gameId = document.getElementsByClassName('.large-card').id.replace('game_button_', '');

    var homeModelType = document.querySelector('input[name="home_model_type"]:checked').value;
    if (homeModelType == 'home_model_1a'){ 
        document.getElementsByName('home_prob')[0].textContent = document.getElementsByName('home_prob_1')[0].textContent
        document.getElementsByName('home_odds')[0].value = parseInt(document.getElementsByName('home_prob_1')[0].getAttribute('odd-value'), 10)

    }
    else if (homeModelType == 'home_model_1b'){ 
        document.getElementsByName('home_prob')[0].textContent = document.getElementsByName('home_prob_2')[0].textContent
        document.getElementsByName('home_odds')[0].value = parseInt(document.getElementsByName('home_prob_2')[0].getAttribute('odd-value'), 10)
    } else {
        document.getElementsByName('home_prob')[0].textContent = document.getElementsByName('home_prob_3')[0].textContent
        document.getElementsByName('home_odds')[0].value = parseInt(document.getElementsByName('home_prob_3')[0].getAttribute('odd-value'), 10)
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

    // if (homeEV > 0.03 && homeProbValue > 0.48){ 

    //     var homeBetSize = 0.05*(((homeOddsDecimal*homeProbValue)-(1-homeProbValue))/homeProbValue)
    //     homeBetSize = homeBetSize.toFixed(3)

    //     var data;

    //     if(homeModelType == 'home_model_1a')
    //         data = {'game_id':gameId, 'team':'home', 'modal':'A','Ev': homeEV * 100, 'betSize': homeBetSize * 100}
    //     else
    //         data = {'game_id':gameId, 'team':'home', 'modal':'B','Ev': homeEV * 100, 'betSize': homeBetSize * 100}
    // }
    // else{ 
    //     var homeBetSize = 'No Bet!'
    // }

    // Fill in new values 
    document.getElementsByName('home_edge')[0].textContent = homeEV; 
    // document.getElementsByName('home_bet_size')[0].textContent = homeBetSize

    // $.ajax({
    //     url: '/update_predicdata', 
    //     type: 'POST', 
    //     data: { 'data' : JSON.stringify(data)},
    //     error: function (error) {
    //         alert('error; ' + eval(error));
    //     }
    // })


    // Change Color 
    // if (homeBetSize != 'No Bet!'){ 
    //     document.getElementsByName('home_bet_size')[0].style.color = 'green'
    // }
    // else{ 
    //     document.getElementsByName('home_bet_size')[0].style.color = 'red'
    // }

}

function changeAwayAdjustment() {
    // Get Data
    var awayProbValue = document.getElementsByName('away_prob')[0].textContent
    var awayAdjustment = document.getElementsByName('away_adjustment')[0].value

    awayProbValue = parseFloat(awayProbValue.replace("%",""))
    awayProbValue = awayProbValue + awayAdjustment * 100
    document.getElementsByName('away_prob')[0].textContent = awayProbValue + '%'

    away_dec_odd = (1.03 / (awayProbValue / 100)).toFixed(2)
    if(away_dec_odd >= 2)
        away_odd = ((away_dec_odd - 1) * 100).toFixed(2)
    else if(away_dec_odd < 2)
        away_odd = (100/(1-away_dec_odd)).toFixed(2)

    document.getElementsByName('away_odds')[0].value = away_odd

    var awayEV = (awayProbValue/100)*(away_dec_odd-1) - (1-awayProbValue/100)
    awayEV = awayEV.toFixed(3)

    document.getElementsByName('away_edge')[0].textContent = awayEV; 
}


function changeHomeAdjustment() {
    // Get Data
    var homeProbValue = document.getElementsByName('home_prob')[0].textContent
    var homeAdjustment = document.getElementsByName('home_adjustment')[0].value

    homeProbValue = parseFloat(homeProbValue.replace("%",""))
    homeProbValue = homeProbValue + homeAdjustment * 100
    document.getElementsByName('home_prob')[0].textContent = homeProbValue + '%'

    home_dec_odd = (1.03 / (homeProbValue / 100)).toFixed(2)
    if(home_dec_odd >= 2)
        home_odd = ((home_dec_odd - 1) * 100).toFixed(2)
    else if(home_dec_odd < 2)
    home_odd = (100/(1-home_dec_odd)).toFixed(2)

    document.getElementsByName('home_odds')[0].value = home_odd

    var homeEV = (homeProbValue/100)*(home_dec_odd-1) - (1-homeProbValue/100)
    homeEV = homeEV.toFixed(3)

    document.getElementsByName('home_edge')[0].textContent = homeEV;
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
            document.location.reload()
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
                alert('Success Batter Data Added')
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
                alert('Success Pitcher Data Added')
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

function  getPlayerStats(id, type){
    var param = {'game_id' : id, 'type': type}
    $.ajax({
        type: 'POST', 
        url: '/get_PlayerStats',
        data: { 'data' : JSON.stringify(param)},
        beforeSend: function(){ 
            console.log('before sending');
        },
        success: function (data){ 
            var html = '';
                const divContainer = document.getElementById(id);
                const divContent = document.getElementById(`stats_${id}`);
        
                const topPosition = divContainer.offsetTop;
                const height = divContainer.offsetHeight;
                const bottomPosition = topPosition + height;
                var awayBatterRat = 0, homeBatterRat = 0, awayStarterRat = 0, homeStarterRat = 0;

                if(data.model == 1) {
                    for(var i=0; i < data.batter.length; i++) {
                        var team = data.batter[i].position.substring(0, 4);
    
                        if(team == 'Away')
                        homeStarterRat = homeStarterRat + data.batter[i].difficulty_rating;
                        else if(team == 'Home')
                            awayStarterRat = awayStarterRat + data.batter[i].difficulty_rating;
                    }

                    for(var j=0; j < data.pitcher.length; j++) {
                        var team = data.pitcher[j].position.substring(0, 4);
                        
                        if(team == 'Away')
                            homeBatterRat = data.pitcher[j].difficulty_rating;
                        else if(team == 'Home')
                            awayBatterRat = data.pitcher[j].difficulty_rating;
                    }
                }

                homeStarterRat = homeStarterRat / 9;
                homeStarterRat = homeStarterRat.toFixed(3);

                awayStarterRat = awayStarterRat / 9;
                awayStarterRat = awayStarterRat.toFixed(3);


                divContent.style.top = `${bottomPosition}px`;
                divContent.style.left = '160px';
                divContent.style.width = `${window.innerWidth - 165 * 2}px`;

                if(data.batter != undefined && data.batter.length > 0) {
                    html += '<div class="batter-container">'
                    html += '<div style="background-color:black">GID</div>'
                    html += '<div style="background-color:black">POS</div>'
                    html += '<div style="background-color:black">PID</div>'
                    html += '<div style="background-color:black">CAB</div>'
                    html += '<div style="background-color:black">CAVG</div>'
                    html += '<div style="background-color:black">CHR</div>'
                    html += '<div style="background-color:black">COBP</div>'
                    html += '<div style="background-color:black">COPS</div>'
                    html += '<div style="background-color:black">CRBI</div>'
                    html += '<div style="background-color:black">CSLG</div>'
                    html += '<div style="background-color:black">CSO</div>'
                    html += '<div style="background-color:black">RAB</div>'
                    html += '<div style="background-color:black">RAVG</div>'
                    html += '<div style="background-color:black">RHR</div>'
                    html += '<div style="background-color:black">ROBP</div>'
                    html += '<div style="background-color:black">ROPS</div>'
                    html += '<div style="background-color:black">RRBI</div>'
                    html += '<div style="background-color:black">RSLG</div>'
                    html += '<div style="background-color:black">RSO</div>'
                    html += '<div style="background-color:black">RAT</div>'
                    html += '<div style="background-color:black">OPRAT</div>'
                    

                    for(var x in data.batter) {
                        html += `<div>${data.batter[x].game_id}</div>`
                        html += `<div>${data.batter[x].position}</div>`
                        html += `<div>${data.batter[x].player_id}</div>`
                        html += `<div>${data.batter[x].career_atbats}</div>`
                        html += `<div>${data.batter[x].career_avg}</div>`
                        html += `<div>${data.batter[x].career_homeruns}</div>`
                        html += `<div>${data.batter[x].career_obp}</div>`
                        html += `<div>${data.batter[x].career_ops}</div>`
                        html += `<div>${data.batter[x].career_rbi}</div>`
                        html += `<div>${data.batter[x].career_slg}</div>`
                        html += `<div>${data.batter[x].career_strikeouts}</div>`
                        html += `<div>${data.batter[x].recent_atbats}</div>`
                        html += `<div>${data.batter[x].recent_avg}</div>`
                        html += `<div>${data.batter[x].recent_homeruns}</div>`
                        html += `<div>${data.batter[x].recent_obp}</div>`
                        html += `<div>${data.batter[x].recent_ops}</div>`
                        html += `<div>${data.batter[x].recent_rbi}</div>`
                        html += `<div>${data.batter[x].recent_slg}</div>`
                        html += `<div>${data.batter[x].recent_strikeouts}</div>`

                        if(data.model == 0) {
                            html += `<div></div>`
                            html += `<div></div>`
                        } else if(data.model == 1) {
                            html += `<div>${data.batter[x].difficulty_rating}</div>`
                            html += `<div>${data.batter[x].position.substring(0, 4) == 'Away'?awayBatterRat: homeBatterRat}</div>`
                        }

                    }
                    html += '</div>';
                }

                if(data.pitcher != undefined && data.pitcher.length > 0) {
                    html += '<div class="pitcher-container">'
                    html += '<div style="background-color:black">GID</div>'
                    html += '<div style="background-color:black">POS</div>'
                    html += '<div style="background-color:black">PID</div>'
                    html += '<div style="background-color:black">CERA</div>'
                    html += '<div style="background-color:black">CHR</div>'
                    html += '<div style="background-color:black">CWHP</div>'
                    html += '<div style="background-color:black">CBF</div>'
                    html += '<div style="background-color:black">RERA</div>'
                    html += '<div style="background-color:black">RHR</div>'
                    html += '<div style="background-color:black">RWHP</div>'
                    html += '<div style="background-color:black">RBF</div>'
                    html += '<div style="background-color:black">RAT</div>'
                    html += '<div style="background-color:black">OPRAT</div>'
                    

                    for(var y in data.pitcher) {
                        html += `<div>${data.pitcher[y].game_id}</div>`
                        html += `<div>${data.pitcher[y].position}</div>`
                        html += `<div>${data.pitcher[y].player_id}</div>`
                        html += `<div>${data.pitcher[y].career_era}</div>`
                        html += `<div>${data.pitcher[y].career_homeruns}</div>`
                        html += `<div>${data.pitcher[y].career_whip}</div>`
                        html += `<div>${data.pitcher[y].career_battersfaced}</div>`
                        html += `<div>${data.pitcher[y].recent_era}</div>`
                        html += `<div>${data.pitcher[y].recent_homeruns}</div>`
                        html += `<div>${data.pitcher[y].recent_whip}</div>`
                        html += `<div>${data.pitcher[y].recent_battersfaced}</div>`
                        if(data.model == 0) {
                            html += `<div></div>`
                            html += `<div></div>`
                        } else if(data.model == 1) {
                            html += `<div>${data.pitcher[y].difficulty_rating}</div>`
                            html += `<div>${data.pitcher[y].position.substring(0, 4) == 'Away'?awayStarterRat: homeStarterRat}</div>`
                        }
                    }

                    html += '</div>'
                }
              // Show the div container
              divContent.innerHTML = html;
        },
        error: function() {
        }
    })
}

function setAutoBetState(gameid, state) {
    console.log('gameid', gameid)
    console.log('state', state)
    var value = state? 1: 0;

    $.ajax({
        type: 'POST', 
        url: '/set_autoBet_state', 
        data: {
            'gameid' : gameid,
            'value' : value
        },
        beforeSend: function(){ 

        },
        success: function (data){

         }, 
    })
}

function formatToFinancial(num) {
    num = Number(num); // Convert to number if not already
    return num.toLocaleString('en-US', {
        style: 'currency',
        currency: 'USD',
        minimumFractionDigits: 0,
        maximumFractionDigits: 0
    });
}


// function selectPlayer(){ 
//     $.ajax({
//         url: '/selectPlayer', 
//         type: 'GET',
//         success: function (){ 
//             location.href = '/selectPlayer';
//         }
//     })
// }

function toggleDarkMode() {
    if (localStorage.getItem("darkMode") === "enabled") {
        localStorage.setItem("darkMode", "disabled");
        $(".div-container-dark").addClass("div-container").removeClass("div-container-dark");
        $(".home_label-dark").addClass("home_label").removeClass("home_label-dark");
        $(".nav-dark").addClass("nav").removeClass("nav-dark");
        
    } else {
        localStorage.setItem("darkMode", "enabled");
        $(".div-container").addClass("div-container-dark").removeClass("div-container");
        $(".home_label").addClass("home_label-dark").removeClass("home_label");
        $(".nav").addClass("nav-dark").removeClass("nav");
    }

    $("body").toggleClass("dark-mode");
    $("select").toggleClass("select-dark-mode");
    $("a").toggleClass("dark-mode");
    $("p").toggleClass("dark-mode");
    $("div").toggleClass("dark-mode");
    $("span").toggleClass("dark-mode");
    $("table").toggleClass("dark-mode");
    $("#stake").toggleClass("dark-mode");
    $("#gameTh").toggleClass("thead-dark");
    $("#gameTd").toggleClass("tbody-dark");
    $("#loginForm").toggleClass("border-dark border-white");
    $("#average-container").toggleClass("average-container average-container-dark");
    $("#total-amount").toggleClass("dark-mode total-amount-txt");
    $("#win-amount").toggleClass("dark-mode win-amount-txt");
    $("#total-amount-total").toggleClass("dark-mode total-amount-txt");
    $("#win-amount-total").toggleClass("dark-mode win-amount-txt");
} 

function changeTheme(state) {
    if (state == 1) {
        $("body").addClass("dark-mode");
        $("a").addClass("dark-mode");
        $("div").addClass("dark-mode");
        $("p").addClass("dark-mode");
        $("span").addClass("dark-mode");
        $("select").addClass("select-dark-mode");
        $("table").addClass("dark-mode");
        $("#gameTh").addClass("thead-dark");
        $("#gameTd").addClass("tbody-dark");
        $("#stake").addClass("dark-mode");
        $("#total-amount").addClass("dark-mode").removeClass("total-amount-txt");
        $("#win-amount").addClass("dark-mode").removeClass("win-amount-txt");
        $("#total-amount-total").addClass("dark-mode").removeClass("total-amount-txt");
        $("#win-amount-total").addClass("dark-mode").removeClass("win-amount-txt");
        $("#loginForm").addClass("border-white").removeClass("border-dark");
        $("#average-container").addClass("average-container-dark").removeClass("average-container");
        $(".div-container").addClass("div-container-dark").removeClass("div-container");
        $(".home_label").addClass("home_label-dark").removeClass("home_label");
        $(".nav").addClass("nav-dark").removeClass("nav");
    } else {
        $("body").removeClass("dark-mode");
        $("a").removeClass("dark-mode");
        $("div").removeClass("dark-mode");
        $("p").removeClass("dark-mode");
        $("span").removeClass("dark-mode");
        $("select").removeClass("select-dark-mode");
        $("table").removeClass("dark-mode");
        $("#gameTh").removeClass("thead-dark");
        $("#gameTd").removeClass("tbody-dark");
        $("#stake").removeClass("dark-mode");
        $("#total-amount").addClass("total-amount-txt").removeClass("dark-mode");
        $("#win-amount").addClass("win-amount-txt").removeClass("dark-mode");
        $("#total-amount-total").addClass("total-amount-txt").removeClass("dark-mode");
        $("#win-amount-total").addClass("win-amount-txt").removeClass("dark-mode");
        $("#loginForm").addClass("border-dark").removeClass("border-white");
        $("#average-container").addClass("average-container").removeClass("average-container-dark");
        $(".div-container-dark").addClass("div-container").removeClass("div-container-dark");
        $(".home_label-dark").addClass("home_label").removeClass("home_label-dark");
        $(".nav-dark").addClass("nav").removeClass("nav-dark");
    }
}