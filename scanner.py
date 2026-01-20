import yfinance as yf
import pandas as pd
import numpy as np

# Added "1y" to allowed intervals
ALLOWED_INTERVALS = {"1d", "1wk", "1mo", "3mo", "6mo", "1y"}

def get_resampled_data(TICKER, PERIOD, INTERVAL):
    """Fetches RAW data and ensures resampling alignment."""
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
            stock = monthly.resample('QS').agg(ohlc_dict).dropna()
        elif INTERVAL in ['6m', '6mo']:
            stock = monthly.resample('2QS').agg(ohlc_dict).dropna()
        elif INTERVAL in ['1y', '1yr']:  # Added: Resamples monthly to Yearly candles
            stock = monthly.resample('YS').agg(ohlc_dict).dropna()
        else:
            stock = monthly
    if isinstance(stock.columns, pd.MultiIndex):
        stock.columns = [col[0] for col in stock.columns.values]
    return stock

def find_demand_zones(stock, TICKER, pattern_choice, num_bases, num_legouts,
                     legin_threshold, legout_threshold, base_threshold,
                     strict_mode, entry_buffer_pct, base_mode, legout_mode,
                     enable_entry_filter, zone_status_limit, marking_type,
                     enable_super_exciting=False, super_lookback=20):
    """
    Core zone detection logic.
    Integrated: Super Exciting (Range >= Avg Range) & Absolute Base tracking.
    """
    if stock.empty: return stock, None
    o, h, l, c = 'Open', 'High', 'Low', 'Close'
    
    # Pre-processing
    stock[f'Open_{TICKER}'], stock[f'High_{TICKER}'] = stock[o], stock[h]
    stock[f'Low_{TICKER}'], stock[f'Close_{TICKER}'] = stock[l], stock[c]
    current_price = stock[c].iloc[-1]
    
    stock['Abs_CO'] = (stock[c] - stock[o]).abs()
    stock['Abs_HL'] = (stock[h] - stock[l]).abs()
    stock['Body_Pct'] = (stock['Abs_CO'] / stock['Abs_HL'].replace(0, 0.001)) * 100
    
    # --- ADDITIONAL CRITERIA: SUPER EXCITING CANDLES ---
    if enable_super_exciting:
        stock['Avg_Range'] = stock['Abs_HL'].rolling(window=super_lookback).mean()
        # High-Low Range must be >= Average High-Low Range
        stock['Range_Qualified'] = stock['Abs_HL'] >= stock['Avg_Range']
    else:
        stock['Range_Qualified'] = True
    
    # Patterns
    stock['Is_Base'] = stock['Body_Pct'] <= base_threshold
    
    # Leg-In/Leg-Out must now also pass Range_Qualified if enabled
    stock['Is_Legin_Green'] = (stock['Body_Pct'] >= legin_threshold) & (stock[o] < stock[c]) & stock['Range_Qualified']
    stock['Is_Legin_Red'] = (stock['Body_Pct'] >= legin_threshold) & (stock[o] > stock[c]) & stock['Range_Qualified']
    stock['Is_Standard_Exciting'] = (stock['Body_Pct'] >= 50) & (stock[o] < stock[c]) & stock['Range_Qualified']
    stock['Is_User_Legout'] = (stock['Body_Pct'] >= legout_threshold) & (stock[o] < stock[c]) & stock['Range_Qualified']
    
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
                    
                    # Capture Zone Markings for visuals
                    if marking_type == "Body to Wick":
                        zone_high = base_candles[[o, c]].max(axis=1).max()
                    else:
                        zone_high = base_candles[h].max()
                    
                    # REQUIREMENT: Capture absolute Extremes of Bases for confluence check
                    base_max_high = base_candles[h].max()
                    base_min_low = base_candles[l].min()

                    zone_low = min(base_candles[l].min(), stock.iloc[idx + b + 1][l])
                    if label_name == "Drop-Base-Rally": 
                        zone_low = min(zone_low, stock.iloc[idx][l])
                    
                    test_count, zone_broken = 0, False
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
                    
                    # Store absolute values for strict confluence
                    rows['Base_Max_High'] = base_max_high
                    rows['Base_Min_Low'] = base_min_low
                    
                    rows['Formation_ID'] = f"{TICKER}_{rows['LegIn_Date']}_{label_name}_{b}"
                    all_found.append(rows)
        return all_found

    all_results = []
    if pattern_choice.upper() in ["RBR", "BOTH"]: all_results.extend(find_patterns("Is_Legin_Green", "Rally-Base-Rally"))
    if pattern_choice.upper() in ["DBR", "BOTH"]: all_results.extend(find_patterns("Is_Legin_Red", "Drop-Base-Rally"))
    return stock, pd.concat(all_results) if all_results else None

def scan_stock(TICKER, PERIOD, htf_interval, htf_pattern, htf_base_count, htf_legout_count,
               htf_legin_thresh, htf_legout_thresh, htf_bs_thresh, htf_strict_mode,
               htf_buffer, htf_base_mode, htf_legout_mode, htf_enable_entry_filter, htf_zone_status, htf_marking_type,
               ltf_interval, ltf_pattern, ltf_base_count, ltf_legout_count,
               ltf_legin_thresh, ltf_legout_thresh, ltf_bs_thresh, ltf_strict_mode,
               ltf_buffer, ltf_base_mode, ltf_legout_mode, ltf_enable_entry_filter, ltf_zone_status, ltf_marking_type,
               enable_confluence, enable_super_exciting=False, super_lookback=20):
    
    htf_stock = get_resampled_data(TICKER, PERIOD, htf_interval)
    htf_zones = pd.DataFrame()
    if enable_confluence and not htf_stock.empty:
        _, htf_result = find_demand_zones(htf_stock, TICKER, htf_pattern, htf_base_count, htf_legout_count, 
                                          htf_legin_thresh, htf_legout_thresh, htf_bs_thresh, htf_strict_mode, 
                                          htf_buffer, htf_base_mode, htf_legout_mode, htf_enable_entry_filter, 
                                          htf_zone_status, htf_marking_type, enable_super_exciting, super_lookback)
        if htf_result is not None: htf_zones = htf_result.drop_duplicates(subset=['Formation_ID'])
    
    ltf_stock = get_resampled_data(TICKER, PERIOD, ltf_interval)
    if ltf_stock.empty: return None, None, "No data found."
    
    ltf_stock, ltf_result = find_demand_zones(ltf_stock, TICKER, ltf_pattern, ltf_base_count, ltf_legout_count, 
                                              ltf_legin_thresh, ltf_legout_thresh, ltf_bs_thresh, ltf_strict_mode, 
                                              ltf_buffer, ltf_base_mode, ltf_legout_mode, ltf_enable_entry_filter, 
                                              ltf_zone_status, ltf_marking_type, enable_super_exciting, super_lookback)
    
    if enable_confluence:
        if htf_zones.empty or ltf_result is None:
            return ltf_stock, None, "No Confluence Zone Found"
        
        confluenced = []
        ltf_unique = ltf_result.drop_duplicates(subset=['Formation_ID'])
        
        for _, ltf_z in ltf_unique.iterrows():
            # CONFLUENCE REQUIREMENT: LTF Base Wicks (High/Low) must be inside HTF Zone
            matches = htf_zones[
                (htf_zones['Zone_Low'] <= ltf_z['Base_Min_Low']) & 
                (ltf_z['Base_Max_High'] <= htf_zones['Zone_High'])
            ]
            
            if not matches.empty:
                ltf_z_copy = ltf_z.copy()
                ltf_z_copy['HTF_LegIn_Date'] = matches.iloc[0]['LegIn_Date']
                confluenced.append(ltf_z_copy)
        
        if not confluenced: return ltf_stock, None, "No Confluence Zone Found"
        ltf_result = pd.DataFrame(confluenced)
    
    return ltf_stock, ltf_result, None