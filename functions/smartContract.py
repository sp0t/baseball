from web3 import Web3

w3 = Web3(Web3.HTTPProvider('https://rpc-mumbai.maticvigil.com'))
chainId = 80001
contractAddress = "0x0DfDcA862dB4730feF06a6f08bABf95547777653"
abi = '[{"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"betDic","outputs":[{"internalType":"string","name":"betdate","type":"string"},{"internalType":"string","name":"game","type":"string"},{"internalType":"string","name":"teams","type":"string"},{"internalType":"string","name":"market","type":"string"},{"internalType":"string","name":"place","type":"string"},{"internalType":"uint256","name":"stake","type":"uint256"},{"internalType":"uint256","name":"odds","type":"uint256"},{"internalType":"uint256","name":"profitloss","type":"uint256"},{"internalType":"string","name":"status","type":"string"},{"internalType":"string","name":"site","type":"string"},{"internalType":"uint256","name":"createdAt","type":"uint256"}],"stateMutability":"view","type":"function"},{"inputs":[{"internalType":"uint256","name":"_betId","type":"uint256"},{"internalType":"string","name":"_status","type":"string"}],"name":"changeBetstatus","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[{"internalType":"uint256","name":"_betId","type":"uint256"},{"internalType":"string","name":"_betDate","type":"string"},{"internalType":"string","name":"_game","type":"string"},{"internalType":"string","name":"_teams","type":"string"},{"internalType":"string","name":"_market","type":"string"},{"internalType":"string","name":"_place","type":"string"},{"internalType":"uint256","name":"_stake","type":"uint256"},{"internalType":"uint256","name":"_odds","type":"uint256"},{"internalType":"uint256","name":"_profitloss","type":"uint256"},{"internalType":"string","name":"_status","type":"string"},{"internalType":"string","name":"_site","type":"string"}],"name":"createBetData","outputs":[],"stateMutability":"nonpayable","type":"function"},{"inputs":[],"name":"decimals","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"}]'
public_key = "0x56a2FD1875eD5B43B3f60DfB1B9087Ca11268509"
private_key = "7c9fc9d0fe048f58b03d49a277af17e92279c40f6fb172e4820ea508cd144ce9"
deployed_contract = w3.eth.contract(address=contractAddress, abi=abi)
decimals = deployed_contract.functions.decimals().call()

def createBetData(betID, betData):
  _betId = int(betID)
  _betDate = betData["gamedate"]
  _game = betData["game"].lower()
  if(betData["team1"] == betData["team2"]):
    global _teams
    _teams = betData["team1"]
  else:
    _teams = betData["team1"] + " vs " + betData["team2"]

  _market = betData["market"]
  _place = betData["place"]
  _stake = int(float(betData["stake"]) * 100)
  _odds = int(float(betData["odds"]) * 100)
  _profitloss = int(float(betData["wins"]) * 100)
  _status = "PENDING"
  _site = betData["site"]

  print("1")
  add_tx = deployed_contract.functions.createBetData( _betId, _betDate, _game, _teams, _market, _place, _stake, _odds, _profitloss, _status, _site)
  print("2")
  nonce = w3.eth.getTransactionCount(public_key)
  print("3")
  gasprice = w3.eth.gas_price
  print("4")
  add_tx = add_tx.buildTransaction({'from': public_key, 'chainId': chainId, 'gasPrice': gasprice, 'nonce': nonce})
  print("5")
  tx_create = w3.eth.account.sign_transaction(add_tx, private_key)
  txn_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
  print("txn_hash1", txn_hash)
  return

def changeBetStatus(betID, status):
  betid = int(betID)
  add_tx = deployed_contract.functions.changeBetstatus(betid, status)
  nonce = w3.eth.getTransactionCount(public_key)
  gasprice = w3.eth.gas_price
  add_tx = add_tx.buildTransaction({'from': public_key, 'chainId': chainId, 'gasPrice': gasprice, 'nonce': nonce})
  tx_create = w3.eth.account.sign_transaction(add_tx, private_key)
  txn_hash = w3.eth.sendRawTransaction(tx_create.rawTransaction)
  print("txn_hash1", txn_hash)
  return