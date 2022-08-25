from scripts.get_weth import get_weth
from scripts.helpful_scripts import get_account
from brownie import network, config, interface
from web3 import Web3

AMOUNT = Web3.toWei(0.1, "ether")


def main():
    account = get_account()
    # Get the address of the asset
    erc20_address = config["networks"][network.show_active()]["weth_token"]
    if network.show_active() in ["mainnet-fork"]:
        # call get_weth() function just incase we don't have WETH
        get_weth()
    # ABI
    # Address

    lending_pool = get_lending_pool()
    # Deposit - first, we need to approve ERC20 to use our token - this is standard protocol
    approve_erc20(AMOUNT, lending_pool.address, erc20_address, account)
    print("Depositing ETH...")
    tx = lending_pool.deposit(
        erc20_address, AMOUNT, account.address, 0, {"from": account}
    )
    tx.wait(1)
    print("Deposited!")

    # ...how much can we borrow and not get liquidated? Let us pull our stats

    borrowable_eth, total_debt = get_borrowable_data(lending_pool, account)

    print("Let's borrow!")
    # Get DAI in terms of ETH
    dai_to_eth_price = get_asset_price(
        config["networks"][network.show_active()]["dai_eth_price_feed_address"]
    )

    amount_of_dai_to_borrow = (1 / dai_to_eth_price) * (borrowable_eth * 0.95)
    print(f"We are going to borrow {amount_of_dai_to_borrow} DAI")

    # Now we will borrow

    dai_address = config["networks"][network.show_active()]["dai_token"]
    borrow_tx = lending_pool.borrow(
        dai_address,
        Web3.toWei(amount_of_dai_to_borrow, "ether"),
        1,
        0,
        account.address,
        {"from": account},
    )
    borrow_tx.wait(1)
    print("We borrowed some DAI!")
    get_borrowable_data(lending_pool, account)
    # repay_all(AMOUNT, lending_pool, account)

    print("You just deposited, borrowed and repaid with AAVE, Brownie and Chainlink!")


def repay_all(amount, lending_pool, account):
    approve_erc20(
        Web3.toWei(amount, "ether"),
        lending_pool,
        config["networks"][network.show_active()]["dai_token"],
        account,
    )

    repay_tx = lending_pool.repay(
        config["networks"][network.show_active()]["dai_token"],
        amount,
        1,
        account.address,
        {"from": account},
    )

    repay_tx.wait(1)
    print("Repaid!")


def get_asset_price(price_feed_address):
    dai_eth_price_feed = interface.AggregatorV3Interface(price_feed_address)
    latest_price = dai_eth_price_feed.latestRoundData()[1]
    converted_price = Web3.fromWei(latest_price, "ether")
    print(f"The DAI/ETH price is {converted_price}")

    return float(converted_price)


def get_borrowable_data(lending_pool, account):
    (
        totalCollateralETH,
        totalDebtETH,
        availableBorrowsETH,
        currentLiquidationThreshold,
        ltv,
        healthFactor,
    ) = lending_pool.getUserAccountData(account.address)

    totalCollateralETH = Web3.fromWei(totalCollateralETH, "ether")
    totalDebtETH = Web3.fromWei(totalDebtETH, "ether")
    availableBorrowsETH = Web3.fromWei(availableBorrowsETH, "ether")

    print(f"You have {totalCollateralETH} worth of ETH deposited.")
    print(f"You have {totalDebtETH} worth of ETH borrowed.")
    print(f"You can borrow {availableBorrowsETH} worth of ETH.")

    return (float(availableBorrowsETH), float(totalDebtETH))


def approve_erc20(amount, spender, erc20_address, account):
    print("Approving ERCToken...")
    erc20 = interface.IERC20(erc20_address)
    tx = erc20.approve(spender, amount, {"from": account})
    tx.wait(1)
    print("Approved!")

    return tx


def get_lending_pool():
    # ABI
    # Address - Check!
    lending_pool_address_provider = interface.ILendingPoolAddressesProvider(
        config["networks"][network.show_active()]["lending_pool_address"]
    )
    lending_pool_address = lending_pool_address_provider.getLendingPool()
    lending_pool = interface.ILendingPool(lending_pool_address)

    return lending_pool
