"""
COMPaSS - Cache Owner Management Platform and Sites System
A desktop application for managing cache owners and sites with persistent settings, logging,
function management, and help documentation system based on OHM's proven UI.
"""

import flet as ft
import os
import getpass
import logging
import json
import platform
import socket
import zipfile
import tempfile
import subprocess
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple
import pandas as pd
from cryptography.fernet import Fernet, InvalidToken

# Configure logging
DATA_DIR = Path.home() / "COMPaSS-data"
os.makedirs(DATA_DIR / "logfiles", exist_ok=True)
log_filename = DATA_DIR / "logfiles" / f"compass_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

file_handler = logging.FileHandler(log_filename)
file_handler.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.ERROR)

formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logging.basicConfig(level=logging.DEBUG, handlers=[file_handler, console_handler])
logger = logging.getLogger(__name__)

# Reduce Flet's logging verbosity
logging.getLogger("flet").setLevel(logging.WARNING)
logging.getLogger("flet_core").setLevel(logging.WARNING)
logging.getLogger("flet_desktop").setLevel(logging.WARNING)

# Persistent storage file
PERSISTENCE_FILE = DATA_DIR / "persistent.json"

# Encryption key file
ENCRYPTION_KEY_FILE = DATA_DIR / "encryption_key"

# Sensitive fields that should be encrypted in settings
SENSITIVE_FIELDS = ["project_gc_password", "project_gc_username", "project_gc_login_url"]


def get_or_create_encryption_key() -> bytes:
    """
    Get or create the encryption key from ~/.COMPaSS-data/encryption_key.
    Returns the Fernet key as bytes.
    """
    if ENCRYPTION_KEY_FILE.exists():
        try:
            with open(ENCRYPTION_KEY_FILE, "rb") as f:
                key = f.read()
            # Verify it's a valid Fernet key
            Fernet(key)
            return key
        except Exception as e:
            logger.warning(f"Invalid encryption key file, regenerating: {str(e)}")
    
    # Generate a new key
    key = Fernet.generate_key()
    try:
        with open(ENCRYPTION_KEY_FILE, "wb") as f:
            f.write(key)
        # Restrict permissions to owner only
        os.chmod(ENCRYPTION_KEY_FILE, 0o600)
    except Exception as e:
        logger.error(f"Could not save encryption key: {str(e)}")
    
    return key


def encrypt_sensitive_settings(settings: dict) -> dict:
    """
    Encrypt sensitive fields in settings dictionary.
    Returns a new dictionary with encrypted values.
    """
    try:
        key = get_or_create_encryption_key()
        cipher = Fernet(key)
        encrypted = dict(settings)
        
        for field in SENSITIVE_FIELDS:
            if field in encrypted and encrypted[field]:
                plaintext = str(encrypted[field])
                ciphertext = cipher.encrypt(plaintext.encode()).decode()
                encrypted[field] = ciphertext
        
        return encrypted
    except Exception as e:
        logger.error(f"Could not encrypt settings: {str(e)}")
        return settings


def decrypt_sensitive_settings(settings: dict) -> dict:
    """
    Decrypt sensitive fields in settings dictionary.
    Returns a new dictionary with decrypted values.
    Gracefully handles already-decrypted values and encryption errors.
    """
    try:
        key = get_or_create_encryption_key()
        cipher = Fernet(key)
        decrypted = dict(settings)
        
        for field in SENSITIVE_FIELDS:
            if field in decrypted and decrypted[field]:
                ciphertext = decrypted[field]
                try:
                    # Try to decrypt; if it fails, assume it's already plaintext
                    plaintext = cipher.decrypt(ciphertext.encode()).decode()
                    decrypted[field] = plaintext
                except (InvalidToken, ValueError):
                    # Already plaintext or corrupted; leave as-is
                    pass
        
        return decrypted
    except Exception as e:
        logger.error(f"Could not decrypt settings: {str(e)}")
        return settings


class PersistentStorage:
    """Handle persistent storage of UI state and function usage."""

    def __init__(self):
        self.data = self.load()

    def load(self) -> dict:
        """Load persistent data from file."""
        try:
            if os.path.exists(PERSISTENCE_FILE):
                with open(PERSISTENCE_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"Loaded persistent data from {PERSISTENCE_FILE}")
                return data
        except Exception as e:
            logger.warning(f"Could not load persistent data: {str(e)}")

        return {
            "ui_state": {
                "last_input_dir": "",
                "last_output_dir": "",
                "last_file": "",
                "window_left": None,
                "window_top": None,
            },
            "function_usage": {},
        }

    def save(self):
        """Save persistent data to file."""
        try:
            with open(PERSISTENCE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            logger.debug(f"Saved persistent data to {PERSISTENCE_FILE}")
        except Exception as e:
            logger.error(f"Could not save persistent data: {str(e)}")

    def set_ui_state(self, field: str, value: str):
        """Update UI state field."""
        self.data["ui_state"][field] = value
        self.save()

    def get_ui_state(self, field: str, default: str = "") -> str:
        """Get UI state field."""
        return self.data["ui_state"].get(field, default)

    def record_function_usage(self, function_name: str):
        """Record that a function was used."""
        if function_name not in self.data["function_usage"]:
            self.data["function_usage"][function_name] = {"count": 0}

        self.data["function_usage"][function_name]["last_used"] = datetime.now().isoformat()
        self.data["function_usage"][function_name]["count"] = (
            self.data["function_usage"][function_name].get("count", 0) + 1
        )
        self.save()


def load_help_document(filename: str) -> str:
    """Load help documentation from markdown file."""
    try:
        help_path = Path(__file__).parent / filename
        if help_path.exists():
            return help_path.read_text(encoding="utf-8")
        else:
            return f"# Help Documentation Not Found\n\nCould not find {filename}"
    except Exception as e:
        logger.error(f"Error loading help document {filename}: {e}")
        return f"# Error Loading Help\n\n{str(e)}"


# Global variable to store the current dataframe for use across functions
current_dataframe = None
dataframe_filename = None
APP_SETTINGS_FILENAME = "compass_settings.json"
PROJECT_GC_LOGIN_URL_DEFAULT = (
    "https://project-gc.com/wiki/index.php?title=Special:UserLogin&returnto=Main+Page"
)
PROJECT_GC_USERNAME_DEFAULT = "SummittDweller"
PROJECT_GC_PASSWORD_DEFAULT = "$ummittDw3ll3r"
DEFAULT_APP_SETTINGS = {
    "auto_save_loaded_table": False,
    "auto_save_format": "csv",
    "project_gc_login_url": PROJECT_GC_LOGIN_URL_DEFAULT,
    "project_gc_username": PROJECT_GC_USERNAME_DEFAULT,
    "project_gc_password": PROJECT_GC_PASSWORD_DEFAULT,
}


def get_app_settings_path(working_dir: str) -> Path:
    """Return the settings file path for a working directory."""
    return Path(working_dir) / APP_SETTINGS_FILENAME


def ensure_app_settings_file(working_dir: str) -> Path:
    """Create the app settings file with defaults if it does not exist."""
    settings_path = get_app_settings_path(working_dir)
    os.makedirs(settings_path.parent, exist_ok=True)
    if not settings_path.exists():
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_APP_SETTINGS, f, indent=2, ensure_ascii=False)
    return settings_path


def load_app_settings(working_dir: str) -> Tuple[dict, str]:
    """Load app settings from the working directory settings file."""
    try:
        settings_path = ensure_app_settings_file(working_dir)
        with open(settings_path, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        # Decrypt sensitive fields
        loaded = decrypt_sensitive_settings(loaded)
        settings = dict(DEFAULT_APP_SETTINGS)
        settings.update(loaded)
        return settings, ""
    except Exception as e:
        logger.error(f"Could not load app settings: {str(e)}")
        return dict(DEFAULT_APP_SETTINGS), f"Error loading app settings: {str(e)}"


def save_app_settings(working_dir: str, settings: dict) -> Tuple[bool, str]:
    """Save app settings to the working directory settings file.
    Sensitive fields are encrypted before saving.
    """
    try:
        settings_path = ensure_app_settings_file(working_dir)
        # Encrypt sensitive fields before saving
        settings_to_save = encrypt_sensitive_settings(settings)
        with open(settings_path, "w", encoding="utf-8") as f:
            json.dump(settings_to_save, f, indent=2, ensure_ascii=False)
        return True, str(settings_path)
    except Exception as e:
        logger.error(f"Could not save app settings: {str(e)}")
        return False, f"Error saving app settings: {str(e)}"


def parse_bool_text(value: str) -> Optional[bool]:
    """Parse user-entered boolean text. Returns None if invalid."""
    lowered = (value or "").strip().lower()
    if lowered in ["true", "1", "yes", "y", "on"]:
        return True
    if lowered in ["false", "0", "no", "n", "off"]:
        return False
    return None


def parse_auto_save_format(value: str) -> Optional[str]:
    """Parse and validate auto-save format text. Returns None if invalid."""
    lowered = (value or "").strip().lower()
    if lowered in ["csv", "json"]:
        return lowered
    return None


def _load_gpx_with_gpsbabel(gpx_path: Path) -> Tuple[Optional[pd.DataFrame], str]:
    """Convert GPX to CSV with GPSBabel and load into a DataFrame."""
    gpsbabel_path = shutil.which("gpsbabel")
    if not gpsbabel_path:
        return None, (
            "Error: GPX input detected but GPSBabel is not installed or not on PATH. "
            "Install GPSBabel and retry."
        )

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            csv_path = Path(temp_dir) / f"{gpx_path.stem}_gpsbabel.csv"
            cmd = [
                gpsbabel_path,
                "-i",
                "gpx",
                "-f",
                str(gpx_path),
                "-o",
                "unicsv",
                "-F",
                str(csv_path),
            ]
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                stderr = (result.stderr or "").strip()
                return None, f"Error: GPSBabel failed to convert GPX file. {stderr}"

            df = pd.read_csv(csv_path)
            return (
                df,
                f"Successfully loaded GPX via GPSBabel: {gpx_path.name}\n"
                f"Rows: {len(df)}, Columns: {len(df.columns)}",
            )
    except Exception as e:
        logger.error(f"Error converting GPX with GPSBabel: {str(e)}")
        return None, f"Error loading GPX via GPSBabel: {str(e)}"


def load_data_file(file_path: str) -> Tuple[Optional[pd.DataFrame], str]:
    """
    Load data from a file (CSV, Excel, JSON, GPX, or ZIP containing supported files).
    Returns (DataFrame, status_message)
    """
    try:
        file_path = Path(file_path)
        
        if not file_path.exists():
            return None, f"Error: File not found: {file_path}"
        
        # Handle ZIP files
        if file_path.suffix.lower() == ".zip":
            with tempfile.TemporaryDirectory() as temp_dir:
                with zipfile.ZipFile(file_path, 'r') as zip_ref:
                    zip_ref.extractall(temp_dir)
                
                # Look for data files in the extracted contents
                temp_path = Path(temp_dir)
                gpx_files = sorted(temp_path.glob("**/*.gpx"), key=lambda p: p.name.lower())
                csv_files = sorted(temp_path.glob("**/*.csv"), key=lambda p: p.name.lower())
                xlsx_files = sorted(temp_path.glob("**/*.xlsx"), key=lambda p: p.name.lower())
                xls_files = sorted(temp_path.glob("**/*.xls"), key=lambda p: p.name.lower())
                json_files = sorted(temp_path.glob("**/*.json"), key=lambda p: p.name.lower())

                # Geocaching exports can include both "<name>.gpx" and "<name>-wpts.gpx".
                # Prefer the main GPX (without -wpts) to get the full cache set.
                primary_gpx = [p for p in gpx_files if "-wpts" not in p.stem.lower()]
                preferred_gpx = primary_gpx if primary_gpx else gpx_files

                data_files = preferred_gpx + csv_files + xlsx_files + xls_files + json_files
                
                if not data_files:
                    return None, (
                        f"Error: No GPX, CSV, Excel, or JSON files found in {file_path.name}"
                    )
                
                # Load the first data file found
                data_file = data_files[0]
                df, msg = load_data_file(str(data_file))
                return df, f"Extracted and loaded from ZIP: {data_file.name}\n{msg}"

        # Handle GPX files via GPSBabel
        elif file_path.suffix.lower() == ".gpx":
            return _load_gpx_with_gpsbabel(file_path)
        
        # Handle CSV files
        elif file_path.suffix.lower() == ".csv":
            df = pd.read_csv(file_path)
            return df, f"Successfully loaded CSV: {file_path.name}\nRows: {len(df)}, Columns: {len(df.columns)}"
        
        # Handle Excel files
        elif file_path.suffix.lower() in [".xlsx", ".xls"]:
            df = pd.read_excel(file_path)
            return df, f"Successfully loaded Excel: {file_path.name}\nRows: {len(df)}, Columns: {len(df.columns)}"
        
        # Handle JSON files
        elif file_path.suffix.lower() == ".json":
            df = pd.read_json(file_path)
            return df, f"Successfully loaded JSON: {file_path.name}\nRows: {len(df)}, Columns: {len(df.columns)}"
        
        else:
            return None, (
                f"Error: Unsupported file type: {file_path.suffix}\n"
                "Supported types: GPX, CSV, XLSX, XLS, JSON, ZIP"
            )
    
    except Exception as e:
        logger.error(f"Error loading data file: {str(e)}")
        return None, f"Error loading file: {str(e)}"


def main(page: ft.Page):
    page.title = "COMPaSS - Cache Owner Management Platform and Sites System"
    page.padding = 20
    page.window.width = 1050
    page.window.height = 900
    page.scroll = ft.ScrollMode.AUTO

    storage = PersistentStorage()
    logger.info("COMPaSS application started")

    # ------------------------------------------------------------------ helpers

    def add_log_message(text: str):
        """Prepend a timestamped line to the log output field."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        existing = log_output.value or ""
        log_output.value = f"[{timestamp}] {text}\n{existing}"
        page.update()

    def update_status(message: str, is_error: bool = False):
        """Update the status text field."""
        status_text.value = message
        status_text.color = ft.Colors.RED_700 if is_error else ft.Colors.BLACK
        add_log_message(message)
        page.update()

    def on_copy_status_click(e):
        """Copy status text to clipboard."""
        if status_text.value:
            page.set_clipboard(status_text.value)
            add_log_message("Status copied to clipboard")

    def on_copy_log_click(e):
        """Copy log output to clipboard."""
        if log_output.value:
            page.set_clipboard(log_output.value)
            add_log_message("Log output copied to clipboard")

    def on_clear_log_click(e):
        """Clear the log output."""
        log_output.value = ""
        page.update()
        logger.info("Log cleared")

    # ------------------------------------------------------------------ UI state

    current_directory = None
    input_dir = storage.get_ui_state("last_input_dir")
    if input_dir and Path(input_dir).exists():
        current_directory = Path(input_dir)

    dirs_expanded = True

    # ------------------------------------------------------------------ directory selection

    def on_input_dir_result(e: ft.FilePickerResultEvent):
        nonlocal current_directory
        if e.path:
            current_directory = Path(e.path)
            input_dir_field.value = str(current_directory)
            storage.set_ui_state("last_input_dir", str(current_directory))
            update_status(f"Input directory set: {current_directory.name}")
            page.update()

    def on_output_dir_result(e: ft.FilePickerResultEvent):
        if e.path:
            output_dir_field.value = e.path
            storage.set_ui_state("last_output_dir", e.path)
            try:
                settings_path = ensure_app_settings_file(e.path)
                add_log_message(f"Settings file ready: {settings_path.name}")
            except Exception as ex:
                add_log_message(f"Warning: Could not prepare settings file: {str(ex)}")
            update_status(f"Output directory set: {Path(e.path).name}")
            page.update()

    def on_file_result(e: ft.FilePickerResultEvent):
        if e.files and len(e.files) > 0:
            file_path = e.files[0].path
            file_field.value = file_path
            storage.set_ui_state("last_file", file_path)
            update_status(f"File selected: {Path(file_path).name}")
            page.update()

    input_dir_picker = ft.FilePicker(on_result=on_input_dir_result)
    output_dir_picker = ft.FilePicker(on_result=on_output_dir_result)
    file_picker = ft.FilePicker(on_result=on_file_result)

    page.overlay.extend([input_dir_picker, output_dir_picker, file_picker])

    # ------------------------------------------------------------------ function implementations

    def on_function_0_app_settings(e):
        """Function 0: Open and edit app settings in working directory."""
        storage.record_function_usage("Function 0")

        working_dir = output_dir_field.value
        if not working_dir:
            update_status("Error: Please select a Working/Output Directory first", is_error=True)
            return

        settings, load_error = load_app_settings(working_dir)
        if load_error:
            update_status(load_error, is_error=True)
            return

        settings_path = get_app_settings_path(working_dir)
        auto_save_field = ft.TextField(
            label="auto_save_loaded_table",
            value=str(settings.get("auto_save_loaded_table", False)).lower(),
            hint_text="true or false",
            width=320,
        )
        auto_save_format_field = ft.TextField(
            label="auto_save_format",
            value=str(settings.get("auto_save_format", "csv")).lower(),
            hint_text="csv or json",
            width=320,
        )
        project_gc_login_url_field = ft.TextField(
            label="project_gc_login_url",
            value=str(settings.get("project_gc_login_url", PROJECT_GC_LOGIN_URL_DEFAULT)),
            hint_text="https://project-gc.com/...",
            width=660,
        )
        project_gc_username_field = ft.TextField(
            label="project_gc_username",
            value=str(settings.get("project_gc_username", PROJECT_GC_USERNAME_DEFAULT)),
            hint_text="project-gc username",
            width=320,
        )
        project_gc_password_field = ft.TextField(
            label="project_gc_password",
            value=str(settings.get("project_gc_password", PROJECT_GC_PASSWORD_DEFAULT)),
            hint_text="project-gc password",
            password=True,
            can_reveal_password=True,
            width=320,
        )

        settings_path_text = ft.Text(
            f"Settings file: {settings_path}",
            size=12,
            color=ft.Colors.GREY_700,
            selectable=True,
        )

        def close_dialog(evt):
            settings_dialog.open = False
            page.update()

        def save_settings_click(evt):
            parsed_auto_save = parse_bool_text(auto_save_field.value)
            if parsed_auto_save is None:
                update_status(
                    "Error: auto_save_loaded_table must be true/false (or yes/no, 1/0)",
                    is_error=True,
                )
                return

            parsed_auto_save_format = parse_auto_save_format(auto_save_format_field.value)
            if parsed_auto_save_format is None:
                update_status(
                    "Error: auto_save_format must be csv or json",
                    is_error=True,
                )
                return

            new_settings = {
                "auto_save_loaded_table": parsed_auto_save,
                "auto_save_format": parsed_auto_save_format,
                "project_gc_login_url": (project_gc_login_url_field.value or "").strip()
                or PROJECT_GC_LOGIN_URL_DEFAULT,
                "project_gc_username": (project_gc_username_field.value or "").strip()
                or PROJECT_GC_USERNAME_DEFAULT,
                "project_gc_password": project_gc_password_field.value
                or PROJECT_GC_PASSWORD_DEFAULT,
            }
            ok, save_result = save_app_settings(working_dir, new_settings)
            if not ok:
                update_status(save_result, is_error=True)
                return

            add_log_message(f"Settings saved: {save_result}")
            update_status("Application settings updated")
            settings_dialog.open = False
            page.update()

        settings_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Function 0: App Settings", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    controls=[
                        ft.Text(
                            "Edit app settings and save them to the working directory.",
                            size=13,
                        ),
                        settings_path_text,
                        ft.Container(height=8),
                        auto_save_field,
                        auto_save_format_field,
                        project_gc_login_url_field,
                        ft.Row(
                            controls=[
                                project_gc_username_field,
                                project_gc_password_field,
                            ]
                        ),
                    ],
                    tight=True,
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=700,
                height=360,
            ),
            actions=[
                ft.TextButton("Save", on_click=save_settings_click),
                ft.TextButton("Cancel", on_click=close_dialog),
            ],
        )

        page.overlay.append(settings_dialog)
        settings_dialog.open = True
        page.update()

    def on_function_1_load_data(e):
        """Function 1: Load data from file into Pandas DataFrame."""
        global current_dataframe, dataframe_filename
        storage.record_function_usage("Function 1")

        if not file_field.value:
            update_status(
                "Error: Please select a data file first (GPX, CSV, Excel, JSON, or ZIP)",
                is_error=True,
            )
            return

        file_path = file_field.value
        df, status_msg = load_data_file(file_path)

        if df is None:
            update_status(status_msg, is_error=True)
            logger.error(f"Function 1: Failed to load - {status_msg}")
            return

        current_dataframe = df
        dataframe_filename = Path(file_path).name

        if output_dir_field.value:
            settings, load_error = load_app_settings(output_dir_field.value)
            if load_error:
                add_log_message(load_error)
            if settings.get("auto_save_loaded_table", False):
                try:
                    output_path = Path(output_dir_field.value)
                    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                    auto_save_format = settings.get("auto_save_format", "csv").lower()
                    if auto_save_format not in ["csv", "json"]:
                        auto_save_format = "csv"

                    save_name = (
                        f"{dataframe_filename.rsplit('.', 1)[0]}_autosave_{timestamp}."
                        f"{auto_save_format}"
                    )
                    save_file = output_path / save_name
                    if auto_save_format == "json":
                        current_dataframe.to_json(save_file, orient="records", indent=2)
                    else:
                        current_dataframe.to_csv(save_file, index=False)
                    add_log_message(f"Auto-saved loaded data to {save_file.name}")
                except Exception as ex:
                    add_log_message(f"Auto-save failed: {str(ex)}")

        # Create a summary display of the dataframe
        summary_text = f"✓ Data Loaded Successfully\n\n"
        summary_text += f"File: {dataframe_filename}\n"
        summary_text += f"Rows: {len(df)}\n"
        summary_text += f"Columns: {len(df.columns)}\n\n"
        summary_text += "Column Names:\n"
        summary_text += "\n".join(f"  • {col}" for col in df.columns)
        summary_text += f"\n\nFirst few rows preview:\n"
        summary_text += df.head(5).to_string()

        def close_dialog(e):
            dialog.open = False
            page.update()

        def save_loaded_data(e):
            if not output_dir_field.value:
                add_log_message("Note: Set output directory to save the loaded data")
                return
            try:
                output_path = Path(output_dir_field.value)
                save_name = dataframe_filename.rsplit(".", 1)[0] + "_loaded.csv"
                save_file = output_path / save_name
                current_dataframe.to_csv(save_file, index=False)
                update_status(f"Data saved to: {save_file.name}")
                add_log_message(f"Saved loaded data to {save_file.name}")
            except Exception as ex:
                update_status(f"Error saving data: {str(ex)}", is_error=True)

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Function 1: Load Data", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(summary_text, selectable=True, size=11),
                ], scroll=ft.ScrollMode.AUTO),
                width=700,
                height=500,
            ),
            actions=[
                ft.TextButton("Save as CSV", on_click=save_loaded_data),
                ft.TextButton("Close", on_click=close_dialog),
            ],
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

        update_status(f"✓ Loaded data: {len(df)} rows, {len(df.columns)} columns")
        logger.info(f"Function 1: Loaded data from {dataframe_filename} - {len(df)} rows, {len(df.columns)} columns")

    def on_function_2_count_files(e):
        """Function 2: Count files by extension."""
        storage.record_function_usage("Function 2")

        if not current_directory or not current_directory.exists():
            update_status("Error: Please select an input directory first", is_error=True)
            return

        ext_counts = {}
        for file_path in current_directory.glob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower() or "(no extension)"
                ext_counts[ext] = ext_counts.get(ext, 0) + 1

        result_text = f"File count by extension in {current_directory.name}:\n\n"
        if ext_counts:
            for ext, count in sorted(ext_counts.items(), key=lambda x: x[1], reverse=True):
                result_text += f"• {ext}: {count}\n"
        else:
            result_text += "(No files found)"

        def close_dialog(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Function 2: Count Files by Extension"),
            content=ft.Container(
                content=ft.Text(result_text, selectable=True),
                width=600,
                height=400,
            ),
            actions=[ft.TextButton("Close", on_click=close_dialog)],
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

        total = sum(ext_counts.values())
        update_status(f"Counted {total} file(s) across {len(ext_counts)} extension(s)")
        logger.info(f"Function 2: Counted files by extension in {current_directory}")

    def on_function_3_system_info(e):
        """Function 3: Display system information."""
        storage.record_function_usage("Function 3")

        info_lines = [
            f"Hostname: {socket.gethostname()}",
            f"OS: {platform.system()} {platform.release()}",
            f"Machine: {platform.machine()}",
            f"Python: {platform.python_version()}",
            f"User: {getpass.getuser()}",
            f"Data Directory: {DATA_DIR}",
        ]

        result_text = "System Information:\n\n" + "\n".join(f"• {line}" for line in info_lines)

        def close_dialog(e):
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text("Function 3: System Info"),
            content=ft.Container(
                content=ft.Text(result_text, selectable=True),
                width=600,
                height=300,
            ),
            actions=[ft.TextButton("Close", on_click=close_dialog)],
        )

        page.overlay.append(dialog)
        dialog.open = True
        page.update()

        update_status("Displayed system information")
        logger.info("Function 3: Displayed system information")

    # ------------------------------------------------------------------ function management

    active_functions = [
        "function_0_app_settings",
        "function_1_list_files",
        "function_2_count_files",
        "function_3_system_info",
    ]

    functions = {
        "function_0_app_settings": {
            "label": "0: App Settings",
            "icon": "⚙️",
            "handler": on_function_0_app_settings,
            "help_file": "FUNCTION_0_APP_SETTINGS.md"
        },
        "function_1_list_files": {
            "label": "1: Load Data File",
            "icon": "📊",
            "handler": on_function_1_load_data,
            "help_file": "FUNCTION_1_LOAD_DATA.md"
        },
        "function_2_count_files": {
            "label": "2: Count Files by Extension",
            "icon": "📊",
            "handler": on_function_2_count_files,
            "help_file": "FUNCTION_2_COUNT_FILES.md"
        },
        "function_3_system_info": {
            "label": "3: System Information",
            "icon": "💻",
            "handler": on_function_3_system_info,
            "help_file": "FUNCTION_3_SYSTEM_INFO.md"
        },
    }

    help_mode_enabled = ft.Ref[ft.Checkbox]()

    def show_help_dialog(function_key):
        """Display the help markdown file for a function"""
        if function_key not in functions:
            return

        func_info = functions[function_key]
        help_file = func_info.get("help_file")
        display_label = func_info['label']

        if not help_file:
            add_log_message(f"No help file available for {display_label}")
            return

        markdown_content = load_help_document(help_file)
        add_log_message(f"Displaying help for: {display_label}")

        def close_help_dialog(e):
            help_dialog.open = False
            page.update()

        def copy_help(e):
            page.set_clipboard(markdown_content)
            add_log_message("Help content copied to clipboard")

        help_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Text(f"Function {display_label}", weight=ft.FontWeight.BOLD),
            content=ft.Container(
                content=ft.Column(
                    [
                        ft.Markdown(
                            markdown_content,
                            selectable=True,
                            extension_set=ft.MarkdownExtensionSet.GITHUB_WEB,
                        ),
                    ],
                    scroll=ft.ScrollMode.AUTO,
                ),
                width=700,
                height=500,
            ),
            actions=[
                ft.TextButton("Copy to Clipboard", on_click=copy_help),
                ft.TextButton("Close", on_click=close_help_dialog),
            ],
        )

        page.overlay.append(help_dialog)
        help_dialog.open = True
        page.update()

    def execute_selected_function(function_key):
        """Execute or show help for the selected function."""
        if not function_key or function_key not in functions:
            return

        if help_mode_enabled.current and help_mode_enabled.current.value:
            show_help_dialog(function_key)
        else:
            func_info = functions[function_key]
            handler = func_info.get("handler")
            if handler:
                logger.info(f"Executing {func_info['label']}")
                handler(None)

        active_function_dropdown.value = None
        page.update()

    def get_sorted_function_options(function_list):
        """Return dropdown options sorted by numeric prefix in each function label."""
        sortable = []
        for func_key in function_list:
            if func_key in functions:
                f = functions[func_key]
                label = f.get("label", "")
                try:
                    number = int(label.split(":", 1)[0].strip())
                except Exception:
                    number = 999
                sortable.append((number, func_key, f))

        sortable.sort(key=lambda item: (item[0], item[2].get("label", "")))

        return [
            ft.dropdown.Option(
                key=func_key,
                text=f"{f.get('icon', '')} {f.get('label', func_key)}".strip(),
            )
            for _, func_key, f in sortable
        ]

    # ------------------------------------------------------------------ UI fields

    input_dir_field = ft.TextField(
        label="Input Directory",
        value=storage.get_ui_state("last_input_dir"),
        read_only=True,
        expand=True,
    )

    output_dir_field = ft.TextField(
        label="Working/Output Directory",
        value=storage.get_ui_state("last_output_dir"),
        read_only=True,
        expand=True,
    )

    if output_dir_field.value and Path(output_dir_field.value).exists():
        try:
            ensure_app_settings_file(output_dir_field.value)
        except Exception as ex:
            add_log_message(f"Warning: Could not prepare settings file at startup: {str(ex)}")

    file_field = ft.TextField(
        label="Select File",
        value=storage.get_ui_state("last_file"),
        read_only=True,
        expand=True,
    )

    status_text = ft.TextField(
        value="Ready",
        multiline=True,
        min_lines=2,
        max_lines=3,
        read_only=True,
    )

    log_output = ft.TextField(
        value="",
        multiline=True,
        min_lines=8,
        max_lines=8,
        read_only=True,
    )

    def toggle_dirs(e):
        nonlocal dirs_expanded
        dirs_expanded = not dirs_expanded
        dirs_toggle_button.icon = (
            ft.Icons.EXPAND_LESS if dirs_expanded else ft.Icons.EXPAND_MORE
        )
        inputs_inner_column.visible = dirs_expanded
        page.update()

    dirs_toggle_button = ft.IconButton(
        icon=ft.Icons.EXPAND_LESS,
        tooltip="Collapse/Expand directories section",
        on_click=toggle_dirs,
    )

    inputs_inner_column = ft.Column(
        controls=[
            ft.Row(
                controls=[
                    input_dir_field,
                    ft.ElevatedButton(
                        "Browse...",
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=lambda _: input_dir_picker.get_directory_path(
                            dialog_title="Select Input Directory"
                        ),
                    ),
                ],
            ),
            ft.Container(height=5),
            ft.Row(
                controls=[
                    output_dir_field,
                    ft.ElevatedButton(
                        "Browse...",
                        icon=ft.Icons.FOLDER_OPEN,
                        on_click=lambda _: output_dir_picker.get_directory_path(
                            dialog_title="Select Working/Output Directory"
                        ),
                    ),
                ],
            ),
        ],
        visible=True,
    )

    # ------------------------------------------------------------------ layout

    page.add(
        ft.Column(
            controls=[
                # ---- Title
                ft.Row([
                    ft.Icon(ft.Icons.EXPLORE, size=28, color=ft.Colors.BLUE_700),
                    ft.Text(
                        "COMPaSS — Cache Owner Management Platform and Sites System",
                        size=24,
                        weight=ft.FontWeight.BOLD,
                    ),
                ], spacing=10),
                ft.Text(
                    "Cache Owner Management Platform and Sites System",
                    size=13,
                    color=ft.Colors.GREY_700,
                    italic=True,
                ),
                ft.Divider(height=5),

                # ---- Directories section (collapsible)
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Directories",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    dirs_toggle_button,
                                ],
                            ),
                            inputs_inner_column,
                        ],
                        spacing=5,
                    ),
                    padding=5,
                ),

                ft.Divider(height=5),

                # ---- File Selection
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Text(
                                "File Selection",
                                size=18,
                                weight=ft.FontWeight.BOLD,
                            ),
                            ft.Row(
                                controls=[
                                    file_field,
                                    ft.ElevatedButton(
                                        "Browse...",
                                        icon=ft.Icons.FILE_OPEN,
                                        on_click=lambda _: file_picker.pick_files(
                                            dialog_title="Select File",
                                            allow_multiple=False,
                                        ),
                                    ),
                                ],
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=5,
                ),

                ft.Divider(height=5),

                # ---- Functions
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Column(
                                        controls=[
                                            ft.Text(
                                                "Functions",
                                                size=18,
                                                weight=ft.FontWeight.BOLD,
                                            ),
                                            ft.Text(
                                                "Select and execute workflow functions",
                                                size=12,
                                                italic=True,
                                                color=ft.Colors.GREY_700,
                                            ),
                                            ft.Container(height=5),
                                            active_function_dropdown := ft.Dropdown(
                                                label="Select Function to Execute",
                                                hint_text="Choose a function",
                                                width=500,
                                                options=[],
                                                on_change=lambda e: execute_selected_function(
                                                    e.control.value
                                                ),
                                            ),
                                            ft.Container(height=5),
                                            ft.Checkbox(
                                                label="Help Mode",
                                                ref=help_mode_enabled,
                                                tooltip="Enable to view help documentation for functions instead of executing them",
                                            ),
                                        ],
                                        spacing=5,
                                    ),
                                ],
                                vertical_alignment=ft.CrossAxisAlignment.START,
                            ),
                        ],
                        spacing=5,
                    ),
                    padding=5,
                ),

                ft.Divider(height=5),

                # ---- Status
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Status",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.COPY,
                                        tooltip="Copy status to clipboard",
                                        on_click=on_copy_status_click,
                                        icon_size=20,
                                    ),
                                ],
                            ),
                            status_text,
                        ],
                        spacing=5,
                    ),
                    padding=5,
                ),

                ft.Divider(height=5),

                # ---- Log output
                ft.Container(
                    content=ft.Column(
                        controls=[
                            ft.Row(
                                controls=[
                                    ft.Text(
                                        "Log Output",
                                        size=18,
                                        weight=ft.FontWeight.BOLD,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.DELETE_SWEEP,
                                        tooltip="Clear log",
                                        on_click=on_clear_log_click,
                                        icon_size=20,
                                    ),
                                    ft.IconButton(
                                        icon=ft.Icons.COPY,
                                        tooltip="Copy log to clipboard",
                                        on_click=on_copy_log_click,
                                        icon_size=20,
                                    ),
                                ],
                            ),
                            log_output,
                        ],
                        spacing=5,
                    ),
                    padding=5,
                ),
            ],
            spacing=5,
        )
    )

    # Initialize function dropdown
    # Build from the function registry to avoid missing options if the active list drifts.
    registered_function_keys = [k for k in active_functions if k in functions]
    for func_key in functions:
        if func_key not in registered_function_keys:
            registered_function_keys.append(func_key)

    active_function_dropdown.options = get_sorted_function_options(registered_function_keys)
    page.update()

    logger.info("UI initialised successfully")
    add_log_message("COMPaSS application ready. Select a function to begin.")


if __name__ == "__main__":
    logger.info("Application starting…")
    ft.app(target=main)
