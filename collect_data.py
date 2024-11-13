from tqdm import tqdm
from bs4 import BeautifulSoup
from markdownify import markdownify as md
import yfinance as yf
import json
import pandas as pd
import numpy as np
import requests
import datetime
import requests_cache

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
		"longBusinessSummary",
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

	session = requests_cache.CachedSession('yfinance.cache')
	session.headers['User-agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
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

def process_elements(elems):
	text = ""
	for elem in elems:
		text += elem.text.strip() + "\n"
	return text

def collect_deloitte():
	def collect_webpage(url):
		r = requests.get(url)
		soup = BeautifulSoup(r.text, "html.parser")
		elements = soup.find(class_="responsivegrid content-width-di-sm aem-GridColumn aem-GridColumn--default--8").find_all(["h1", "h2", "h3", "li", "p"])
		return process_elements(elements)
		
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

def collect_motley_sectors():
	docs = []
	sector_articles = [
    "https://www.fool.com/investing/stock-market/market-sectors/",
    "https://www.fool.com/investing/stock-market/market-sectors/materials/",
    "https://www.fool.com/investing/stock-market/market-sectors/industrials/",
    "https://www.fool.com/investing/stock-market/market-sectors/consumer-staples/",
    "https://www.fool.com/investing/stock-market/market-sectors/information-technology/",
    "https://www.fool.com/investing/stock-market/market-sectors/real-estate-investing/",
    "https://www.fool.com/investing/stock-market/market-sectors/energy/",
    "https://www.fool.com/investing/stock-market/market-sectors/healthcare/"
	]
	for url in tqdm(sector_articles):
		r = requests.get(url)
		soup = BeautifulSoup(r.text, "html.parser")
		paragraphs = [p.text for p in soup.find("div",
																class_="max-w-full w-full mx-auto article-body"
																).find_all("p")]

		key_points = [filter(lambda x : x.text.strip() != "",
												point.contents).__next__().text.strip()
									for point in soup.find("div", class_="mt-8 bg-white shadow-card p-20px").find("ul").find_all("li")]
		content = "\n".join(key_points + paragraphs)
		docs.append(content)
	return docs

def collect_motley_fools():
	headers = {
    "X-Requested-With": "fetch"
	}
	num_pages = 4
	articles = []
	for p in range(num_pages):
			print(f"Page {p}")
			fool_url = f"https://www.fool.com/market-trends/filtered_articles_by_page/?page={p}"
			r = requests.get(fool_url, headers=headers)
			html = json.loads(r.text)
			soup = BeautifulSoup(html['html'], "html.parser")
			articles_raw = soup.find_all("div", class_="flex py-12px text-gray-1100")
			
			for art in tqdm(articles_raw):
					article = dict()
					
					date_str = art.find("div", class_="text-sm text-gray-800 mb-2px md:mb-8px").text.split("by")[0].strip()
					post_date = datetime.datetime.strptime(date_str, "%b %d, %Y")
					article["date"] = post_date

					title = art.find("h5", class_="self-center mb-6 font-medium md:text-h5 text-md md:mb-4px").text.strip()
					article["title"] = title

					link = "https://www.fool.com" + art.find("a")['href']
					article["link"] = link

					articles.append(article)
	
	documents = []
	for article in tqdm(articles):
		try:
			r = requests.get(article["link"])
			soup = BeautifulSoup(r.text, "html.parser")
			paragraphs = [p.text for p in soup.find("section",
																						class_="container mx-auto bg-white px-24px md:px-40 pt-36px sm:pt-16px md:pt-16px md:pb-8"
																						).find_all("p")]
			
			key_points = [point.find_all("div")[-1].text for point in soup.find("div", class_="mt-8 bg-white shadow-card p-20px").find("ul").find_all("li")]
			content = "\n".join(key_points + paragraphs)
			documents.append(content)
		except Exception as e:
			print("Motley Fool Document Parsing Failed")
			print(e)
	
	return documents

def collect_news():
	documents = []
	sources = [
		# Motley Fools with sector definitions and recommendations
		collect_motley_sectors,

		# Motley Fools covers market trends
		collect_motley_fools,

		# Deloitte covers global trends
		collect_deloitte
	]

	for i, source in enumerate(sources):
		print(f"Source {i}")
		documents.extend(source())

	for i, doc in enumerate(documents):
		with open(f"input/markdown/markdown_{i}.md", "w") as md_txt:
			md_txt.write(doc)


def collect_ticker_data():
	tickers = get_tickers()
	metadatas = []
	numerics = []
	symbols = []
	summaries = []
	sectors = set()
	for ticker in tqdm(tickers):
		try:
			symbol = ticker["symbol"]
			m, n = get_ticker_info(symbol)
			summaries.append((symbol, m["long business summary"]))
			m["name"] = ticker["name"]
			m["symbol"] = symbol
			sectors.add(m["sector"])
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
	with open("tickers/sectors.json", "w") as sector_json:
		json.dump(list(sectors), sector_json)
	
	numeric_df, meta_df, weighable_attributes = clean_attributes(numerics, metadatas, symbols)

	numeric_df.to_csv("tickers/tickers_numerics.csv")
	meta_df.to_csv("tickers/tickers_metadata.csv")

	with open("tickers/weighable_attributes.json", "w") as attr_json:
		json.dump(weighable_attributes.tolist(), attr_json)
	
	# for symbol, summary in summaries:
	# 	with open(f"input/markdown/summaries/markdown_{symbol}.md", "w") as symbol_json:
	# 		symbol_json.write(summary)
		
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
	print("Collecting Stock Data")
	collect_ticker_data()
	print("Collecting News")
	collect_news()

