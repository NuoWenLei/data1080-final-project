import requests
import json

base_url = "https://paper-api.alpaca.markets"

version = "v2"

with open("secrets/secrets.json", "r") as secrets_json:
	secrets = json.load(secrets_json)

all_secrets = {}

all_secrets["top_model"] = secrets

def overhaul_portfolio(symbols, weights = None, secret_version = "top_model"):
	print(symbols)

	failed_sells = sell_all(secret_version = secret_version)

	print(failed_sells)

	unavailable_equity = 0
	if len(failed_sells) > 0:
		for p in failed_sells:
			unavailable_equity += float(p["qty"]) * float(p["current_price"])

	print(unavailable_equity)

	failed_buys, failed_reasons = buy_stocks(symbols, weights, unavailable_equity = unavailable_equity, secret_version = secret_version)

	print(failed_buys)

	return failed_buys, failed_reasons

def get_account_info(secret_version = "top_model"):

	endpoint = base_url + "/" + version + "/account"

	headers = all_secrets[secret_version]

	r = requests.get(endpoint, headers = headers)

	return json.loads(r.text)

def sell_all(secret_version = "top_model"):
	positions = get_all_positions(secret_version=secret_version)

	failed = []
	causes = []

	for p in positions:
		res = order(p["symbol"], str(p["qty_available"]), "sell", by_value = False, secret_version = secret_version)
		if res != "success!!!":
			failed.append(p)
			causes.append(res)
	
	if len(failed) > 0:
		print("Following stocks failed to sell")
		print([p["symbol"] for p in failed])
		print("Due to")
		print(causes)

	return failed

def buy_stocks(symbols, weights = None, unavailable_equity = 0, secret_version = "top_model"):
	account_info = get_account_info(secret_version=secret_version)

	equity = float(account_info["equity"]) - unavailable_equity

	stock_notional_pair = []

	if weights:
		assert len(symbols) == len(weights), "Number of weights does not match number of symbols"
		weights_sum = sum(weights)
		for s, w in zip(symbols, weights):
			stock_notional_pair.append([s, int(equity * w / weights_sum)])
	else:
		num_symbols = len(symbols)
		for s in symbols:
			stock_notional_pair.append([s, int(equity / num_symbols)])
	
	failed = []
	causes = []

	for symbol, value in stock_notional_pair:
		res = order(symbol, str(value), "buy", by_value = True, secret_version = secret_version)
		if res != "success!!!":
			failed.append(symbol)
			causes.append(res)
	
	if len(failed) > 0:
		print("Following stocks failed to buy")
		print(failed)
		print("Due to")
		print(causes)

	return failed, causes

def get_all_positions(secret_version = "top_model"):
	endpoint = base_url + "/" + version + "/positions"

	headers = all_secrets[secret_version]

	r = requests.get(endpoint, headers = headers)

	return json.loads(r.text)

def get_history(period = "1W", date_end = None, timeframe = "1D", secret_version = "top_model", extended_hours = False):
	endpoint = base_url + "/" + version + "/account/portfolio/history"
	
	headers = all_secrets[secret_version]

	params = {
		"period": period,
		"timeframe": timeframe,
		"extended_hours": extended_hours
	}

	if date_end:
		params["date_end"] = date_end

	r = requests.get(endpoint, headers = headers, params = params)

	return json.loads(r.text)

def delete_all_orders(secret_version):
	endpoint = base_url + "/" + version + "/orders"

	headers = all_secrets[secret_version]

	r = requests.delete(endpoint, headers = headers)

	return json.loads(r.text)

def order(
	quote: str,
	value: str,
	side: str,
	type_: str = "market",
	time_in_force: str = "day",
	by_value: bool = True,
	secret_version: str = "top_model"
):
	endpoint = base_url + "/" + version + "/orders"

	headers = all_secrets[secret_version]

	params = {
		"symbol": quote.upper(),
		"side": side.lower(),
		"type": type_,
		"time_in_force": time_in_force
		}

	if by_value:
		params["notional"] = value
	else:
		params["qty"] = value

	r = requests.post(endpoint, data = json.dumps(params), headers = headers)

	if r.status_code == 200:
		return "success!!!"
	else:
		return r.text