# COMPaSS Changelog

All notable changes to the COMPaSS (Cache Owner Management Platform and Sites System) project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2026-05-11

### Development Session Summary
Implemented comprehensive data management pipeline with persistent settings, multi-format data loading, and encrypted credential storage. This release transforms COMPaSS from a template application into a functional geocaching data management platform.

### Added

#### Function 0: App Settings Manager
- **Settings Editor Dialog**: Modal popup with text input fields for all application settings
- **Persistent Configuration**: Settings stored in `compass_settings.json` within the working directory
- **Settings Available**:
  - `auto_save_loaded_table`: Boolean toggle for auto-saving loaded data
  - `auto_save_format`: Format selection (csv or json) for auto-saved files
  - `project_gc_login_url`: Base login URL for project-gc website
  - `project_gc_username`: Project-gc account username
  - `project_gc_password`: Project-gc account password (masked in UI, encrypted at rest)
- **Validation**: Input validation with helpful error messages for invalid boolean/format values
- **Backward Compatibility**: Gracefully merges loaded settings with defaults if missing

#### Function 1: Multi-Format Data Loader
- **Supported File Formats**:
  - ✅ GPX (GroundSpeak GPS exchange format) — primary geocaching export format
  - ✅ CSV (Comma-separated values) — with automatic detection
  - ✅ Excel (.xlsx, .xls) — via openpyxl
  - ✅ JSON (Records format)
  - ✅ ZIP archives — automatic extraction with format detection
  
- **GPX Loading via GPSBabel**:
  - Subprocess integration with `/opt/homebrew/bin/gpsbabel` (macOS) or system PATH
  - Converts GPX files to CSV in-memory using temporary files
  - Preserves all GPS and waypoint data
  - Automatic cleanup of temporary conversion files
  - Graceful fallback if GPSBabel not found

- **ZIP File Handling**:
  - Automatic extraction to temporary directory
  - Intelligent file selection (prefers primary GPX over waypoints-only exports)
  - Filename heuristics: deprioritizes files with "-wpts" suffix
  - Support for nested directory structures

- **Data Output**:
  - Loads data into Pandas DataFrame
  - Shows preview dialog with:
    - Row and column counts
    - Column names
    - First 5 rows preview
  - Returns both data and status message for logging

#### Auto-Save System
- **Conditional Auto-Save**: Respects `auto_save_loaded_table` setting
- **Timestamped Filenames**: Format `{base}_autosave_{YYYYMMDD_HHMMSS}.{csv|json}`
- **Format Selection**: Uses `auto_save_format` setting (csv or json)
- **Automatic Triggering**: Activates after successful data load if enabled
- **Manual Save Option**: Always available via "Save" button in preview dialog

#### Encrypted Credential Storage
- **Encryption Method**: AES-256 symmetric encryption using Fernet (cryptography library)
- **Encrypted Fields**: `project_gc_password`, `project_gc_username`, `project_gc_login_url`
- **Key Management**:
  - Encryption key auto-generated on first use
  - Stored in `~/.COMPaSS-data/encryption_key`
  - Restricted permissions (0o600 — owner read/write only)
  - Key persists across sessions for consistent decryption
  
- **User Experience**:
  - Users enter credentials as plain text in Function 0 editor
  - Encryption/decryption transparent — no additional UI changes
  - Settings file safe for GitHub/version control (credentials encrypted at rest)
  
- **Implementation**:
  - `encrypt_sensitive_settings()`: Encrypts before JSON save
  - `decrypt_sensitive_settings()`: Decrypts after JSON load
  - Graceful handling of already-plaintext values (migration support)
  - Non-sensitive fields remain unencrypted for readability

### Changed

#### Dependencies
- **Added**: `cryptography>=41.0.0` — for AES-256 encryption of sensitive settings
- **Existing**: pandas, openpyxl unchanged; GPSBabel expected as external tool

#### Documentation
- Updated `FUNCTION_0_APP_SETTINGS.md`: Added security note about encryption and clarified settings purpose
- Updated `FUNCTION_1_LOAD_DATA.md`: Comprehensive guide for multi-format loading and auto-save
- Updated `README.md`: Noted new settings file location and structure

#### UI/UX
- Function dropdown now includes Function 0 with "⚙️ App Settings" label
- Improved dropdown sorting to prioritize Function 0 (numeric prefix sorting)
- Settings editor uses password field for project_gc_password (masked input)
- Help documentation system supports new function help files

### Technical Implementation

#### Code Architecture
- `get_or_create_encryption_key()`: One-time key setup with persistence
- `encrypt_sensitive_settings(dict) → dict`: Encrypts before save
- `decrypt_sensitive_settings(dict) → dict`: Decrypts after load, handles legacy plaintext
- `load_app_settings()`: Integrates decrypt step
- `save_app_settings()`: Integrates encrypt step
- `_load_gpx_with_gpsbabel()`: Subprocess wrapper for GPX conversion
- `load_data_file()`: Router function dispatching to appropriate loader based on file type

#### File System Changes
- New file: `~/.COMPaSS-data/encryption_key` (created automatically on first use)
- New file: `{working_dir}/compass_settings.json` (app settings, encrypted sensitive fields)
- Auto-save files: `{working_dir}/{name}_autosave_{YYYYMMDD_HHMMSS}.{csv|json}`

### Testing & Validation

#### Verified Functionality
- ✅ Encryption/decryption round-trip (plaintext → encrypted → plaintext)
- ✅ GPX loading from GroundSpeak exports (tested with 91-waypoint cache)
- ✅ ZIP file selection with intelligent file preference
- ✅ Auto-save filename generation with correct timestamp format
- ✅ Settings save/load cycle via Function 0 popup
- ✅ Backward compatibility with plaintext settings
- ✅ All code compiles cleanly, no syntax errors
- ✅ No diagnostic errors detected

#### Debugging Context
- ZIP handling: Fixed file selection to prefer primary GPX over -wpts variant
- Function 0 visibility: Fixed dropdown sorting and function registration
- GPSBabel integration: Subprocess error handling for missing tool
- Settings storage: Verified JSON serialization of encrypted credentials

---

## [1.0.0] - 2026-05-04

### Initial Release

COMPaSS is a production-ready desktop application for managing cache owners and sites. It was created by extracting and generalizing the proven UI framework from OHM (Oral History Manager), resulting in a clean 715-line application that maintains all of OHM's battle-tested features while removing application-specific functionality.

### Features

#### UI Architecture (Based on OHM)
- **Professional Layout** with proven vertical spacing and organization
- **Compass Icon** (🧭) in header using Flet Icons
- **Collapsible Directories Section** to maximize screen space once directories are set
- **File Selection Section** always visible for quick file changes between operations
- **Status Output** with copy-to-clipboard button
- **Log Output** with timestamped entries, copy and clear buttons
- **Function Dropdown** with emoji icons and workflow ordering
- **Help Mode** checkbox to view documentation instead of executing functions

#### Core Systems
- **Persistent Settings**
  - Automatic save/restore of window position
  - Directory and file selections persisted across sessions
  - Function usage tracking with timestamps and counts
  - Stored in `~/COMPaSS-data/persistent.json`

- **Logging System**
  - Timestamped log files in `~/COMPaSS-data/logfiles/`
  - Real-time log display in UI with prepended entries
  - Separate file and console handlers
  - Configurable log levels
  - Reduced verbosity for Flet internal logging

- **Function Management**
  - Dictionary-based function registry
  - Icon support with emoji indicators
  - Help file association per function
  - Usage tracking and statistics
  - Automatic dropdown population

#### Example Functions
- **Function 1** 📁: List all files in a directory
- **Function 2** 📊: Count files by extension type with statistics
- **Function 3** 💻: Display system information
- Each includes professional help documentation in markdown

#### Development & Distribution
- **Runtime Scripts**
  - `run.sh`: macOS/Linux launcher with automatic venv management
  - `run.bat`: Windows launcher with automatic venv management
  
- **Distribution Tools**
  - `build_dmg.sh`: Create macOS DMG installers
  - `build_windows_zip.sh`: Create Windows ZIP packages
  
- **Documentation**
  - Comprehensive README with customization guide
  - QUICKSTART.md for rapid onboarding
  - Individual function help files in markdown
  - CHANGELOG following Keep a Changelog format

- **Quality**
  - `.gitignore` with sensible Python/Flet exclusions
  - MIT License
  - Clean 715-line codebase (down from OHM's 3160 lines)
  - Well-commented code with docstrings

### Technical Details
- **Python 3.8+** required
- **Flet 0.25.2** with flet-desktop
- No additional dependencies for base template
- Cross-platform: macOS, Windows, Linux

### Credits
FLAT's UI architecture is based on the patterns developed for OHM (Oral History Manager) by Mark McFate for Digital.Grinnell. The application represents the distillation of real-world application development experience into a reusable foundation.

---

## Future Plans

Planned improvements for future releases:
- Additional example functions demonstrating common patterns
- Theme customization support
- Window state management (maximized, minimized)
- Multi-language support framework
- Plugin/extension system
- Additional UI components (progress bars, tabs, etc.)

---

## Contributing

Contributions are welcome! Please feel free to submit pull requests or open issues for:
- Bug fixes
- Documentation improvements  
- Additional example functions
- UI enhancements
- Code optimization

## Repository

https://github.com/Digital-Grinnell/COMPaSS

### Documentation

- Comprehensive README with:
  - Quick start guide
  - Customization instructions
  - How to add new functions
  - How to modify UI layout
  - Building standalone packages
  - Flet resources and tips

- Function-specific help documentation:
  - `FUNCTION_0_APP_SETTINGS.md`
  - `FUNCTION_1_LOAD_DATA.md`
  - `FUNCTION_2_COUNT_FILES.md`
  - `FUNCTION_3_SYSTEM_INFO.md`

### Technical Details

- Built with Flet 0.25.2
- Python 3.8+ required
- No external dependencies beyond Flet
- Cross-platform: macOS, Windows, Linux

---

## Future Development

COMPaSS is a starting application. When you customize COMPaSS for your own needs:

1. Update the changelog with your app's version history
2. Replace example functions with your own
3. Customize the UI to match your needs
4. Add any additional dependencies required

---

## Credits

COMPaSS was derived from the OHM (Oral History Manager) project, which demonstrated effective patterns for Flet desktop applications including persistent settings, logging, function management, and help documentation.

Built with [Flet](https://flet.dev) - a Python framework for building desktop applications.
