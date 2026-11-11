# SmartAgri – Agricultural Market Price Analysis and Farmer Decision Support

A beginner-friendly Python Data Analytics project using Streamlit, Pandas, NumPy, Matplotlib and CSV. No machine learning is used.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Run on Replit
1. Create a Python Repl/workspace.
2. Upload/extract this ZIP into the workspace.
3. Ensure `requirements.txt`, `app.py`, and `data/` are at the project root.
4. In the Shell, run `pip install -r requirements.txt`.
5. Run `streamlit run app.py --server.port 3000 --server.address 0.0.0.0`.
6. Open the web preview.

## Data
The included `data/sample_market_prices.csv` is illustrative sample data for testing. It is NOT live market data and must not be cited as actual mandi prices.

The sidebar supports fetching an official data.gov.in resource when you supply:
- a valid data.gov.in API key
- the exact resource ID for an agricultural market-price resource

The resource must provide fields equivalent to state, district, market, commodity, arrival date, min price, max price and modal price. The app maps common column-name variations, but official resource schemas can differ. If fields are missing, the app reports an error rather than inventing values.

Find a suitable resource at https://www.data.gov.in/ and check its field names, units, update frequency and API availability before connecting it. AGMARKNET is a source of Indian agricultural market information. API access and resource availability may vary.

## Important limitations
- Sample data is illustrative only.
- Prices can be stale and may not be available for every product/market.
- The recommendation is a simple decision-support estimate, not a guarantee of sale price or profit.
- Transport cost is entered as one estimated amount per market for the selected comparison.
- Shelf-life values are illustrative reference assumptions. Actual shelf life depends on variety, maturity, handling, temperature, packaging and storage.
- The application does not currently account for commissions, loading/unloading, quality deductions, buyer availability or live logistics.
- Before using fetched data, verify whether prices are in ₹/quintal or another unit.

## Files
- `app.py`: Streamlit application and Python analysis
- `data/sample_market_prices.csv`: illustrative test dataset
- `requirements.txt`: Python dependencies
