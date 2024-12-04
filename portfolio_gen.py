import json, pandas as pd, numpy as np
from constants import SECTORS, NUM_STOCKS_PER_SECTOR, TOTAL_FUND

def generate_final_stock_portfolio():
  with open("weightages/overall_strategy.json", "r") as overall_json:
    overall_strategy = json.load(overall_json)
  weightages = []
  for sector in SECTORS:
    with open(f"weightages/sectors/{sector}_strategy.json", "r") as strat_json:
      weightages.append(json.load(strat_json))
  
  metadata = pd.read_csv("tickers/tickers_metadata.csv").set_index("Unnamed: 0")
  numerics = pd.read_csv("tickers/tickers_numerics.csv").set_index("Unnamed: 0")
  numeric_columns = numerics.columns

  valid_stocks = metadata[metadata["sector"].isin(SECTORS)]
  valid_numerics = numerics.loc[valid_stocks.index]
  valid_numerics["sector"] = valid_stocks.loc[valid_numerics.index]["sector"]

  best_stocks_per_sector = dict()

  for sector, raw_weights in zip(SECTORS, weightages):
    sector_stocks = valid_numerics[valid_numerics["sector"] == sector].copy()
    sector_scores = []
    weights = dict()
    for weight in raw_weights:
      if weight in numeric_columns:
        weights[weight] = raw_weights[weight]
        
    for stock in sector_stocks.index.values:
      curr_stock = sector_stocks.loc[stock]
      score = 0.0
      skip_count = 0
      for weight in weights:
        val = curr_stock.loc[weight]
        if ((str(val) != "nan") or ("inf" in str(val))):
          score += val * weights[weight]
        else:
          skip_count += 1
      
      if skip_count >= (len(weights) // 2):
        sector_scores.append(np.nan)
      else:
        sector_scores.append(score)
    
    sector_stocks["scores"] = sector_scores
    best_stocks = sector_stocks[~sector_stocks["scores"].isna()].sort_values(by = "scores", ascending=False).head(NUM_STOCKS_PER_SECTOR)
    best_stocks_per_sector[sector] = list(zip(best_stocks.index.values.tolist(), best_stocks["scores"].values.tolist()))
  
  strategy_sum = sum(v for v in overall_strategy.values())
  investments = dict()
  for sector in SECTORS:
    sector_investments = dict()
    for stock in best_stocks_per_sector[sector]:
      sector_investments[stock[0]] = TOTAL_FUND * (overall_strategy[sector] / strategy_sum) / NUM_STOCKS_PER_SECTOR
    investments[sector] = sector_investments

  with open("weightages/final_investments.json", "w") as final_json:
    json.dump(investments, final_json)

  # numerics

if __name__ == "__main__":
  generate_final_stock_portfolio()