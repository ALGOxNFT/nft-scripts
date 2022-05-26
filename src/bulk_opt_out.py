from algosdk import account, mnemonic
from algosdk.v2client import indexer, algod
from algosdk.future import transaction

#
# Replace the `wallet_mnemonic` with your own 25 word passphrase
#
# Run this file with the following command `python bulk_opt_out.py`
#

wallet_mnemonic = ""

wallet_mnemonic_clean = wallet_mnemonic.replace(",", "")
wallet_pk = mnemonic.to_private_key(wallet_mnemonic_clean)
wallet_address = account.address_from_private_key(wallet_pk)

MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"

TESTNET_NODE_API = "https://testnet-api.algonode.cloud"
TESTNET_INDEXER_API = "https://testnet-idx.algonode.cloud"


def find_nfts_in_wallet(indexer_client):
    print(f"\nSearching for empty NFTs in the wallet {wallet_address}...")

    asa_ids = []
    next_token = None

    try:
        while True:
            payload = indexer_client.lookup_account_assets(wallet_address, next_page=next_token)
            assets = payload.get('assets')

            for nft in assets:
                if nft.get('amount') == 0:
                    asa_ids.append(nft.get('asset-id'))

            next_token = payload.get('next-token', None)
            if next_token is None:
                break

            print(".")

    except Exception as err:
        print(err)

    print("\nFound the following ASA IDs")
    print(asa_ids)
    print(f"\nWe will opt-out of {len(asa_ids)} NFTs from this wallet")

    return asa_ids


def opt_out_of_nfts(node_client, asset_ids):
    print(f"\nBeginning the opt-out process on {wallet_address}...")

    params = node_client.suggested_params()
    params.flat_fee = True
    params.fee = 1000

    for n, asa_id in enumerate(asset_ids):
        print(f"{n}: asset opt-out {asa_id}")

        try:
            opt_out_txn = transaction.AssetCloseOutTxn(sender=wallet_address,
                                                       sp=params,
                                                       receiver=wallet_address,
                                                       index=asa_id)

            signed_txn = opt_out_txn.sign(wallet_pk)
            node_client.send_transactions([signed_txn])

        except Exception as err:
            print(err)


def user_will_continue(msg):
    print(msg)
    user_input = input().lower()
    return user_input == "y"


def run_bulk_opt_out(indexer_client, node_client):
    print(f"Beginning the bulk opt-out process on {wallet_address}")

    if not user_will_continue(f"Ready to clean {wallet_address}? [y/N]"):
        print("Bulk opt-out cancelled")
        return

    print("\nProceeding with bulk opt_out...")

    asset_ids = find_nfts_in_wallet(indexer_client)

    if not user_will_continue("Are these the NFTs you want to opt-out of? [y/N]"):
        print("Bulk opt-out cancelled")
        return

    print("\nProceeding with bulk opt_out...")

    opt_out_of_nfts(node_client, asset_ids)


if __name__ == "__main__":

    idx_client = indexer.IndexerClient(indexer_token="",
                                       indexer_address=MAINNET_INDEXER_API)
    algod_client = algod.AlgodClient(algod_token="",
                                    algod_address=MAINNET_NODE_API)

    run_bulk_opt_out(idx_client, algod_client)
