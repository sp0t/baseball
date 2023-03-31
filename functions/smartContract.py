from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://polygon-rpc.com'))
chainId = 137
contractAddress = "0x2dE282dAfa9F92b7066387FAEde44EEe7D07B1E6"
abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"betDic","outputs":[{"internalType":"string","name":"betdate","type":"string"},{"internalType":"string","name":"game","type":"string"},{"internalType":"string","name":"teams","type":"string"},{"internalType":"string","name":"market","type":"string"},{"internalType":"string","name":"place","type":"string"},{"internalType":"string","name":"stake","type":"string"},{"internalType":"string","name":"odds","type":"string"},{"internalType":"string","name":"profitloss","type":"string"},{"internalType":"string","name":"status","type":"string"},{"internalType":"string","name":"site","type":"string"},{"internalType":"uint256","name":"createdAt","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"betIndex","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"betRatio","outputs":[{"internalType":"uint256","name":"betcount","type":"uint256"},{"internalType":"uint256","name":"wincount","type":"uint256"},{"internalType":"uint256","name":"losecount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_betId","type":"uint256"},{"internalType":"string","name":"_status","type":"string"}],"name":"changeBetstatus","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"_betDate","type":"string"},{"internalType":"string","name":"_game","type":"string"},{"internalType":"string","name":"_teams","type":"string"},{"internalType":"string","name":"_market","type":"string"},{"internalType":"string","name":"_place","type":"string"},{"internalType":"string","name":"_stake","type":"string"},{"internalType":"string","name":"_odds","type":"string"},{"internalType":"string","name":"_profitloss","type":"string"},{"internalType":"string","name":"_status","type":"string"},{"internalType":"string","name":"_site","type":"string"}],"name":"createBetData","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
public_key = "0xf0a487CB71E4D79D6f9D0Ad3fe8e5Fcd45dab55D"
private_key = "a9f80db9607f931c9df074124f79adba541ddfb8d8634262039d365e7a4f5550"
deployed_contract = w3.eth.contract(address=contractAddress, abi=abi)

data = {'betdate':'1', 'game':'1', 'team1':'1', 'team2':'2', 'market':'1', 'place':'1', 'stake':'1', 'odds':'1', 'wins':'1', 'site':'1'}

def betIndex():
  betindex = deployed_contract.functions.betIndex().call()
  print(betindex)
  return betindex

def createBetData(betData):
  _betDate = betData["betdate"]
  _game = betData["game"].lower()
  if(betData["team1"] == betData["team2"]):
    global _teams
    _teams = betData["team1"]
  else:
    _teams = betData["team1"] + " vs " + betData["team2"]

  _market = betData["market"]
  _place = betData["place"]
  _stake = str(betData["stake"])
  _odds = betData["odds"]
  _profitloss = str(betData["wins"])

  _status = "PENDING"
  _site = betData["site"]

  add_tx = deployed_contract.functions.createBetData(_betDate, _game, _teams, _market, _place, _stake, _odds, _profitloss, _status, _site)
  nonce = w3.eth.get_transaction_count(public_key)
  gasprice = w3.eth.gas_price
  add_tx = add_tx.buildTransaction({'from': public_key, 'chainId': chainId, 'gasPrice': gasprice, 'nonce': nonce})
  tx_create = w3.eth.account.sign_transaction(add_tx, private_key)
  txn_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
  w3.eth.wait_for_transaction_receipt(txn_hash)
  
  return

def changeBetStatus(betID, status):
  betid = int(betID)
  add_tx = deployed_contract.functions.changeBetstatus(betid, status)
  nonce = w3.eth.get_transaction_count(public_key)
  gasprice = w3.eth.gas_price
  add_tx = add_tx.buildTransaction({'from': public_key, 'chainId': chainId, 'gasPrice': gasprice, 'nonce': nonce})
  tx_create = w3.eth.account.sign_transaction(add_tx, private_key)
  txn_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
  w3.eth.wait_for_transaction_receipt(txn_hash)

  return