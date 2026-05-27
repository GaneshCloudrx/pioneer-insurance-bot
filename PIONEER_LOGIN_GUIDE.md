# Pioneer Login Module - Quick Guide

## Overview

The `modules/login.py` module provides complete Pioneer application automation for login and setup.

## Quick Start

### 1. Simple Login

```python
from modules import login

# Login to Pioneer
app, main_win = login.login_pioneer(
    app_path=r"C:\Path\To\PioneerRx.lnk",
    username="your_username",
    password="your_pin"
)

if app and main_win:
    print("Login successful!")
    # Your automation here
    login.close_pioneer(app)
```

### 2. With Framework (Recommended)

```python
from modules.base_automation import BaseAutomation
from modules import login

PIONEER_PATH = r"C:\Path\To\PioneerRx.lnk"
USERNAME = "username"
PASSWORD = "pin"

def my_automation(automation):
    automation.log("Logging into Pioneer...")
    app, main_win = login.login_pioneer(PIONEER_PATH, USERNAME, PASSWORD)
    
    if app and main_win:
        automation.log("✓ Login successful!")
        # Your automation logic here
        login.close_pioneer(app)

automation = BaseAutomation()
automation.run_with_framework(my_automation)
```

## Available Functions

### `login_pioneer(app_path, username, password, change_mode=True)`

Complete login workflow - **recommended for most use cases**.

**Parameters:**
- `app_path`: Path to PioneerRx.lnk or PioneerPharmacy.exe
- `username`: Pioneer username
- `password`: Pioneer password/PIN
- `change_mode`: Whether to switch to Single mode (default: True)

**Returns:**
- `(app, main_win)` if successful
- `(None, None)` if failed

**Example:**
```python
app, main_win = login.login_pioneer(
    r"C:\Pioneer\PioneerRx.lnk",
    "jdoe",
    "1234"
)
```

### `kill_pioneer()`

Kill any running Pioneer processes.

**Returns:** `bool` - True if processes were killed

**Example:**
```python
from modules import login

login.kill_pioneer()
```

### `launch_pioneer(app_path)`

Launch Pioneer application without logging in.

**Parameters:**
- `app_path`: Path to application

**Returns:** `Application` object or `None`

**Example:**
```python
app = login.launch_pioneer(r"C:\Pioneer\PioneerRx.lnk")
```

### `login(app, username, password)`

Perform login on already-launched application.

**Parameters:**
- `app`: pywinauto Application object
- `username`: Pioneer username
- `password`: Pioneer password/PIN

**Returns:** `bool` - True if successful

**Example:**
```python
app = login.launch_pioneer(PIONEER_PATH)
if login.login(app, "jdoe", "1234"):
    print("Login successful!")
```

### `close_pioneer(app=None)`

Close Pioneer application gracefully.

**Parameters:**
- `app`: Application object (optional)

**Returns:** `bool` - True if closed successfully

**Example:**
```python
login.close_pioneer(app)
```

## Login Workflow Steps

The `login_pioneer()` function performs these steps automatically:

1. **Kill existing processes** - Ensures clean start
2. **Launch application** - Starts Pioneer
3. **Login** - Enters username and password
4. **Handle dialogs** - Dismisses timezone warnings, etc.
5. **Wait for main window** - Waits until ready
6. **Change to Single mode** - Switches from Shared if needed
7. **Activate main view** - Clicks side pane to activate

## Configuration

### Option 1: Environment Variables (Recommended)

```python
import os

PIONEER_PATH = os.environ.get('PIONEER_PATH', r"C:\Default\Path\PioneerRx.lnk")
USERNAME = os.environ.get('PIONEER_USERNAME', 'default_user')
PASSWORD = os.environ.get('PIONEER_PASSWORD', 'default_pin')
```

### Option 2: Config File

```python
# In config.py
PIONEER_PATH = r"C:\Path\To\PioneerRx.lnk"
PIONEER_USERNAME = "your_username"
PIONEER_PASSWORD = "your_pin"

# In your script
import config

app, main_win = login.login_pioneer(
    config.PIONEER_PATH,
    config.PIONEER_USERNAME,
    config.PIONEER_PASSWORD
)
```

### Option 3: Direct (Testing Only)

```python
app, main_win = login.login_pioneer(
    r"C:\Pioneer\PioneerRx.lnk",
    "testuser",
    "1234"
)
```

## Error Handling

The module automatically:
- ✅ Logs all steps using `helper.log_print()`
- ✅ Takes screenshots on failures
- ✅ Handles optional dialogs gracefully
- ✅ Returns `None` values on failure (easy to check)

**Example with error handling:**

```python
from modules import login
from modules.base_automation import BaseAutomation

def safe_automation(automation):
    app, main_win = login.login_pioneer(PIONEER_PATH, USERNAME, PASSWORD)
    
    if not app:
        automation.log("❌ Login failed - aborting")
        return False
    
    try:
        # Your automation here
        automation.log("Performing tasks...")
        
    except Exception as e:
        automation.log(f"❌ Error: {e}")
        automation.take_screenshot("error")
        return False
        
    finally:
        login.close_pioneer(app)
    
    return True

automation = BaseAutomation()
automation.run_with_framework(safe_automation)
```

## Advanced Usage

### Skip Mode Change

If you don't want to change to Single mode:

```python
app, main_win = login.login_pioneer(
    PIONEER_PATH,
    USERNAME,
    PASSWORD,
    change_mode=False  # Stay in current mode
)
```

### Manual Step-by-Step

For custom workflows:

```python
from modules import login

# Kill existing
login.kill_pioneer()

# Launch
app = login.launch_pioneer(PIONEER_PATH)

# Login
login.login(app, USERNAME, PASSWORD)

# Handle dialogs
login.handle_dialogs(app)

# Get main window
main_win = login.wait_for_main_window(app)

# Change mode (optional)
login.change_to_single_mode(app, main_win, PASSWORD)

# Activate view
login.activate_main_view(main_win)

# Your automation here...

# Close
login.close_pioneer(app)
```

## Common Use Cases

### Use Case 1: Daily Data Entry

```python
def daily_data_entry(automation):
    automation.log("Starting daily data entry...")
    
    app, main_win = login.login_pioneer(PIONEER_PATH, USERNAME, PASSWORD)
    if not app:
        return
    
    try:
        # Enter data
        # Navigate screens
        # Save records
        pass
    finally:
        login.close_pioneer(app)

automation = BaseAutomation()
automation.run_with_framework(daily_data_entry)
```

### Use Case 2: Continuous Processing

```python
from modules.base_automation import ContinuousAutomation

def fetch_work_items():
    # Fetch from API/database
    return items if items else None

def process_items(items):
    app, main_win = login.login_pioneer(PIONEER_PATH, USERNAME, PASSWORD)
    if not app:
        return
    
    try:
        for item in items:
            # Process each item in Pioneer
            pass
    finally:
        login.close_pioneer(app)

automation = ContinuousAutomation()
automation.set_data_fetcher(fetch_work_items)
automation.set_processor(process_items)
automation.run_continuous()
```

### Use Case 3: Multiple Sessions

```python
def multi_session_automation(automation):
    """Process different users/clinics"""
    
    users = [
        ("user1", "pin1"),
        ("user2", "pin2"),
        ("user3", "pin3")
    ]
    
    for username, password in users:
        automation.log(f"Processing as {username}...")
        
        app, main_win = login.login_pioneer(PIONEER_PATH, username, password)
        if not app:
            continue
        
        try:
            # Automation for this user
            automation.take_screenshot(f"{username}_complete")
        finally:
            login.close_pioneer(app)
            time.sleep(2)  # Brief pause between sessions
```

## Troubleshooting

### Issue: "Process not found"

**Solution:** Update `PIONEER_PATH` to correct location

```python
# Try full executable path instead of .lnk
PIONEER_PATH = r"C:\Program Files\PioneerRx\PioneerPharmacy.exe"
```

### Issue: Login window not found

**Solution:** Increase wait time

```python
# In login.py, modify launch_pioneer():
time.sleep(10)  # Instead of 5
```

### Issue: Mode change fails

**Solution:** Skip mode change or handle manually

```python
# Option 1: Skip it
app, main_win = login.login_pioneer(..., change_mode=False)

# Option 2: Handle failure gracefully (module already does this)
```

### Issue: Dialogs not handled

**Solution:** Add custom dialog handling

```python
def my_custom_dialogs(app):
    try:
        # Handle your specific dialog
        dialog = app.window(title="Your Dialog")
        dialog.child_window(title="OK").click()
    except:
        pass

# After login
app, main_win = login.login_pioneer(...)
my_custom_dialogs(app)
```

## Requirements

- `pywinauto` - Windows application automation
- `psutil` - Process management
- Framework's `helper` module - Logging and screenshots

Install:
```bash
pip install pywinauto psutil
```

## Testing

Test the login module:

```bash
# Edit login.py and set TEST_* variables at bottom
python modules\login.py
```

Or test with framework:

```bash
python pioneer_automation_example.py
```

## Tips

1. **Always close Pioneer** - Use `try/finally` to ensure cleanup
2. **Check return values** - `None` means failure
3. **Use framework** - Automatic recording, logging, error handling
4. **Take screenshots** - At key steps for debugging
5. **Test incrementally** - Test login first, then add automation

## Examples

See these files for complete examples:
- `pioneer_automation_example.py` - Basic usage with framework
- `modules/login.py` - Test code at bottom of file
- `main.py` - Framework patterns

---

**Ready to automate Pioneer! 🚀**
