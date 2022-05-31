import datetime

from algosdk import account, mnemonic
from algosdk.v2client import indexer, algod
from algosdk.future import transaction
from pprint import pprint

########################################################################################################################
# Hello, this is a a simple airdrop script
# To begin, feel free to change any of these values to suit your needs
#
# NOTE: Proceed with caution, NOT tested for multi-mints
#

# Hodl NFT Configuration
CREATOR_WALLET_ADDRESS = ""  # NOTE: FILL-IN
NFT_PREFIX = ""   # NOTE: FILL-IN or leave empty EXAMPLE ('goan' for Al Goanna collection)
DAYS_HELD = 7  # NOTE: FILL-IN

# Airdrop
AIRDROP_ASSET_ID = 0  # NOTE: FILL-IN  EXAMPLE (DEGEN TOKEN = 417708610)
AIRDROP_AMOUNT = 0  # NOTE: FILL-IN  TIP: Use 0 amount first to do a sanity check

# Airdrop wallet configuration
AIRDROP_SENDER_WALLET_MNEMONIC = ""  # NOTE: FILL-IN
AIRDROP_SENDER_WALLET_MNEMONIC_CLEAN = AIRDROP_SENDER_WALLET_MNEMONIC.replace(",", "")
AIRDROP_SENDER_WALLET_PK = mnemonic.to_private_key(AIRDROP_SENDER_WALLET_MNEMONIC_CLEAN)
AIRDROP_SENDER_WALLET = account.address_from_private_key(AIRDROP_SENDER_WALLET_PK)


# BLACKLIST may include creator wallet, known escrows, etc
AIRDROP_BLACKLIST = []  # NOTE: FILL-IN (optional)  EXAMPLE ["FA4WWPRQGSQSYPKMPYNTEZZTH5ITQO3AJJYB66MUEIA5TSP4MGHT27PXYQ"]


########################################################################################################################


MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"

TESTNET_NODE_API = "https://testnet-api.algonode.cloud"
TESTNET_INDEXER_API = "https://testnet-idx.algonode.cloud"


def fetch_created_nfts(indexer_client, creator, prefix):
    print(f"Fetching all of the created NFTs for {creator} with prefix {prefix}...")

    created_nfts = []
    next_token = None

    try:
        while True:
            payload = indexer_client.lookup_account_asset_by_creator(creator, next_page=next_token)
            created_nfts = created_nfts + payload.get('assets')

            next_token = payload.get('next-token', None)
            if next_token is None:
                break

            print(".")

    except Exception as e:
        print(e)

    print(f"Found {len(created_nfts)} NFTs from the creator wallet: {creator}")
    print(f"Filtering this list of NFTs by the following prefix {prefix}")

    filtered_nfts = []
    for nft in created_nfts:
        params = nft.get('params')
        unit_name = params.get('unit-name')

        if len(prefix) > 0 and unit_name.startswith(prefix):
            filtered_nfts.append(nft)

    print(f"Filtered out {len(created_nfts) - len(filtered_nfts)} and {len(filtered_nfts)} NFTs remain")

    return filtered_nfts


def get_holders(indexer_client, assets):
    print(f"Finding all of the current holders for the {len(assets)} NFTs...")
    all_holders = []

    for index, asset in enumerate(assets):
        asset_id = asset.get('index')
        next_token = None
        asset_holders = []

        while True:
            try:
                payload = indexer_client.asset_balances(asset_id, next_page=next_token)
                any_balance = payload.get('balances')

                holders_with_nonzero_balance = list(filter(lambda x: x.get('amount', 0) > 0, any_balance))
                asset_holders = asset_holders + holders_with_nonzero_balance

                next_token = payload.get('next-token', None)
                if next_token is None:
                    break

            except Exception as e:
                print(e)

        print(f"{index}: Found {len(asset_holders)} holder of {asset_id}")

        asset_to_balances = {
            asset_id: asset_holders
        }
        all_holders.append(asset_to_balances)

    pprint(all_holders)
    print("Finished finding all holders...")

    return all_holders


def filter_holders(indexer_client, asset_to_holders_list):
    print(f"Filtering holders by hodl duration of {DAYS_HELD} days")

    wagmi_holders = []
    minimum_hold_length = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=DAYS_HELD)

    for asset_to_holders in asset_to_holders_list:

        for asset_id, wallet_info_list in asset_to_holders.items():

            for wallet_info in wallet_info_list:
                wallet_address = wallet_info.get('address')

                if wallet_address in AIRDROP_BLACKLIST:
                    print(f"Skipping {wallet_address}")
                    continue

                payload = indexer_client.search_asset_transactions(asset_id,
                                                                   address=wallet_address,
                                                                   start_time=minimum_hold_length.isoformat())
                txns_within_timeframe = payload.get('transactions')

                if len(txns_within_timeframe) == 0:
                    # Wallet has a positive balance and has not made any asset transfers in the last N days

                    print(f"WGMI {wallet_address}")
                    wagmi_holders.append(wallet_address)
                else:
                    is_gmi = True

                    for txn in txns_within_timeframe:
                        # Checking transactions to see if holder sent to someone else
                        # and ensuring at least 1 of the NFT was sent

                        sender = txn.get('sender')
                        asset_transfer_txn = txn.get('asset-transfer-transaction')
                        receiver = asset_transfer_txn.get('receiver')
                        amount = asset_transfer_txn.get('amount')

                        if sender == wallet_address and receiver != wallet_address and amount > 0:
                            is_gmi = False
                            break

                    if is_gmi:
                        print(f"WGMI {wallet_address}")
                        wagmi_holders.append(wallet_address)
                    else:
                        print(f"---- {wallet_address}")

    print("\n")
    pprint(wagmi_holders)
    print(f"Found {len(wagmi_holders)} valid holders with minimum holding period of {DAYS_HELD} days")

    return wagmi_holders


def user_will_continue(msg):
    print(msg)
    user_input = input().lower()
    return user_input == "y"


def perform_airdrop(node_client, valid_holder_wallets):
    print(f"Preparing for airdrop to {len(valid_holder_wallets)} holders...")

    params = node_client.suggested_params()
    params.flat_fee = True
    params.fee = 1000

    for index, holder_wallet in enumerate(valid_holder_wallets):

        try:
            print(f"Sending {AIRDROP_AMOUNT} of {AIRDROP_ASSET_ID} to {holder_wallet}...")

            # NOTE: Avoiding 'transaction already in ledger' error when a holder holds multiple of an NFT
            simple_nonce = str.encode(f"send {index}")

            airdrop_txn = transaction.AssetTransferTxn(AIRDROP_SENDER_WALLET,
                                                       params,
                                                       receiver=holder_wallet,
                                                       amt=AIRDROP_AMOUNT,
                                                       index=AIRDROP_ASSET_ID,
                                                       note=simple_nonce)
            txn_id = airdrop_txn.get_txid()
            signed_txn = airdrop_txn.sign(AIRDROP_SENDER_WALLET_PK)
            node_client.send_transactions([signed_txn])

            print(f"Sent to {holder_wallet} with txn_id {txn_id}!")

        except Exception as e:
            print(f"Failed to send to {holder_wallet}")
            print(e)


def run_airdrop(indexer_client, node_client):
    print("Beginning the airdrop process...\n")

    print(f"Airdrop wallet: {AIRDROP_SENDER_WALLET}")
    print(f"Minimum required days to hold NFT: {DAYS_HELD}")
    print(f"Holding NFTs from the creator wallet: {CREATOR_WALLET_ADDRESS}\n")

    if not user_will_continue(f"Verify the above data is correct. Ready to begin airdrop? [y/N]"):
        print("Airdrop cancelled")
        return

    print("\nProceeding with airdrop...\n")

    all_created_nfts = fetch_created_nfts(indexer_client, CREATOR_WALLET_ADDRESS, prefix=NFT_PREFIX)

    if not user_will_continue(f"\nReady to get the holders list? [y/N]"):
        print("Airdrop cancelled")
        return

    print("\nProceeding with airdrop...\n")

    asset_to_holders_list = get_holders(indexer_client, all_created_nfts)

    if not user_will_continue("\nDoes this holder list look good? [y/N]"):
        print("Airdrop cancelled")
        return

    print("\nProceeding with airdrop...\n")

    all_valid_holders = filter_holders(indexer_client, asset_to_holders_list)

    if not user_will_continue(f"\nFiltered down holders to those holding the NFTs for at least {DAYS_HELD} days...\n"
                              f"\nAre you ready for the airdrop? [y/N]"):
        print("Airdrop cancelled")
        return

    print("\nProceeding with airdrop...\n")

    perform_airdrop(node_client, all_valid_holders)

    print("All finished! Good job on the airdrop :)")


if __name__ == "__main__":
    idx_client = indexer.IndexerClient(indexer_token="", indexer_address=MAINNET_INDEXER_API)
    algod_client = algod.AlgodClient(algod_token="", algod_address=MAINNET_NODE_API)

    run_airdrop(idx_client, algod_client)
