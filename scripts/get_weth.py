from brownie import interface, config, network
from web3 import Web3
from scripts.helpful_scripts import get_account


def main():
    get_weth()


def get_weth():

    """
    Mints WETH by depositing ETH to the WETHGETWAY contract
    """

    account = get_account()
    weth = interface.IWeth(config["networks"][network.show_active()]["weth_token"])
    print("Depositing some ETH...")
    tx = weth.deposit({"from": account, "value": Web3.toWei(0.1, "ether")})
    tx.wait(1)
    print("Successfully swapped some ETH for WETH!")

    return tx
