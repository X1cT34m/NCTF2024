from flask import Flask, render_template, request, jsonify
import requests
from web3 import Web3
from eth_account.hdaccount import generate_mnemonic
from eth_account import Account
import deploy
import time
import json
import os

app = Flask(__name__)
deployer_account = None
player_account = None
tx_receipt = None
answer = None
web3 = None


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/button-click', methods=['POST'])
def handle_button_click():
    data = request.json
    button_id = data.get('button_id')
    global deployer_account, tx_receipt, answer, web3, player_account

    if button_id == 'launch':
        mnemonic = generate_mnemonic(12, "english")
        anvil_process = deploy.start_anvil(mnemonic)
        time.sleep(2)
        web3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))
        if not web3.is_connected():
            raise Exception("not connected")

        deployer_account = Account.from_mnemonic(
            mnemonic, account_path=f"m/44'/60'/0'/0/0"
        )

        player_account = Account.from_mnemonic(
            mnemonic, account_path=f"m/44'/60'/0'/0/1"
        )

        web3.provider.make_request(
            "anvil_setBalance",
            [player_account.address, web3.to_wei(1, "ether")]
        )

        result = f"""
Deployer Account: {deployer_account.address}
Player private key: 0x{player_account._private_key.hex()}
Player Account: {player_account.address}
"""
    elif button_id == 'new round':
        answer = os.urandom(32)

        tx_receipt = deploy.new_guess_game_round(
            answer, deployer_account._private_key.hex(), web3)
        result = f"""
challenge contract has been deployed at {tx_receipt.contractAddress}
you can submit your answer in one minute
"""

    elif button_id == 'check winner':
        winner = deploy.check_winner(
            answer, deployer_account._private_key.hex(), tx_receipt, web3)
        if winner == deployer_account.address:
            result = "no winner this round"
        else:
            result = f"""winner of this round is {winner}
"""

    elif button_id == 'get flag':
        if web3.eth.get_balance(player_account.address) > web3.to_wei(10, "ether"):
            result = open("/flag").read()
        else:
            result = "your balance is not enough"
    else:
        result = "error"

    return jsonify({"result": result})


@app.route('/rpc', methods=['POST'])
def rpc_proxy():
    anvil_url = "http://localhost:8545"
    try:
        m = request.get_json()['method'].lower()
        if ('anvil' in m or 'ots' in m or 'unsigned' in m):
            return jsonify({"error": "no"}), 500
        response = requests.post(
            anvil_url,
            json=request.get_json(),
            headers={'Content-Type': 'application/json'}
        )
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({
            "error": f"无法连接到Anvil节点: {str(e)}"
        }), 500


if __name__ == '__main__':
    app.run()
