import json
from web3 import Web3
import os
from dotenv import load_dotenv

load_dotenv()

w3 = Web3(Web3.HTTPProvider('https://base-mainnet.g.alchemy.com/v2/USbVaOTSKlqazrRw7rjg2'))

# Aave V3 Pool
POOL_ADDR = '0xA238Dd80C259a72e81d7e4664a9801593F98d1c5'
# Borrow event signature
BORROW_SIG = '0xb53027b4096d2f3db98a883a48e89f899e32a67a0ee9d34e64f9f25a98bf793c'

def get_liquidatable_users(blocks=1000):
    current = w3.eth.block_number
    print(f'Scanning last {blocks} blocks for Aave Borrows...')
    
    logs = w3.eth.get_logs({
        'fromBlock': current - blocks,
        'toBlock': current,
        'address': POOL_ADDR,
        'topics': [BORROW_SIG]
    })
    
    users = set()
    for log in logs:
        # User is in topic 2
        user = '0x' + log['topics'][2].hex()[-40:]
        users.add(Web3.to_checksum_address(user))
        
    print(f'Found {len(users)} active borrowers. Checking Health Factors...')
    
    pool_abi = [{'inputs':[{'name':'user','type':'address'}],'name':'getUserAccountData','outputs':[{'name':'','type':'uint256'},{'name':'','type':'uint256'},{'name':'','type':'uint256'},{'name':'','type':'uint256'},{'name':'','type':'uint256'},{'name':'healthFactor','type':'uint256'}],'type':'function'}]
    pool = w3.eth.contract(address=POOL_ADDR, abi=pool_abi)
    
    targets = []
    for user in users:
        data = pool.functions.getUserAccountData(user).call()
        hf = data[5] / 1e18
        if hf < 1.1: # Threshold to watch
            print(f'🔥 WATCHING: {user} | HF: {hf:.4f}')
            if hf < 1.0:
                print('  ⭐ LIQUIDATABLE! ⭐')
                targets.append(user)
    
    if not targets:
        print('No one liquidatable right now. Market is Healthy.')

if __name__ == '__main__':
    get_liquidatable_users(5000)
