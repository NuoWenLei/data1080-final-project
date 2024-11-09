from tqdm import tqdm
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import yfinance as yf
import json
import pandas as pd
import numpy as np
import requests
import datetime

def get_tickers():
	with open("tickers/tickers.json", "r") as tickers_json:
		tickers = json.load(tickers_json)
	return tickers

def process_camel_name_to_readable(name: str) -> str:
	newName = ""
	prevLetter = ""
	for c in name:
		if c.isnumeric():
			if prevLetter.isnumeric():
				newName += c
			else:
				newName += " " + c
		elif c.isupper() and len(newName) > 0:
			newName += " " + c.lower()
		else:
			newName += c
		prevLetter = c
	return newName

def get_first_numbers(s: str | None):
	if type(s) != str:
		return None
	numbers = ""
	for c in s:
		if c.isnumeric():
			numbers += c
		else:
			break
	if len(numbers) == 0:
		return None
	return float(numbers)

def get_ticker_info(symbol: str):
	metadataAttributes = [
		"industry",
		"sector",
		"country",
	]
	numericAttributes = ['auditRisk', 'boardRisk', 'compensationRisk', 'shareHolderRightsRisk',
											'overallRisk', 'priceHint', 'previousClose', 'open', 'dayLow', 'dayHigh', 'regularMarketPreviousClose',
											'regularMarketOpen', 'regularMarketDayLow', 'regularMarketDayHigh', 'dividendRate', 'dividendYield',
											'payoutRatio', 'fiveYearAvgDividendYield', 'beta', 'trailingPE', 'forwardPE',
											'volume', 'regularMarketVolume', 'averageVolume', 'averageVolume10days', 'averageDailyVolume10Day',
											'bid', 'ask', 'bidSize', 'askSize', 'marketCap', 'fiftyTwoWeekLow', 'fiftyTwoWeekHigh', 'priceToSalesTrailing12Months',
											'fiftyDayAverage', 'twoHundredDayAverage', 'trailingAnnualDividendRate', 'trailingAnnualDividendYield',
											'enterpriseValue', 'profitMargins', 'floatShares', 'sharesOutstanding', 'sharesShort',
											'sharesShortPriorMonth', 'sharesShortPreviousMonthDate', 'dateShortInterest', 'sharesPercentSharesOut',
											'heldPercentInsiders', 'heldPercentInstitutions', 'shortRatio', 'shortPercentOfFloat', 'impliedSharesOutstanding',
											'bookValue', 'priceToBook', 'earningsQuarterlyGrowth', 'netIncomeToCommon', 'trailingEps', 'forwardEps',
											'pegRatio', 'lastSplitFactor', 'lastSplitDate', 'enterpriseToRevenue', 'enterpriseToEbitda', '52WeekChange',
											'SAndP52WeekChange', 'lastDividendValue', 'lastDividendDate', 
											'currentPrice', 'targetHighPrice', 'targetLowPrice', 'targetMeanPrice',
											'targetMedianPrice', 'totalCash',
											'totalCashPerShare', 'ebitda', 'totalDebt', 'quickRatio', 'currentRatio', 'totalRevenue', 'debtToEquity',
											'revenuePerShare', 'returnOnAssets', 'returnOnEquity', 'freeCashflow', 'operatingCashflow', 'earningsGrowth',
											'revenueGrowth', 'grossMargins', 'ebitdaMargins', 'operatingMargins', 'financialCurrency', 'trailingPegRatio']
	ticker = yf.Ticker(symbol)
	tickerInfo = ticker.info
	tickerNumerics = dict()
	tickerMetadata = dict()
	for metadataAttr in metadataAttributes:
		tickerMetadata[process_camel_name_to_readable(metadataAttr)] = tickerInfo[metadataAttr]
	
	for numericAttr in numericAttributes:
		try:
			tickerNumerics[process_camel_name_to_readable(numericAttr)] = float(tickerInfo[numericAttr])
		except KeyError as e:
			tickerNumerics[process_camel_name_to_readable(numericAttr)] = None
		except Exception as e:
			tickerNumerics[process_camel_name_to_readable(numericAttr)] = get_first_numbers(tickerInfo[numericAttr])
	
	return tickerMetadata, tickerNumerics

def collect_deloitte():
	def collect_webpage(url):
		r = requests.get(url)
		soup = BeautifulSoup(r.text, "html.parser")
		elements = soup.find(class_="responsivegrid content-width-di-sm aem-GridColumn aem-GridColumn--default--8").find_all(["h1", "h2", "h3", "li", "p"])
		html_str = "".join([str(e) for e in elements])
		return md(html_str, strip=["a"])
	year = datetime.datetime.now().year
	prevMonth = datetime.datetime.now().month - 1
	prevUrl = f"https://www2.deloitte.com/us/en/insights/economy/global-economic-outlook/weekly-update/weekly-update-{year}-{prevMonth}.html"
	currUrl = "https://www2.deloitte.com/us/en/insights/economy/global-economic-outlook/weekly-update.html"
	docs = []
	for url in [prevUrl, currUrl]:
		try:
			docs.append(collect_webpage(url))
		except Exception as e:
			pass
	return docs
	

def collect_news():
	documents = []

	# Deloitte covers global trends
	deloitte_docs = collect_deloitte()
	documents.extend(deloitte_docs)

	for i, doc in enumerate(documents):
		with open(f"input/markdown/markdown_{i}.md", "w") as md_txt:
			md_txt.write(doc)


def collect_ticker_data():
	tickers = get_tickers()
	metadatas = []
	numerics = []
	symbols = []
	for ticker in tqdm(tickers):
		try:
			symbol = ticker["symbol"]
			m, n = get_ticker_info(symbol)
			m["name"] = ticker["name"]
			m["symbol"] = symbol
			metadatas.append(m)
			numerics.append(n)
			symbols.append(symbol)
		except Exception as e:
			print(ticker["symbol"])
			print(e)

	with open("tickers/rawTickerMetadata.json", "w") as metadata_json:
		json.dump(metadatas, metadata_json)
	with open("tickers/rawTickerNumerics.json", "w") as numerics_json:
		json.dump(numerics, numerics_json)
	
	numeric_df, meta_df, weighable_attributes = clean_attributes(numerics, metadatas, symbols)

	numeric_df.to_csv("tickers/tickers_numerics.csv")
	meta_df.to_csv("tickers/tickers_metadata.csv")

	with open("tickers/weighable_attributes.json", "w") as attr_json:
		json.dump(weighable_attributes.tolist(), attr_json)
		
def clean_attributes(numerics, metadata, symbols) -> tuple[pd.DataFrame, pd.DataFrame, np.ndarray]:
	numeric_df = pd.DataFrame(numerics, index = symbols)
	numeric_df[numeric_df == np.inf] = np.nan
	numeric_df[numeric_df == -np.inf] = np.nan

	attribute_nan_pct = numeric_df.isna().sum(axis = 0) / numeric_df.shape[0]
	attrs_to_drop = attribute_nan_pct[attribute_nan_pct > .5].index.values
	numeric_df = numeric_df.drop(attrs_to_drop, axis = 1)

	rank_df = pd.DataFrame([], index = numeric_df.index)
	for col in numeric_df.columns:
		rank_df[col] = numeric_df[col].rank(pct = True)

	weighable_attributes = rank_df.columns.values
	meta_df = pd.DataFrame(metadata, index = rank_df.index)

	return numeric_df, meta_df, weighable_attributes

if __name__ == "__main__":
	collect_ticker_data()
	collect_news()

