from algosdk import account, mnemonic
from algosdk.v2client import indexer, algod
from algosdk.future import transaction

#
# Replace the `send_wallet_mnemonic` and `receive_wallet_mnemonic` with your own 25 word passphrase
#
# Run this file with the following command `python bulk_send.py`
#

send_wallet_mnemonic = ""
receive_wallet_mnemonic = ""

send_wallet_mnemonic_clean = send_wallet_mnemonic.replace(",", "")
send_wallet_pk = mnemonic.to_private_key(send_wallet_mnemonic_clean)
send_wallet_address = account.address_from_private_key(send_wallet_pk)

receive_wallet_mnemonic_clean = receive_wallet_mnemonic.replace(",", "")
receive_wallet_pk = mnemonic.to_private_key(receive_wallet_mnemonic_clean)
receive_wallet_address = account.address_from_private_key(receive_wallet_pk)


MAINNET_NODE_API = "https://mainnet-api.algonode.cloud"
MAINNET_INDEXER_API = "https://mainnet-idx.algonode.cloud"

TESTNET_NODE_API = "https://testnet-api.algonode.cloud"
TESTNET_INDEXER_API = "https://testnet-idx.algonode.cloud"


def find_nfts_in_wallet(indexer_client):
    print(f"\nSearching for non-zero NFTs in the sending wallet {send_wallet_address}...")

    asa_ids = []
    next_token = None

    try:
        while True:
            payload = indexer_client.lookup_account_assets(send_wallet_address, next_page=next_token)
            assets = payload.get('assets')

            for nft in assets:
                if nft.get('amount', 0) > 0:
                    asa_ids.append(nft.get('asset-id'))

            next_token = payload.get('next-token', None)
            if next_token is None:
                break

            print(".")

    except Exception as err:
        print(err)

    print("\nFound the following ASA IDs")
    print(asa_ids)
    print(f"\nWe will send {len(asa_ids)} NFTs from this wallet")

    return asa_ids


def opt_into_nfts(node_client, asset_ids):
    print(f"\nBeginning the opt-in process on {receive_wallet_address}...")

    params = node_client.suggested_params()
    params.flat_fee = True
    params.fee = 1000

    for n, asa_id in enumerate(asset_ids):
        print(f"{n}: asset opt-in {asa_id}")

        try:
            send_txn = transaction.AssetOptInTxn(sender=receive_wallet_address,
                                                 sp=params,
                                                 index=asa_id)

            signed_txn = send_txn.sign(receive_wallet_pk)
            node_client.send_transactions([signed_txn])

        except Exception as err:
            print(err)


def send_nfts(node_client, asset_ids):
    print(f"\nBeginning the sending process from {send_wallet_address} to {receive_wallet_address}...")

    params = node_client.suggested_params()
    params.flat_fee = True
    params.fee = 1000

    for n, asa_id in enumerate(asset_ids):
        try:
            print(f"{n}: asset transfer {asa_id}")

            send_txn = transaction.AssetTransferTxn(sender=send_wallet_address,
                                                    sp=params,
                                                    receiver=receive_wallet_address,
                                                    amt=1,
                                                    index=asa_id)

            signed_txn = send_txn.sign(send_wallet_pk)
            node_client.send_transactions([signed_txn])

        except Exception as err:
            print(err)


def user_will_continue(msg):
    print(msg)
    user_input = input().lower()
    return user_input == "y"


def run_bulk_send(indexer_client, node_client):
    print(f"Send wallet: {send_wallet_address}")
    print(f"Receive wallet: {receive_wallet_address}")

    if not user_will_continue("Are the send and receive wallet addresses correct? [y/N]"):
        print("Bulk send cancelled")
        return

    print("\nProceeding with bulk_send...")

    asset_ids = find_nfts_in_wallet(idx_client)

    if not user_will_continue("Are these the NFTs you want to send? [y/N]"):
        print("Bulk send cancelled")
        return

    print("\nProceeding with bulk_send...")

    opt_into_nfts(node_client, asset_ids)
    send_nfts(node_client, asset_ids)


if __name__ == "__main__":

    idx_client = indexer.IndexerClient(indexer_token="",
                                       indexer_address=MAINNET_INDEXER_API)
    node_client = algod.AlgodClient(algod_token="",
                                    algod_address=MAINNET_NODE_API)

    run_bulk_send(idx_client, node_client)
