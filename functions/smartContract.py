from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://rpc-mumbai.maticvigil.com'))
chainId = 80001
contractAddress = "0x8199353E0C8F28eD4229CA5C305164eb1557EA5A"
abi = '[{"inputs":[],"stateMutability":"nonpayable","type":"constructor"},{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"betDic","outputs":[{"internalType":"string","name":"betdate","type":"string"},{"internalType":"string","name":"game","type":"string"},{"internalType":"string","name":"teams","type":"string"},{"internalType":"string","name":"market","type":"string"},{"internalType":"string","name":"place","type":"string"},{"internalType":"string","name":"stake","type":"string"},{"internalType":"string","name":"odds","type":"string"},{"internalType":"string","name":"profitloss","type":"string"},{"internalType":"string","name":"status","type":"string"},{"internalType":"string","name":"site","type":"string"},{"internalType":"uint256","name":"createdAt","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"betIndex","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[],"name":"betRatio","outputs":[{"internalType":"uint256","name":"betcount","type":"uint256"},{"internalType":"uint256","name":"wincount","type":"uint256"},{"internalType":"uint256","name":"losecount","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_betId","type":"uint256"},{"internalType":"string","name":"_status","type":"string"}],"name":"changeBetstatus","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"string","name":"_betDate","type":"string"},{"internalType":"string","name":"_game","type":"string"},{"internalType":"string","name":"_teams","type":"string"},{"internalType":"string","name":"_market","type":"string"},{"internalType":"string","name":"_place","type":"string"},{"internalType":"string","name":"_stake","type":"string"},{"internalType":"string","name":"_odds","type":"string"},{"internalType":"string","name":"_profitloss","type":"string"},{"internalType":"string","name":"_status","type":"string"},{"internalType":"string","name":"_site","type":"string"}],"name":"createBetData","outputs":[],"stateMutability":"nonpayable","type":"function"}]'
public_key = "0x56a2FD1875eD5B43B3f60DfB1B9087Ca11268509"
private_key = "7c9fc9d0fe048f58b03d49a277af17e92279c40f6fb172e4820ea508cd144ce9"
deployed_contract = w3.eth.contract(address=contractAddress, abi=abi)
betIndex = deployed_contract.functions.betIndex().call()

def createBetData(betData):
  _betDate = betData["gamedate"]
  _game = betData["game"].lower()
  if(betData["team1"] == betData["team2"]):
    global _teams
    _teams = betData["team1"]
  else:
    _teams = betData["team1"] + " vs " + betData["team2"]

  _market = betData["market"]
  _place = betData["place"]
  _stake = betData["stake"]
  _odds = betData["odds"]
  _profitloss = betData["wins"]

  _status = "PENDING"
  _site = betData["site"]

  add_tx = deployed_contract.functions.createBetData(_betDate, _game, _teams, _market, _place, _stake, _odds, _profitloss, _status, _site)
  nonce = w3.eth.getTransactionCount(public_key)
  gasprice = w3.eth.gas_price
  add_tx = add_tx.buildTransaction({'from': public_key, 'chainId': chainId, 'gasPrice': gasprice, 'nonce': nonce})
  tx_create = w3.eth.account.sign_transaction(add_tx, private_key)
  txn_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
  return

def changeBetStatus(betID, status):
  betid = int(betID)
  add_tx = deployed_contract.functions.changeBetstatus(betid, status)
  nonce = w3.eth.getTransactionCount(public_key)
  gasprice = w3.eth.gas_price
  add_tx = add_tx.buildTransaction({'from': public_key, 'chainId': chainId, 'gasPrice': gasprice, 'nonce': nonce})
  tx_create = w3.eth.account.sign_transaction(add_tx, private_key)
  txn_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
  return