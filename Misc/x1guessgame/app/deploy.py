import json
import subprocess
from eth_account import Account

Account.enable_unaudited_hdwallet_features()


def start_anvil(mnemonic):
    command = [
        'anvil',
        '--host', '0.0.0.0',
        '--disable-console-log',
        '--silent',
        '--accounts', '2',
        '--mnemonic', mnemonic,
        '-b', '5',
    ]

    try:
        with open('/dev/null', 'w') as devnull:
            process = subprocess.Popen(command, stdout=devnull, stderr=devnull)

        return process
    except Exception as e:
        print(f"Failed to start Anvil: {e}")


def new_guess_game_round(answer, deploy_private_key, web3):
    contract_abi = json.loads(
        open('./contracts/Challenge.abi').read())

    contract_bytecode = open(
        './contracts/Challenge.bin').read()

    deploy_address = web3.eth.account.from_key(deploy_private_key).address

    Contract = web3.eth.contract(abi=contract_abi, bytecode=contract_bytecode)

    answer_hash = web3.keccak(answer)

    construct_txn = Contract.constructor(answer_hash).build_transaction({
        'from': deploy_address,
        'nonce': web3.eth.get_transaction_count(deploy_address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('21', 'gwei'),
        'value': web3.to_wei('10', 'ether')
    })

    signed_txn = web3.eth.account.sign_transaction(
        construct_txn, private_key=deploy_private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)
    return tx_receipt


def check_winner(answer, deploy_private_key, tx_receipt, web3):
    contract_abi = json.loads(
        open('./contracts/Challenge.abi').read())
    challenge_contract = web3.eth.contract(
        tx_receipt.contractAddress, abi=contract_abi)
    deploy_address = web3.eth.account.from_key(deploy_private_key).address

    claim_txn = challenge_contract.functions.claim(answer).build_transaction({
        'from': deploy_address,
        'nonce': web3.eth.get_transaction_count(deploy_address),
        'gas': 2000000,
        'gasPrice': web3.to_wei('21', 'gwei')
    })

    signed_txn = web3.eth.account.sign_transaction(
        claim_txn, private_key=deploy_private_key)

    tx_hash = web3.eth.send_raw_transaction(signed_txn.rawTransaction)

    tx_receipt = web3.eth.wait_for_transaction_receipt(tx_hash)

    is_claimed_after_claim = challenge_contract.functions.isClaimed().call()
    winner = challenge_contract.functions.winner().call()
    if is_claimed_after_claim:
        return winner
    else:
        raise Exception("error")
