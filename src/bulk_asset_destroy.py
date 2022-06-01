from algosdk import account, mnemonic
from algosdk.v2client import indexer, algod
from algosdk.future import transaction

# Run this file with the following command `python bulk_asset_destroy.py`
#
# Replace the `creator_wallet_mnemonic` with your own 25 word passphrase
#
# Optionally, add ASA IDs to the SKIPLIST and/or a PREFIX to filter by
#
# For example, if I had two collections in my wallet, unit names (goan, mngo)
# I would set the PREFIX = 'goan' if I ONLY wanted to delete the Al Goannas
#


creator_wallet_mnemonic = ""  # FILL-IN
PREFIX = ""  # NOTE:
SKIPLIST_ASA_IDS = []  # NOTE: Optional list of ASA IDs to skip - EX: [410618415,600330685]

creator_wallet_mnemonic_clean = creator_wallet_mnemonic.replace(",", "")
creator_wallet_pk = mnemonic.to_private_key(creator_wallet_mnemonic_clean)
creator_wallet_address = account.address_from_private_key(creator_wallet_pk)


MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"

TESTNET_NODE_API = "https://testnet-api.algonode.cloud"
TESTNET_INDEXER_API = "https://testnet-idx.algonode.cloud"


def find_nfts_in_wallet(indexer_client):
    print(f"\nSearching for created NFTs in the wallet {creator_wallet_address}...")

    created_assets = []
    next_token = None

    try:
        while True:
            payload = indexer_client.lookup_account_asset_by_creator(creator_wallet_address, next_page=next_token)
            assets = payload.get('assets')

            for asset in assets:
                asset_id = asset.get('index')
                params = asset.get('params')
                unit_name = params.get('unit-name')

                if asset_id in SKIPLIST_ASA_IDS or (len(PREFIX) and not unit_name.startswith(PREFIX)):
                    continue

                if asset.get('index'):
                    created_assets.append(asset)

            next_token = payload.get('next-token', None)
            if next_token is None:
                break

            print(".")

    except Exception as err:
        print(err)

    print(f"\nFound {len(created_assets)} NFTs")

    for asset in created_assets:
        params = asset.get('params')
        print(f"{asset.get('index')} - {params.get('unit-name')} - {params.get('name')}")

    print(f"\nWe will destroy {len(created_assets)} NFTs from this wallet")

    return created_assets


def bulk_asset_destroy(node_client, created_assets):
    print(f"\nBeginning the asset destroy from the creator wallet {creator_wallet_address}...")

    params = node_client.suggested_params()
    params.flat_fee = True
    params.fee = 1000

    for n, asa in enumerate(created_assets):
        try:
            asset_id = asa.get('index')
            print(f"{n}: asset destroy of asa id {asset_id}")

            send_txn = transaction.AssetDestroyTxn(sender=creator_wallet_address,
                                                   sp=params,
                                                   index=asset_id)

            signed_txn = send_txn.sign(creator_wallet_pk)
            node_client.send_transactions([signed_txn])

        except Exception as err:
            print(err)

    print("\nDone with the bulk asset deletion")


def user_will_continue(msg):
    print(msg)
    user_input = input().lower()
    return user_input == "y"


def run_bulk_asset_destroy(indexer_client, node_client):
    print(f"Asset Destroy wallet: {creator_wallet_address}")

    if not user_will_continue("Is this the wallet where we will delete/destroy created NFTs? [y/N]"):
        print("Bulk asset destroy cancelled")
        return

    print("\nProceeding with bulk asset destroy...")

    created_assets = find_nfts_in_wallet(indexer_client)

    if len(created_assets) == 0:
        return

    if not user_will_continue("Are these the NFTs you want to destroy? [y/N]"):
        print("Bulk destroy cancelled")
        return

    print("\nProceeding with bulk_destroy...")

    bulk_asset_destroy(node_client, created_assets)


if __name__ == "__main__":

    idx_client = indexer.IndexerClient(indexer_token="",
                                       indexer_address=MAINNET_INDEXER_API)
    algod_client = algod.AlgodClient(algod_token="",
                                     algod_address=MAINNET_NODE_API)

    run_bulk_asset_destroy(idx_client, algod_client)
