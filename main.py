import sys

from src.ingestion import extract_batch

if __name__ == "__main__":
    year = int(sys.argv[1]) if len(sys.argv) > 1 else 2024
    extract_batch.run(year=year)
