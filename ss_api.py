import os, logging
from typing import Dict
import httpx, truststore, ssl
from pathlib import Path
from urllib.parse import urlencode


class APIException(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


def list_sheets(*, access_token=None) -> None | Dict:
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client:
            params = urlencode({"includeAll": "true"})
            url = f"https://api.smartsheet.com/2.0/sheets?{params}"
            headers = {
                "Authorization": f"Bearer {bearer}",
            }
            logging.info(f"GET: list sheets, {url},{headers}")
            response = client.get(
                url=url,
                headers=headers,
                timeout=60,
            )
            if response.status_code != 200:
                raise APIException(f"GET: list sheets, {url},{headers}", response)
            return response.json()
    except APIException as e:
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")

    return None

#new get_sheet method to handle 404
def get_sheet(sheet_id, last_modified=None, *, access_token=None) -> None | Dict:
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client:
            url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
            if last_modified:
                params = urlencode({"rowsModifiedSince": last_modified})
                url += f"?{params}"
            headers = {
                "Authorization": f"Bearer {bearer}",
            }
            logging.info(f"GET: get sheet, {url},{headers}")
            response = client.get(
                url=url,
                headers=headers,
                timeout=60,
            )
            if response.status_code == 404:
                # Sheet does not exist, return None
                return None
            if response.status_code != 200:
                # Handle other errors
                raise APIException(f"GET: get sheet, {url},{headers}", response)
            return response.json()
    except APIException as e:
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")

    return None


def get_sheet_as_excel(sheet_id, filepath, *, access_token=None, folder_id=None):
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client:
            # Modify the URL to include the folder ID if provided
            if folder_id:
                url = f"https://api.smartsheet.com/2.0/folders/{folder_id}/sheets/{sheet_id}"
            else:
                url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
            
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Accept": "application/vnd.ms-excel",
            }
            
            response = client.get(
                url=url,
                headers=headers,
                timeout=60,
            )
            if response.status_code != 200:
                raise APIException(f"GET: get sheet, {url},{headers}", response)
            
            with open(filepath, "wb") as f:
                f.write(response.content)
            print(f"File saved as {filepath}")
            if response.headers.get('Content-Type') == 'application/json':
                return response.json()
    except APIException as e:
        
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")

    return None



def update_sheet(sheet_id, updates, *, access_token=None):
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        sheet = get_sheet(sheet_id, access_token=bearer)
        if not sheet or not sheet["rows"]:
            return

        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client:
            url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/rows"
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json",
            }

            batch = 500
            for i in range(0, len(updates), batch):
                response = client.put(
                    url=url,
                    headers=headers,
                    json=updates[i : i + batch],
                    timeout=60,
                )
                if response.status_code != 200:
                    raise APIException(f"PUT: update rows, {url},{headers}", response)
    except APIException as e:
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")


def move_rows(target_sheet_id, source_sheet_id, *, access_token=None):
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        source_sheet = get_sheet(source_sheet_id, access_token=bearer)
        rows = []
        if not source_sheet:
            return
        for row in source_sheet["rows"]:
            rows.append(row["id"])

        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client:
            url = f"https://api.smartsheet.com/2.0/sheets/{source_sheet_id}/rows/move"
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/json",
            }

            batch = 200
            for i in range(0, len(rows), batch):
                response = client.post(
                    url=url,
                    headers=headers,
                    json={
                        "rowIds": rows[i : i + batch],
                        "to": {"sheetId": target_sheet_id},
                    },
                    timeout=120,
                )
                if response.status_code != 200:
                    raise APIException(
                        f"POST: move all rows, {url},{headers}", response
                    )
    except APIException as e:
        
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")


def delete_rows(sheet_id, rows, *, access_token=None):
    try:
        responses = []
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client:
            batch_size = 100
            for i in range(0, len(rows), batch_size):
                batch = ",".join(str(row) for row in rows[i : i + batch_size])
                url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/rows?ids={batch}&ignoreRowsNotFound=true"
                headers = {
                    "Authorization": f"Bearer {bearer}",
                }
                response = client.delete(
                    url=url,
                    headers=headers,
                    timeout=60,
                )
                responses.append(response)
                if response.status_code != 200:
                    raise APIException(
                        f"DELETE: delete rows, {url},{headers}", response
                    )
            return responses
    except APIException as e:
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")
    return None


def delete_sheet(sheet_id, *, access_token=None):
    bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
    ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
    with httpx.Client(verify=ssl_context) as client:
        try:
            url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
            headers = {
                "Authorization": f"Bearer {bearer}",
            }
            response = client.delete(
                url=url,
                headers=headers,
                timeout=60,
            )
            if response.status_code != 200:
                raise APIException(f"GET: get sheet, {url},{headers}", response)
            return response.json()
        except APIException as e:
            
            logging.error(f"API Error: {e.response}")
            print(f"An error occurred: {e.response}")

    return None


def clear_sheet(sheet_id, *, access_token=None):
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        sheet = get_sheet(sheet_id, access_token=bearer)
        if not sheet:
            
            exit()

        if not sheet["rows"]:
            return

        first_row_id = sheet["rows"][0]["id"]
        data = [
            {"id": row["id"], "parentId": first_row_id}
            for i, row in enumerate(sheet["rows"])
            if i > 0
        ]
        update_sheet(sheet_id, data, access_token=bearer)
        delete_rows(sheet_id, [first_row_id], access_token=bearer)
    except APIException as e:
        
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")


def import_excel(sheet_name, filepath, target_folder_id=None, *, access_token=None):
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client, open(filepath, "br") as xl:
            if target_folder_id:
                url = f"https://api.smartsheet.com/2.0/folders/{target_folder_id}/sheets/import?sheetName={sheet_name}&headerRowIndex=0&primaryColumnIndex=0"
                
            else:
                url = f"https://api.smartsheet.com/2.0/sheets/import?sheetName={sheet_name}&headerRowIndex=0&primaryColumnIndex=0"
                

            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Disposition": "attachment",
                "Content-Type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            }
            response = client.post(
                url=url,
                headers=headers,
                content=xl,
                timeout=120,
            )
            if response.status_code != 200:
                raise APIException("POST: import excel", response)
            
            return response.json()
    except APIException as e:
        
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")
    
    return None


def attach_file(sheet_id, filepath, *, access_token=None):
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client, open(filepath, "br") as xl:
            url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/attachments "
            file_size = Path(filepath).stat().st_size
            headers = {
                "Authorization": f"Bearer {bearer}",
                "Content-Type": "application/vnd.ms-excel",
                "Content-Disposition": f'attachment; filename="{os.path.basename(filepath)}"',
                "Content-Length": str(file_size),
            }
            response = client.post(
                url=url,
                headers=headers,
                content=xl,
                timeout=60,
            )
            
            if response.status_code != 200:
                raise APIException(f"POST: attach file, {url},{headers}", response)
            return response
    except APIException as e:
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")
    return None


def update_columns(sheet_id, *, access_token=None):
    try:
        bearer = access_token or os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)

        # Define the column updates
        column_updates = [
            {
                "title": "Status",
                "type": "PICKLIST",
                "options": ["Initial", "In-Work", "Issue", "Updated", "Re-Opened", "Validated", "Complete"]
            },
            {
                "title": "Created Date",
                "type": "DATE"
            },
            {
                "title": "Modified Date",
                "type": "DATE"
            }
        ]

        with httpx.Client(verify=ssl_context) as client:
            # Get the current columns to find their IDs
            url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/columns"
            headers = {
                "Authorization": f"Bearer {bearer}"
            }
            response = client.get(url=url, headers=headers, timeout=180)
            if response.status_code != 200:
                raise APIException(f"GET: get columns, {url},{headers}", response)
            
            columns = response.json()
            
            # Prepare the column updates with correct IDs
            if 'data' in columns:
                columns = columns['data']
            else:
                logging.error("Unexpected response structure: %s", columns)
                raise ValueError("Unexpected response structure from Smartsheet API.")

            # Prepare the column updates with correct IDs
            updates = []
            for col in columns:
                if isinstance(col, dict) and "title" in col:
                    for update in column_updates:
                        if col["title"] == update["title"]:
                            update["id"] = col["id"]
                            updates.append(update)
                            break

            # Update the columns
            for update in updates:
                column_id = update.pop("id")
                url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}/columns/{column_id}"
                response = client.put(url=url, headers=headers, json=update, timeout=180)
                if response.status_code != 200:
                    raise APIException(f"PUT: update column, {url},{headers}", response)

            print("Columns updated successfully.")

    except APIException as e:
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")




def test():
    pass
