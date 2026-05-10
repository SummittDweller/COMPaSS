# Function 1: Load Data File

## Purpose
Load data from files (GPX, CSV, Excel, JSON, or ZIP) into a Pandas DataFrame for analysis. The loaded data becomes available for use in subsequent functions.

## When to Use
Use this function when you want to:
- Import data from external files into an analysis pipeline
- Automatically extract and load data from ZIP archives
- Prepare data for analysis using Functions 2 and 3
- Save loaded data as CSV for sharing or backup

## Supported File Formats
- **GPX** (.gpx) - Geocaching/GPS Exchange files (processed with GPSBabel)
- **CSV** (.csv) - Comma-separated values
- **Excel** (.xlsx, .xls) - Microsoft Excel workbooks
- **JSON** (.json) - JavaScript Object Notation
- **ZIP** (.zip) - Compressed archives containing any of the above formats

## Requirements
- A data file must be selected using the **Select File** button
- File must be in one of the supported formats
- For ZIP files, must contain at least one GPX, CSV, Excel, or JSON file
- For GPX support, GPSBabel must be installed and available on PATH

## Usage

1. **Select a data file**
   - Click the **Browse...** button in the **File Selection** section
   - Navigate to and select your data file (.gpx, .csv, .xlsx, .json, or .zip)

2. **Execute Function 1**
   - Select **1: Load Data File** from the Functions dropdown
   - The data will be loaded and analyzed

3. **Review the loaded data**
   - A dialog shows:
     - Data file name
     - Row count
     - Column names
     - Preview of first 5 rows

4. **Save the loaded data (optional)**
   - Click **Save as CSV** to export the loaded data
   - Set an output directory first to specify where to save

## Output
The function displays:
- ✓ Confirmation of successful load
- File name and format
- Number of rows and columns
- List of all column names
- Preview table of first 5 rows

### Data Storage
- Loaded data is stored in memory as a Pandas DataFrame
- Available to other functions for analysis
- Persists across function calls until new data is loaded

## Example Usage

### Loading a CSV File
```
Selected file: sales_data.csv

Output:
✓ Data Loaded Successfully
File: sales_data.csv
Rows: 1000
Columns: 8

Column Names:
  • date
  • product_id
  • quantity
  • price
  • customer_id
  • region
  • sales
  • profit

First few rows preview:
       date  product_id  quantity  price  customer_id region  sales   profit
0  2024-01-01          101       5    10.50         001     North   52.50    15.75
1  2024-01-01          102       3    25.00         002     South   75.00    18.75
...
```

### Loading from a ZIP Archive
```
Selected file: data_export_2024.zip
(Contains: quarterly_sales.csv)

Output:
✓ Data Loaded Successfully
File: data_export_2024.zip
Extracted and loaded from: quarterly_sales.csv
Rows: 500
Columns: 5
```

### Loading a GroundSpeak GPX File
```
Selected file: 24897695_CacheOwnerQuery(SummittDweller).zip
(Contains: geocache_visits.gpx)

Output:
✓ Data Loaded Successfully
File: 24897695_CacheOwnerQuery(SummittDweller).zip
Extracted and loaded from ZIP: geocache_visits.gpx
Successfully loaded GPX via GPSBabel: geocache_visits.gpx
Rows: 214
Columns: 28
```

## Notes
- CSV files are read with automatic delimiter detection
- Excel files use the first sheet by default
- JSON files should be in table format (array of objects)
- GPX files are converted through GPSBabel using unicsv output
- ZIP files automatically extract to a temporary location
- If a ZIP contains multiple supported files, the first one found is used (GPX is preferred)
- If `auto_save_loaded_table` is enabled, Function 1 always autosaves with a timestamp in the filename
- Autosave format is controlled by `auto_save_format` (`csv` or `json`)
- The loaded DataFrame is used by other functions for analysis
- Data is held in memory; restart the application to clear loaded data
