import sys

from src.ingestion import extract_batch

if __name__ == "__main__":
    years = [int(a) for a in sys.argv[1:]] or [2024]
    extract_batch.run(years=years)
