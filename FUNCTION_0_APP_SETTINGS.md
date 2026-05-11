# Function 0: App Settings

## Purpose
Open the application settings file in the selected working/output directory and edit values using popup text input fields.

## Security Note
**Sensitive fields are encrypted** (`project_gc_password`, `project_gc_username`, `project_gc_login_url`). You enter and see them as plain text in the editor, but they are automatically encrypted when saved to `compass_settings.json`. This makes it safe to commit your settings file to version control (GitHub, etc.) without exposing credentials.

The encryption key is stored separately in `~/.COMPaSS-data/encryption_key` with restricted permissions.

## Current Settings
- **auto_save_loaded_table**: When `true`, Function 1 automatically saves the loaded Pandas table to a CSV file in the working/output directory.
- **auto_save_format**: Output format for autosave files. Allowed values are `csv` and `json`.
- **project_gc_login_url**: Base login URL for project-gc. **[ENCRYPTED]** Default is:
	`https://project-gc.com/wiki/index.php?title=Special:UserLogin&returnto=Main+Page`
- **project_gc_username**: Saved project-gc username. **[ENCRYPTED]**
- **project_gc_password**: Saved project-gc password. **[ENCRYPTED]**

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
