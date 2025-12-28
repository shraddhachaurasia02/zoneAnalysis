import yfinance as yf
import pandas as pd
import numpy as np

ALLOWED_INTERVALS = {"1d", "1wk", "1mo"}

def scan_stock(
   TICKER, PERIOD, INTERVAL, pattern_choice, num_bases, num_legouts=1,
   legin_threshold=50, legout_threshold=50, base_threshold=35,
   strict_mode=True, entry_buffer_pct=15, base_mode="upto", legout_mode="exact",
   enable_entry_filter=True, zone_status_limit="Fresh Only", marking_type="Wick to Wick"
):
   INTERVAL = INTERVAL.lower()
   if INTERVAL not in ALLOWED_INTERVALS:
       return None, None, f"Invalid interval '{INTERVAL}'."

   stock = yf.download(TICKER, period=PERIOD, interval=INTERVAL, progress=False)
   if stock.empty:
       return None, None, f"No data found for {TICKER}."

   if isinstance(stock.columns, pd.MultiIndex):
       stock.columns = [col[0] for col in stock.columns.values]

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
                   leg_in_candle = stock.iloc[idx]
                   base_candles = stock.iloc[idx + 1 : idx + b + 1]
                   first_legout_candle = stock.iloc[idx + b + 1]
                  
                   if marking_type == "Body to Wick":
                       zone_high = base_candles[[o, c]].max(axis=1).max()
                   else:
                       zone_high = base_candles[h].max()
                  
                   base_low = base_candles[l].min()
                   legout_low = first_legout_candle[l]
                   if label_name == "Drop-Base-Rally":
                       legin_low = leg_in_candle[l]
                       zone_low = min(base_low, legin_low, legout_low)
                   else:
                       zone_low = min(base_low, legout_low)

                   test_count = 0
                   zone_broken = False
                   future_candles = stock.iloc[idx + b + l_o + 1:]
                  
                   for _, f_row in future_candles.iterrows():
                       if f_row[l] <= zone_high:
                           if f_row[l] < zone_low:
                               zone_broken = True
                               break
                           test_count += 1
                  
                   if zone_broken: continue

                   if zone_status_limit == "Fresh Only" and test_count > 0: continue
                   if "Up to 1 time" in zone_status_limit and test_count > 1: continue
                   if "Up to 2 times" in zone_status_limit and test_count > 2: continue

                   # ENTRY BARRIER FIX: Only apply comparison if enabled
                   if enable_entry_filter:
                       zone_entry = stock[o].iloc[idx + b + 1]
                       if not (current_price >= zone_entry and current_price <= (zone_entry * buffer_multiplier)):
                           continue

                   rows = stock.iloc[idx : idx + b + l_o + 1].copy()
                   rows['Pattern_Found'] = label_name
                   rows['Base_Count'] = b
                   rows['LegOut_Count'] = l_o
                   rows['LegIn_Date'] = stock.index[idx].strftime('%Y-%m-%d')
                   rows['LegOut_Date'] = stock.index[idx + b + 1].strftime('%Y-%m-%d')
                   rows['Zone_High'] = zone_high
                   rows['Zone_Low'] = zone_low
                   rows['Tests'] = test_count
                   rows['Formation_ID'] = f"{TICKER}_{rows['LegIn_Date']}_{label_name}_{b}_{marking_type[0]}"
                   all_found.append(rows)
       return all_found

   all_results = []
   choice = pattern_choice.upper()
   if choice in ["RBR", "BOTH"]: all_results.extend(find_patterns("Is_Legin_Green", "Rally-Base-Rally"))
   if choice in ["DBR", "BOTH"]: all_results.extend(find_patterns("Is_Legin_Red", "Drop-Base-Rally"))

   if not all_results: return stock, None, "No patterns found."
   return stock, pd.concat(all_results), None