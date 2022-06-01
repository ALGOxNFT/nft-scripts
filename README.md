# nft-scripts
Short tools for Algorand NFT management


### Pre-requisites

- Install pipenv (see resources)


## Running Bulk Send

0. Set `send_wallet_mnemonic` and `receive_wallet_mnemonic` in the `src/bulk_send.py` file with your own 25 words
1. Run `pipenv install` to install the dependencies
2. Run `pipenv shell` to active the pipenv environment
3. Run `python src/bulk_send.py` to run the script


## Running Bulk Opt-out

0. Set `wallet_mnemonic` in the `src/bulk_opt_out.py` file with your own 25 words
1. Run `pipenv install` to install the dependencies
2. Run `pipenv shell` to active the pipenv environment
3. Run `python src/bulk_opt_out.py` to run the script


# Running bulk deletion

0. Set `creator_wallet_mnemonic` in the `src/bulk_asset_destroy.py` file with your own 25 words
1. Run `pipenv install` to install the dependencies
2. Run `pipenv shell` to active the pipenv environment
3. Run `python src/bulk_asset_destroy.py` to run the script


## Running Airdrop (not tested for multi-mints)

0. Set `wallet_mnemonic` in the `src/bulk_opt_out.py` file with your own 25 words
1. Update the various configurations
   1. CREATOR_WALLET_ADDRESS
   2. NFT_PREFIX
   3. DAYS_HELD
   4. AIRDROP_ASSET_ID
   5. AIRDROP_AMOUNT
   6. AIRDROP_BLACKLIST
2. Run `pipenv install` to install the dependencies
3. Run `pipenv shell` to active the pipenv environment
4. Run `python src/airdrop.py` to run the script


### Resources

- https://pipenv.pypa.io/en/latest/install/
- https://pipenv-fork.readthedocs.io/en/latest/basics.html
