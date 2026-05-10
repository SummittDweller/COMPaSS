# Function 0: App Settings

## Purpose
Open the application settings file in the selected working/output directory and edit values using popup text input fields.

## Current Settings
- **auto_save_loaded_table**: When `true`, Function 1 automatically saves the loaded Pandas table to a CSV file in the working/output directory.
- **auto_save_format**: Output format for autosave files. Allowed values are `csv` and `json`.

## Requirements
- A **Working/Output Directory** must be selected first.

## Usage
1. Set **Working/Output Directory**.
2. Select **0: App Settings** from the function list.
3. Edit values in the text input fields.
4. Click **Save**.

## Settings File
- File name: `compass_settings.json`
- Location: Inside the selected working/output directory

## Accepted Boolean Values
For `auto_save_loaded_table`, you can enter:
- true/false
- yes/no
- 1/0
- on/off

## Accepted Format Values
For `auto_save_format`, enter one of:
- csv
- json
