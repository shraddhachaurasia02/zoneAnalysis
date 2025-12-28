# data/__init__.py
from .nifty_indices import NIFTY_50, NIFTY_100, NIFTY_200, NIFTY_500, Cash_Market

STOCK_GROUPS = {
    "Nifty 50": NIFTY_50,
    "Nifty 100": NIFTY_100,
    "Nifty 200": NIFTY_200,
    "Nifty 500": NIFTY_500,
    "Cash Market": Cash_Market
}