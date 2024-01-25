import requests, json, os, decimal, time

class Main():

    def __init__(self):
        
        self.node = 'https://api.mainnet-beta.solana.com'

        if not os.path.exists('./mainnet.json'):
            print("Downloading Raydium pool data...")
            req = requests.get('https://api.raydium.io/v2/sdk/liquidity/mainnet.json')
            with open('./mainnet.json', 'w') as file:
                file.write(json.dumps(req.json()['unOfficial']))
                file.close()
        with open('./mainnet.json', 'r') as file:
            self.data = json.load(file)
        pass
    
    def get_token_reserves(self, contract_address):
        for reserve in self.data:
            if reserve['baseMint'] == contract_address:
                return reserve['quoteVault']
            elif reserve['quoteMint'] == contract_address:
                return reserve['baseVault']
                
    def get_sol_reserve_balance(self, contract_address):
        headers = {"Content-Type": "application/json"}
        reserve = self.get_token_reserves(contract_address)
        data = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "getBalance",
            "params": [f"{reserve}"]
        }
        res = requests.post(self.node, headers=headers, json=data)
        reserve = res.json()['result']['value']
        return decimal.Decimal((reserve / decimal.Decimal(1e9)))
    
    def get_token_reserve_balance(self, contract_address):
        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "getTokenAccountsByOwner",
            "params": [
                "5Q544fKrFoe6tsEbD7S8EmxGTJYAKtTVhAW5Q5pge4j1",
                {
                    "mint": contract_address
                },
                {
                    "encoding": "jsonParsed"
                }
            ]
        }
        res = requests.post(self.node, headers=headers, json=data)
        return decimal.Decimal(res.json()['result']['value'][0]['account']['data']['parsed']['info']['tokenAmount']['uiAmount'])
    
    def get_sol_price(self):
        res = requests.get('https://api.dexscreener.com/latest/dex/pairs/solana/b6ll9acwvuo1ttcjoyvctdqyrq1vjmfci8uhxsm4uxtr').json()
        return decimal.Decimal(res['pairs'][0]['priceNative'])
    
    def get_token_supply(self, contract_address):
        headers = {"Content-Type": "application/json"}
        data = {
            "jsonrpc": "2.0",
            "id": 0,
            "method": "getTokenSupply",
            "params": [
                contract_address
            ]
        }
        res = requests.post(self.node, headers=headers, json=data).json()
        return decimal.Decimal(res['result']['value']['uiAmount'])
    
    def get_token_name(self, contract_address):
        res = requests.get(f'https://api.dexscreener.com/latest/dex/tokens/{contract_address}').json()
        return res['pairs'][0]['baseToken']['name']
    
    def one_token_price_usd(self, contract_address):
        token = self.get_token_reserve_balance(contract_address)
        soltoken = self.get_sol_reserve_balance(contract_address)
        solprice = self.get_sol_price()
        return decimal.Decimal(f'{(soltoken/token*solprice):.8f}')
    
    def market_cap(self, contract_address):
        token_supply = self.get_token_supply(contract_address)
        one_token_price = self.one_token_price_usd(contract_address)
        return(token_supply * one_token_price)

                
    def run(self, contract_address):
        market_cap_value = self.market_cap(contract_address)
        get_token_name = self.get_token_name(contract_address)
        print(f" Name: {get_token_name} | Market Cap: {market_cap_value:.2f} USD", end='\r', flush=True)
        time.sleep(10) ## 10 sec refresh interval

if __name__ == "__main__":
    token = input("Token address:")
    while True:
        try:
            Main().run(token)
        except KeyboardInterrupt:
            print("\nTerminating the process.")
            break
        except:
            pass
