import yfinance as yf
import pandas as pd

# Download 5 years of Apple (AAPL) data
df = yf.download("AAPL", start="2019-01-01", end="2024-01-01")
# We only need the closing price for this simple test
df = df[['Close']]

print(df.head())