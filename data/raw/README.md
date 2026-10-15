# Raw Datasets Directory

This directory contains raw smartphone catalogs prior to ingestion, normalization, and quality validation.

## 1. Provided Synthetic Benchmark
- `synthetic_phones_raw.csv`: Procedurally generated 125-device catalog with intentional edge cases (missing attributes, messy string formats, out-of-range values) for functional evaluation and unit testing under CC0 / MIT license.

## 2. Using External / Real-World Datasets
If you are evaluating SmartPick AI on a proprietary or third-party catalog (e.g. from Kaggle, GSMArena, or a retailer export):
1. **Check Licensing**: Verify whether the dataset's license permits redistribution. If redistribution is restricted (e.g. proprietary terms, scraped data), **do not commit the raw files to Git**. `.gitignore` is configured to exclude external raw CSVs by default.
2. **Placement**: Place your raw CSV file in this directory:
   ```bash
   cp /path/to/my_phones.csv data/raw/phones_raw.csv
   ```
3. **Ingestion & Normalization**:
   Execute the ingestion pipeline adapter:
   ```bash
   python -m src.ingest --input data/raw/phones_raw.csv --output data/phones.csv
   ```
4. **Update Provenance Record**:
   Update `data/PROVENANCE.md` with:
   - Source name and URL
   - License and usage terms
   - Retrieval and verification date
