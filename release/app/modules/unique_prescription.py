"""
Unique Prescription Module
Reads queue export file, adds unique strings, and claims prescription via API
"""
import os
import base64
import json
import pandas as pd
import requests
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import config
from modules.helper import log_print


def process_queue_file(file_path):
    """
    Read queue export file and add unique string for each prescription.
    
    Args:
        file_path: Path to Excel file from queue_download
    
    Returns:
        tuple: (success: bool, df_queue_table: DataFrame, row_count: int)
    """
    try:
        log_print(f"Reading file: {file_path}")
        
        # Read Excel file
        df_queue_table = pd.read_excel(file_path, engine='openpyxl')
        log_print(f"Read {len(df_queue_table)} rows from file")
        
        df_queue_table['Index'] = df_queue_table.index
        
        # Filter 1: Method should be "escript" (case insensitive)
        df_queue_table = df_queue_table[df_queue_table['Method'].astype(str).str.lower() == 'escript']
        log_print(f"After Method filter: {len(df_queue_table)} rows")
        
        # Filter 2: Locked By should be empty or null (not locked by anyone)
        # Column may be absent in some exports — skip filter if missing
        if 'Locked By' in df_queue_table.columns:
            locked_by = df_queue_table['Locked By'].astype(str).str.strip().str.lower()
            df_queue_table = df_queue_table[(locked_by == '') | (locked_by == 'nan') | (locked_by == 'none')]
            log_print(f"After Locked By filter: {len(df_queue_table)} rows")
        else:
            log_print("'Locked By' column not found in export — skipping lock filter")
        
        if len(df_queue_table) == 0:
            log_print("No valid rows after filtering")
            return True, pd.DataFrame(), 0
        
        # Rename columns
        df_queue_table = df_queue_table.rename(columns={
            'Request On': 'RequestOn',
            'Patient': 'PatientName',
            'Item': 'MedicineName',
            'Prescriber': 'Prescriber',
            'Requested Priority': 'RequestedPriority'
        })
        
        # Add uniqueString column with duplicate handling
        unique_counts = {}
        unique_strings = []
        
        for _, row in df_queue_table.iterrows():
            unique_temp = str(row['PatientName']) + str(row['MedicineName']) + str(row['RequestOn']) + str(row['Prescriber'])
            unique_temp = unique_temp.replace(' ', '') + "python_bot_prod"
            
            if unique_temp in unique_counts:
                unique_counts[unique_temp] += 1
                unique_strings.append(f"{unique_temp}_{unique_counts[unique_temp]}")
            else:
                unique_counts[unique_temp] = 1
                unique_strings.append(unique_temp)
        
        df_queue_table['uniqueString'] = unique_strings
        
        row_count = len(df_queue_table)
        log_print(f"✓ Processed {row_count} prescriptions")
        
        return True, df_queue_table, row_count
        
    except Exception as e:
        log_print(f"Failed to process file: {e}")
        return False, pd.DataFrame(), 0


def unique_prescription_from_queue_api(df_queue_table, pioneer_username, retry_file_path=None):
    """
    Loop through prescriptions and claim the first available one via API.
    
    Args:
        df_queue_table: Filtered DataFrame with uniqueString column
        pioneer_username: Bot username for claiming
        retry_file_path: Optional path to retry file (for retrying failed prescriptions)
    
    Returns:
        tuple: (success, index, unique_string, api_id, patient_name, requested_priority)
               Returns (False, -1, "Nothing", -1, "Nothing", "Nothing") if none claimed
    """
    try:
        # Default return values
        claimed_index = -1
        claimed_unique_string = "Nothing"
        claimed_api_id = -1
        claimed_patient_name = "Nothing"
        claimed_requested_priority = "Nothing"
        
        # Load retry file if exists
        retry_lines = []
        retry_check = False
        if retry_file_path and os.path.exists(retry_file_path):
            with open(retry_file_path, 'r') as f:
                retry_lines = [line.strip() for line in f.readlines()]
            retry_check = True
        
        auth_string = base64.b64encode(f"{config.PORTAL_USERNAME}:{config.PORTAL_PASSWORD}".encode()).decode()

        session = requests.Session()
        session.headers.update({
            "Content-Type": "application/json",
            "Authorization": f"Basic {auth_string}"
        })

        retry_set = set(retry_lines) if retry_check else set()

        for _, row in df_queue_table.iterrows():
            unique_string_value = str(row['uniqueString'])
            patient_name = str(row['PatientName'])
            medicine_name = str(row['MedicineName'])
            prescriber = str(row['Prescriber'])
            requested_priority = str(row['RequestedPriority'])
            
            if retry_check and unique_string_value in retry_set:
                if not unique_string_value.endswith("RETRY"):
                    unique_string_value = unique_string_value + "RETRY"
            
            body = {
                "key": unique_string_value,
                "bot_name": pioneer_username,
                "request_on": requested_priority,
                "patient_name": patient_name,
                "prescriber_name": prescriber,
                "item": medicine_name
            }
            
            response = session.post(config.API_QUEUE_ENDPOINT, json=body, timeout=10)
            
            if response.status_code == 200:
                result = response.json()
                
                if str(result.get("status", "")).upper() == "SUCCESS":
                    claimed_index = int(row['Index']) + 1
                    claimed_unique_string = unique_string_value
                    claimed_api_id = int(result["data"]["id"])
                    claimed_patient_name = patient_name
                    claimed_requested_priority = requested_priority
                    
                    log_print(f"✓ Claimed: {patient_name} | {medicine_name} | API ID: {claimed_api_id}")
                    session.close()
                    return True, claimed_index, claimed_unique_string, claimed_api_id, claimed_patient_name, claimed_requested_priority
        
        session.close()
        log_print("No prescription available to claim")
        return False, claimed_index, claimed_unique_string, claimed_api_id, claimed_patient_name, claimed_requested_priority
        
    except Exception as e:
        log_print(f"Failed to claim prescription: {e}")
        return False, -1, "Nothing", -1, "Nothing", "Nothing"


# Test
if __name__ == "__main__":
    import glob

    files = sorted(glob.glob(os.path.join(config.QUEUE_EXPORT_DIR, "*.xlsx")))
    TEST_FILE = files[-1] if files else None
    PIONEER_USER = config.PIONEER_USERNAME
    
    # Step 1: Process file
    success, df_queue_table, count = process_queue_file(TEST_FILE) if TEST_FILE else (False, pd.DataFrame(), 0)
    
    if success and count > 0:
        log_print(f"\n{count} prescriptions found, claiming from API...")
        
        # Step 2: Claim prescription
        success, index, unique_string, api_id, patient_name, priority = unique_prescription_from_queue_api(df_queue_table, PIONEER_USER)
        
        if success:
            log_print(f"\n✓ TEST PASSED")
            log_print(f"  Index: {index}")
            log_print(f"  UniqueString: {unique_string}")
            log_print(f"  API ID: {api_id}")
            log_print(f"  Patient: {patient_name}")
            log_print(f"  Priority: {priority}")
        else:
            log_print(f"\n✗ No prescription claimed")
    else:
        log_print("\n✗ No data to process")
