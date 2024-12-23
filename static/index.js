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

    const awaypriceInput = document.getElementById('awayprice');
    awaypriceInput.addEventListener('input', function () {
        let value = awaypriceInput.value;
        if (value.startsWith('+') || value.startsWith('-')) {
            value = value.substring(1);
        }

        if (value !== '') {
            awaypriceInput.value = awaypriceInput.value.startsWith('-') ? `-${value}` : `+${value}`;
        }
    })

    const homepriceInput = document.getElementById('homeprice');
    homepriceInput.addEventListener('input', function () {
        let value = homepriceInput.value;
        if (value.startsWith('+') || value.startsWith('-')) {
            value = value.substring(1);
        }

        if (value !== '') {
            homepriceInput.value = homepriceInput.value.startsWith('-') ? `-${value}` : `+${value}`;
        }
    })

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
            teams.innerHTML = '';

            var newOption = document.createElement('option');
            newOption.value = ''; 
            newOption.innerHTML = '-';
            newOption.style.fontSize = '15px';
            newOption.style.padding = '3px';
            teams.append(newOption);

            var awayOption = document.createElement('option');
            awayOption.value = data['away']; 
            awayOption.innerHTML = data['away'];
            awayOption.style.fontSize = '15px';
            awayOption.style.padding = '3px';
            if(data['away'] == data['place'])
                awayOption.setAttribute('selected', true);

            teams.append(awayOption);

            var homeOption = document.createElement('option');
            homeOption.value = data['home']; 
            homeOption.innerHTML = data['home'];
            homeOption.style.fontSize = '15px';
            homeOption.style.padding = '3px';

            if(data['home'] == data['place'])
                homeOption.setAttribute('selected', true);

            teams.append(homeOption);

            var sites = document.getElementById('sites'); 
            sites.innerHTML = '';

            var newOption = document.createElement('option');
            newOption.value = ''; 
            newOption.innerHTML = '-';
            newOption.style.fontSize = '15px';
            newOption.style.padding = '3px';
            sites.append(newOption);

            for (var i = 0; i<data['site_list'].length; i++) {
                newOption = document.createElement('option');
                newOption.value = data['site_list'][i]; 
                newOption.innerHTML = data['site_list'][i];
                newOption.style.fontSize = '15px';
                newOption.style.padding = '3px';
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

function openNHLBetModal(gameid){ 
    data = {}
    data['gameid'] = gameid
    data['site'] = 'NOSITE'
    $.ajax({
        type: 'POST', 
        url: '/get_NHL_bet_info', 
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
            $('#priceform').hide();
            $('#betform').show();
            $("#modal_game_id").val(gameid);

            var betdate = document.getElementById('betdate');
            betdate.innerHTML = data['date'];

            var away = document.getElementById('awayname');
            away.value = data['away'];

            var home = document.getElementById('homename');
            home.value = data['home'];

            var teams = document.getElementById('teams'); 
            teams.innerHTML = '';

            var newOption = document.createElement('option');
            newOption.value = ''; 
            newOption.innerHTML = '-';
            newOption.style.fontSize = '15px';
            newOption.style.padding = '3px';
            teams.append(newOption);

            var awayOption = document.createElement('option');
            awayOption.value = data['away']; 
            awayOption.innerHTML = data['away'];
            awayOption.style.fontSize = '15px';
            awayOption.style.padding = '3px';
            if(data['away'] == data['place'])
                awayOption.setAttribute('selected', true);

            teams.append(awayOption);

            var homeOption = document.createElement('option');
            homeOption.value = data['home']; 
            homeOption.innerHTML = data['home'];
            homeOption.style.fontSize = '15px';
            homeOption.style.padding = '3px';

            if(data['home'] == data['place'])
                homeOption.setAttribute('selected', true);

            teams.append(homeOption);

            var market = document.getElementById('market'); 
            market.innerHTML = '';

            var newOption = document.createElement('option');
            newOption.value = ''; 
            newOption.innerHTML = '-';
            newOption.style.fontSize = '15px';
            newOption.style.padding = '3px';
            market.append(newOption);

            var otOption = document.createElement('option');
            otOption.value = "OT"; 
            otOption.innerHTML = "OT";
            otOption.style.fontSize = '15px';
            otOption.style.padding = '3px';
            if(data['market'] == "OT")
                otOption.setAttribute('selected', true);

            market.append(otOption);

            var sites = document.getElementById('sites'); 
            sites.innerHTML = '';

            var newOption = document.createElement('option');
            newOption.value = ''; 
            newOption.innerHTML = '-';
            newOption.style.fontSize = '15px';
            newOption.style.padding = '3px';
            sites.append(newOption);

            for (var i = 0; i<data['site_list'].length; i++) {
                newOption = document.createElement('option');
                newOption.value = data['site_list'][i]; 
                newOption.innerHTML = data['site_list'][i];
                newOption.style.fontSize = '15px';
                newOption.style.padding = '3px';
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

function openPriceModal(gameid){ 
    document.getElementById('modal_game_id').value = gameid;
    $('.large-card').css('width', '350px').css('height', '260px').show();
    $('#large-card-wrapper').show();
    $('#betform').hide();
    $('#priceform').show();
}


function changeBetSite(site) {
    var gameid = $("#modal_game_id").val();

    data = {}
    data['gameid'] = gameid
    data['site'] = site

    $.ajax({
        type: 'POST', 
        url: '/get_NHL_bet_info', 
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

function closeCard(value = 0){ 
    
    var allOptions = document.querySelectorAll('.option');
    allOptions.forEach(option => {
        option.remove();
    });

    var selectElement = document.getElementById('teams');
    var options = selectElement.querySelectorAll('option');

    options.forEach(option => {
        option.remove();
    });

    if(value != 1) {
        selectElement = document.getElementById('sites');
        var options = selectElement.querySelectorAll('option');
    
        options.forEach(option => {
            option.remove();
        });
    }

    if(value == 1) {
        $('#betid-rec').val(0);
    }

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
    var site = '';
    var betid = 0;
    if(value == 2 || value == 3) { 
        site = document.getElementById('sites-rec').value;
        betid = document.getElementById('betid-rec').value;
    }
    else {
        site = document.getElementById('sites').value;
    }

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
    data['betid'] = betid;

    console.log(data)

    $.ajax({
        type: 'POST', 
        url: '/betting', 
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        beforeSend: function(){ 
        },
        success: function (data){ 
            if(value == 2 || value == 3) {
                closeCard(1);
                var data={};
                data["startdate"] = $("#startdateInput").val();
                data["enddate"] = $("#enddateInput").val();
                data["betsite"] = $("#betsite").val();
            } else {
                closeCard(0);
            }
        }
    })
}


function updateNHLBetInformation(value) {
    var data = {};
    var betdate = document.getElementById('betdate').textContent;
    var away = document.getElementById('awayname').value;
    var home = document.getElementById('homename').value;
    var place = document.getElementById('teams').value;
    var market = document.getElementById('market').value;
    var odds = document.getElementById('oddvalue').value;
    var stake = document.getElementById('stakevalue').value;
    var wins = document.getElementById('winvalue').value;
    var site = '';
    var betid = 0;
    if(value == 2 || value == 3) { 
        site = document.getElementById('sites-rec').value;
        betid = document.getElementById('betid-rec').value;
    }
    else {
        site = document.getElementById('sites').value;
    }

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

    if (market == '') {
        alert('Please select market!');
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
    data['market'] = market;
    data['odds'] = odds;
    data['stake'] = stake;
    data['wins'] = wins;
    data['flag'] = value;
    data['site'] = site;
    data['betid'] = betid;

    console.log(data)

    $.ajax({
        type: 'POST', 
        url: '/NHL_betting', 
        data: JSON.stringify(data),
        dataType: 'json',
        contentType: 'application/json',
        beforeSend: function(){ 
        },
        success: function (data){ 
            if(value == 2 || value == 3) {
                closeNHLCard(1);
                var data={};
                data["startdate"] = $("#startdateInput").val();
                data["enddate"] = $("#enddateInput").val();
                data["betsite"] = $("#betsite").val();
            } else {
                closeNHLCard(0);
            }
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

    away_dec_odd = (1.05 / (awayProbValue / 100)).toFixed(2)
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

    home_dec_odd = (1.05 / (homeProbValue / 100)).toFixed(2)
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
            console.log(data)
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
        
    } else {
        localStorage.setItem("darkMode", "enabled");
    }

    $("body").toggleClass("dark-mode");
} 

function changeTheme(state) {
    if (state == 1) {
        $("body").addClass("dark-mode");
    } else {
        $("body").removeClass("dark-mode");
    }
}

function openBetForm(element) {
    var data = element.getAttribute('data-betstate');
    var betDetails = JSON.parse(data);
    console.log(betDetails);
    $('.large-card').css('width', '350px').css('height', '430px').show();
    $('#large-card-wrapper').show();
    $('#betform').show();

    var betdate = document.getElementById('betdate');
    betdate.innerHTML = betDetails['betdate'];

    var away = document.getElementById('awayname');
    away.value = betDetails['team1'];

    var home = document.getElementById('homename');
    home.value = betDetails['team2'];

    var teams = document.getElementById('teams'); 

    var newOption = document.createElement('option');
    newOption.value = ''; 
    newOption.innerHTML = '-';
    newOption.style.fontSize = '15px';
    newOption.style.padding = '3px';
    teams.append(newOption);

    var awayOption = document.createElement('option');
    awayOption.value = betDetails['team1']; 
    awayOption.innerHTML = betDetails['team1'];
    awayOption.style.fontSize = '15px';
    awayOption.style.padding = '3px';

    if(betDetails['team1'] == betDetails['place'])
        awayOption.setAttribute('selected', true);

    teams.append(awayOption);

    var homeOption = document.createElement('option');
    homeOption.value = betDetails['team2']; 
    homeOption.innerHTML = betDetails['team2'];
    homeOption.style.fontSize = '15px';
    homeOption.style.padding = '3px';

    if(betDetails['team2'] == betDetails['place'])
        homeOption.setAttribute('selected', true);

    teams.append(homeOption);

    var sites = document.getElementById('sites-rec'); 
    sites.value = betDetails['site'];

    var oddvalue = document.getElementById('oddvalue');
    oddvalue.value = betDetails['odds'];

    var stakevalue = document.getElementById('stakevalue');
    stakevalue.value = betDetails['stake'];

    var winvalue = document.getElementById('winvalue');
    winvalue.value = betDetails['wins'];

    document.getElementById('betid-rec').value = betDetails['betid'];
}

//************* NHL functions *********************

function  getNHLPlayerStats(id){
    var param = {'game_id' : id}
    $.ajax({
        type: 'POST', 
        url: '/getNHLPlayerStats',
        data: { 'data' : JSON.stringify(param)},
        beforeSend: function(){ 
            console.log('before sending');
        },
        success: function (data){ 
            console.log(data)
            var html = '';
                const divContainer = document.getElementById(id);
                const divContent = document.getElementById(`stats_${id}`);
        
                const topPosition = divContainer.offsetTop;
                const height = divContainer.offsetHeight;
                const bottomPosition = topPosition + height;

                divContent.style.top = `${bottomPosition}px`;
                divContent.style.left = '160px';
                divContent.style.width = `${window.innerWidth - 165 * 2}px`;

                if(data.skater != undefined && data.skater.length > 0) {
                    html += '<div class="skater-container">'
                    html += '<div style="background-color:black">GID</div>'
                    html += '<div style="background-color:black">PID</div>'
                    html += '<div style="background-color:black">TEAM</div>'
                    html += '<div style="background-color:black">GAMES</div>'
                    html += '<div style="background-color:black">WG</div>'
                    html += '<div style="background-color:black">WA</div>'
                    html += '<div style="background-color:black">WP</div>'
                    html += '<div style="background-color:black">WPM</div>'
                    html += '<div style="background-color:black">WPeM</div>'
                    html += '<div style="background-color:black">WTOI</div>'
                    html += '<div style="background-color:black">WCF</div>'
                    html += '<div style="background-color:black">WCA</div>'
                    html += '<div style="background-color:black">WFP</div>'
                    html += '<div style="background-color:black">WFPr</div>'
                    html += '<div style="background-color:black">RG</div>'
                    html += '<div style="background-color:black">RA</div>'
                    html += '<div style="background-color:black">RP</div>'
                    html += '<div style="background-color:black">RPM</div>'
                    html += '<div style="background-color:black">RPeM</div>'
                    html += '<div style="background-color:black">RTOI</div>'
                    html += '<div style="background-color:black">RCF</div>'
                    html += '<div style="background-color:black">RCA</div>'
                    html += '<div style="background-color:black">RFP</div>'
                    html += '<div style="background-color:black">RFPr</div>'
                    

                    for(var x in data.skater) {
                        html += `<div>${data.skater[x].game_id}</div>`
                        html += `<div>${data.skater[x].player_id}</div>`
                        html += `<div>${data.skater[x].plays_for_home_team == 0 ? 'AWAY': 'HOME'}</div>`
                        html += `<div>${data.skater[x].total_games}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_goals).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_assists).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_points).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_plus_minus).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_penalty_minutes).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_time_on_ice).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_corsi_for).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_corsi_against).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_fenwick_for_percent).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].weighted_average_fenwick_for_percent_relative).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_goals).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_assists).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_points).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_plus_minus).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_penalty_minutes).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_time_on_ice).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_corsi_for).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_corsi_against).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_fenwick_for_percent).toFixed(2)}</div>`
                        html += `<div>${Number(data.skater[x].recent_form_fenwick_for_percent_relative).toFixed(2)}</div>`
                    }
                    html += '</div>';
                }

                if(data.goaltender != undefined && data.goaltender.length > 0) {
                    html += '<div class="goaltender-container">'
                    html += '<div style="background-color:black">GID</div>'
                    html += '<div style="background-color:black">PID</div>'
                    html += '<div style="background-color:black">TEAM</div>'
                    html += '<div style="background-color:black">GAMES</div>'
                    html += '<div style="background-color:black">WPeM</div>'
                    html += '<div style="background-color:black">WTOI</div>'
                    html += '<div style="background-color:black">WSP</div>'
                    html += '<div style="background-color:black">WGA</div>'
                    html += '<div style="background-color:black">RPM</div>'
                    html += '<div style="background-color:black">RTOI</div>'
                    html += '<div style="background-color:black">RSP</div>'
                    html += '<div style="background-color:black">RGA</div>'
                    

                    for(var y in data.goaltender) {
                        html += `<div>${data.goaltender[y].game_id}</div>`
                        html += `<div>${data.goaltender[y].player_id}</div>`
                        html += `<div>${data.goaltender[y].plays_for_home_team == 0 ? 'AWAY': 'HOME'}</div>`
                        html += `<div>${data.goaltender[y].total_games}</div>`
                        html += `<div>${Number(data.goaltender[y].weighted_average_penalty_minutes).toFixed(2)}</div>`
                        html += `<div>${Number(data.goaltender[y].weighted_average_time_on_ice).toFixed(2)}</div>`
                        html += `<div>${Number(data.goaltender[y].weighted_average_save_percentage).toFixed(2)}</div>`
                        html += `<div>${Number(data.goaltender[y].weighted_average_goals_against).toFixed(2)}</div>`
                        html += `<div>${Number(data.goaltender[y].recent_form_penalty_minutes).toFixed(2)}</div>`
                        html += `<div>${Number(data.goaltender[y].recent_form_time_on_ice).toFixed(2)}</div>`
                        html += `<div>${Number(data.goaltender[y].recent_form_save_percentage).toFixed(2)}</div>`
                        html += `<div>${Number(data.goaltender[y].recent_form_goals_against).toFixed(2)}</div>`
                    }
                    html += '</div>'
                }
              divContent.innerHTML = html;
        },
        error: function() {
        }
    })
}

function switchSite(flag) {
    $.ajax({
        type: 'POST', 
        url: '/switchSite', 
        data: {
            'flag' : flag == 0 ? 'MLB': 'NHL',
        },
        beforeSend: function(){ 
            $('#loader').show(); 
        },
        success: function (data){
            $('#loader').hide(); 
            window.location.reload(true);
         }, 
    })
}

function closeNHLCard(value = 0){ 
    $('.large-card').hide(); 
}


function saveRequestPrice(value = 0){ 
    var awayprice = document.getElementById('awayprice').value ? document.getElementById('awayprice').value : 0;
    var homeprice = document.getElementById('homeprice').value ? document.getElementById('homeprice').value : 0;
    var gameid = document.getElementById('modal_game_id').value;
    var bet = document.getElementById('auto_bet').checked ? 1: 0;
    var stake = document.getElementById('stake_size').value;

    
    data = {}
    data['gameid'] = gameid;
    data['awayprice'] = awayprice;
    data['homeprice'] = homeprice;
    data['bet'] = bet;
    data['site'] = 'NHL';
    data['stake'] = stake;
    
    console.log(data);
    $.ajax({
        type: 'POST', 
        url: '/price_request', 
        data: { 'data' : JSON.stringify(data)},
        beforeSend: function(){
            $('#large-card-wrapper').hide();
            $('#loader').show();
        }, 
        success: function (data){
            $('#loader').hide(); 
            $('#large-card-wrapper').show();
         }, 
    });
    $('.large-card').hide(); 
}
