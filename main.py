from utils import get_dse_data

def main():
    print("=== DSE Stock Analysis ===")
    
    # Ask user for file path
    uploaded_file = input("Enter path to your Excel/CSV file: ").strip()

    try:
        all_data, tickers = get_dse_data(uploaded_file)
        print(f"\n✅ Loaded {len(tickers)} tickers successfully!")
    except Exception as e:
        print(f"\n❌ Error loading data: {e}")
        return

    # Example: show first 5 rows of each ticker
    for t in tickers[:5]:  # just show first 5 tickers for brevity
        print(f"\nTicker: {t}")
        print(all_data[t].head())

if __name__ == "__main__":
    main()
