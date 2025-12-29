import yfinance as yf
import pandas as pd
import numpy as np

ALLOWED_INTERVALS = {"1d", "1wk", "1mo", "3mo", "6mo"}

def get_resampled_data(TICKER, PERIOD, INTERVAL):
    """Fetches RAW data and ensures 6M alignment to half-year starts (Jan 1 / July 1)."""
    INTERVAL = INTERVAL.lower()
    fetch_params = {"period": PERIOD, "progress": False, "auto_adjust": False, "actions": False}

    if INTERVAL in ["1d", "1wk"]:
        stock = yf.download(TICKER, interval=INTERVAL, **fetch_params)
    elif INTERVAL in ["1m", "1mo"]:
        stock = yf.download(TICKER, interval="1mo", **fetch_params)
    else:  
        monthly = yf.download(TICKER, interval="1mo", **fetch_params)
        if monthly.empty: return monthly
        if isinstance(monthly.columns, pd.MultiIndex):
            monthly.columns = [col[0] for col in monthly.columns.values]
        
        ohlc_dict = {'Open': 'first', 'High': 'max', 'Low': 'min', 'Close': 'last', 'Volume': 'sum'}
        
        if INTERVAL in ['3m', '3mo']:
            # Aligns to Jan 1, Apr 1, Jul 1, Oct 1
            stock = monthly.resample('QS').agg(ohlc_dict).dropna()
        elif INTERVAL in ['6m', '6mo']:
            # ✅ Aligns to Jan 1 and Jul 1 strictly
            stock = monthly.resample('2QS').agg(ohlc_dict).dropna()
        else:
            stock = monthly

    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = [col[0] for col in stock.columns.values]
    return stock

def scan_stock(TICKER, PERIOD, INTERVAL, pattern_choice, num_bases, num_legouts=1,
               legin_threshold=50, legout_threshold=50, base_threshold=35,
               strict_mode=True, entry_buffer_pct=15, base_mode="upto", legout_mode="exact",
               enable_entry_filter=True, zone_status_limit="Fresh Only", marking_type="Wick to Wick"):
   
   stock = get_resampled_data(TICKER, PERIOD, INTERVAL.lower())
   if stock.empty: return None, None, "No data found."

   o, h, l, c = 'Open', 'High', 'Low', 'Close'
   stock[f'Open_{TICKER}'], stock[f'High_{TICKER}'] = stock[o], stock[h]
   stock[f'Low_{TICKER}'], stock[f'Close_{TICKER}'] = stock[l], stock[c]
   current_price = stock[c].iloc[-1]

   stock['Abs_CO'] = (stock[c] - stock[o]).abs()
   stock['Abs_HL'] = (stock[h] - stock[l]).abs()
   stock['Body_Pct'] = (stock['Abs_CO'] / stock['Abs_HL'].replace(0, 0.001)) * 100

   stock['Is_Base'] = stock['Body_Pct'] <= base_threshold
   stock['Is_Legin_Green'] = (stock['Body_Pct'] >= legin_threshold) & (stock[o] < stock[c])
   stock['Is_Legin_Red'] = (stock['Body_Pct'] >= legin_threshold) & (stock[o] > stock[c])
   stock['Is_Standard_Exciting'] = (stock['Body_Pct'] >= 50) & (stock[o] < stock[c])
   stock['Is_User_Legout'] = (stock['Body_Pct'] >= legout_threshold) & (stock[o] < stock[c])

   base_range = [num_bases] if base_mode == "exact" else range(1, num_bases + 1)
   legout_range = [num_legouts] if legout_mode == "exact" else range(1, num_legouts + 1)

   def find_patterns(legin_col, label_name):
       all_found = []
       buffer_multiplier = 1 + (entry_buffer_pct / 100)
       for b in base_range:
           for l_o in legout_range:
               mask = (stock[legin_col] == True)
               for i in range(1, b + 1):
                   mask &= (stock['Is_Base'].shift(-i) == True)
               mask &= (stock['Is_User_Legout'].shift(-(b + 1)) == True)
               if l_o > 1:
                   for j in range(2, l_o + 1):
                       mask &= (stock['Is_Standard_Exciting'].shift(-(b + j)) == True)
               if strict_mode:
                   mask &= (stock[c].shift(-(b + 1)) > stock[h])

               indices = np.where(mask)[0]
               for idx in indices:
                   base_candles = stock.iloc[idx + 1 : idx + b + 1]
                   zone_high = base_candles[[o, c]].max(axis=1).max() if marking_type == "Body to Wick" else base_candles[h].max()
                   zone_low = min(base_candles[l].min(), stock.iloc[idx + b + 1][l])
                   if label_name == "Drop-Base-Rally":
                       zone_low = min(zone_low, stock.iloc[idx][l])

                   test_count = 0
                   zone_broken = False
                   future_candles = stock.iloc[idx + b + l_o + 1:]
                   for _, f_row in future_candles.iterrows():
                       if f_row[l] <= zone_high:
                           if f_row[l] < zone_low:
                               zone_broken = True; break
                           test_count += 1
                   if zone_broken: continue
                   if (zone_status_limit == "Fresh Only" and test_count > 0) or \
                      ("Up to 1 time" in zone_status_limit and test_count > 1) or \
                      ("Up to 2 times" in zone_status_limit and test_count > 2): continue

                   if enable_entry_filter:
                       zone_entry = stock[o].iloc[idx + b + 1]
                       if not (current_price >= zone_entry and current_price <= (zone_entry * buffer_multiplier)): continue

                   rows = stock.iloc[idx : idx + b + l_o + 1].copy()
                   rows['Pattern_Found'] = label_name
                   rows['Base_Count'], rows['LegOut_Count'] = b, l_o
                   rows['LegIn_Date'] = stock.index[idx].strftime('%Y-%m-%d')
                   rows['Zone_High'], rows['Zone_Low'], rows['Tests'] = zone_high, zone_low, test_count
                   rows['Formation_ID'] = f"{TICKER}_{rows['LegIn_Date']}_{label_name}_{b}"
                   all_found.append(rows)
       return all_found

   all_results = []
   if pattern_choice.upper() in ["RBR", "BOTH"]: all_results.extend(find_patterns("Is_Legin_Green", "Rally-Base-Rally"))
   if pattern_choice.upper() in ["DBR", "BOTH"]: all_results.extend(find_patterns("Is_Legin_Red", "Drop-Base-Rally"))

   return stock, pd.concat(all_results) if all_results else None, None