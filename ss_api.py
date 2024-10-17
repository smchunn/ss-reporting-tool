import smartsheet
import sys, os, logging
import httpx, truststore, ssl
import toml, openpyxl
from datetime import datetime


start_time = datetime.now()

CONFIG = None
_dir_in = os.path.join(os.path.dirname(os.path.abspath(__file__)), "in/")
_dir_out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out/")
_conf = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.toml")


class APIException(Exception):
    def __init__(self, message, response):
        super().__init__(message)
        self.response = response


def get_sheet():

    smart = smartsheet.Smartsheet()
    smart.errors_as_exceptions(True)

    if isinstance(CONFIG, dict):
        print("Starting ...")
        if "verbose" in CONFIG and CONFIG["verbose"] == True:
            logging.basicConfig(filename="sheet.log", level=logging.INFO)
        for k, v in CONFIG["tables"].items():
            table_id = v["id"]
            table_src = v["src"]
            table_name = k
            _get_sheet_as_excel(table_id, _dir_out)

            workbook = openpyxl.load_workbook(os.path.join(_dir_out, table_src))
            worksheet = workbook[table_name]
            worksheet.title = "AUDIT"
            workbook.save(os.path.join(_dir_out, table_src))


def set_sheet():
    print("Starting ...")

    if isinstance(CONFIG, dict):
        target_folder_id = CONFIG["target_folder"]
        for k, v in CONFIG["tables"].items():
            table_id = v["id"]
            table_src = v["src"]
            table_name = k
            print(f"starting {table_name}...")

            if not table_id:
                print(f"No existing table, uploading {table_src} to {table_name}")
                result = _import_excel(
                    f"{table_name}",
                    os.path.join(_dir_in, table_src),
                    target_folder_id=target_folder_id,
                )
                if result:
                    table_id = str(result["result"]["id"])
                    print(f"  {table_name}({table_id}): new table loaded")
                    CONFIG["tables"][k]["id"] = table_id
            else:
                result = _import_excel(
                    f"TMP_{table_name}", os.path.join(_dir_in, table_src)
                )
                if not result:
                    continue

                if "message" in result and result["message"] != "SUCCESS":
                    print(result["message"])
                    return

                import_sheet_id = result["result"]["id"]
                target_sheet_id = table_id

                if not import_sheet_id or not target_sheet_id:
                    continue

                # for column in target_sheet['columns']:
                #     column_map[column.title] = column.id

                _clear_sheet(target_sheet_id)
                _move_rows(target_sheet_id, import_sheet_id)
                _delete_sheet(import_sheet_id)
            print("done...")


def _get_sheet(sheet_id):
    try:
        bearer = os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client:
            url = f"https://api.smartsheet.com/2.0/sheets/{sheet_id}"
            headers = {
                "Authorization": f"Bearer {bearer}",
            }
            logging.info(f"GET: get sheet, {url},{headers}")
            response = client.get(
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


def _get_sheet_as_excel(sheet_id, filepath):
    try:
        bearer = os.environ["SMARTSHEET_ACCESS_TOKEN"]
        ssl_context = truststore.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
        with httpx.Client(verify=ssl_context) as client:
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
            return response.json()
    except APIException as e:
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")

    return None


def _update_sheet(sheet_id, updates):
    try:
        bearer = os.environ["SMARTSHEET_ACCESS_TOKEN"]
        sheet = _get_sheet(sheet_id)
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


def _move_rows(target_sheet_id, source_sheet_id):
    try:
        bearer = os.environ["SMARTSHEET_ACCESS_TOKEN"]

        source_sheet = _get_sheet(source_sheet_id)
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


def _delete_rows(sheet_id, rows):
    try:
        responses = []
        bearer = os.environ["SMARTSHEET_ACCESS_TOKEN"]
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


def _delete_sheet(sheet_id):
    bearer = os.environ["SMARTSHEET_ACCESS_TOKEN"]
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


def _clear_sheet(sheet_id):
    try:
        sheet = _get_sheet(sheet_id)
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
        _update_sheet(sheet_id, data)
        _delete_rows(sheet_id, [first_row_id])
    except APIException as e:
        logging.error(f"API Error: {e.response}")
        print(f"An error occurred: {e.response}")


def _import_excel(sheet_name, filepath, target_folder_id=None):
    try:
        bearer = os.environ["SMARTSHEET_ACCESS_TOKEN"]
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


def test():
    pass


if __name__ == "__main__":
    with open(_conf, "r") as conf:
        CONFIG = toml.load(conf)
        if isinstance(CONFIG, dict):
            for k, v in CONFIG["env"].items():
                os.environ[k] = v
            if CONFIG.get("verbose", False):
                logging.basicConfig(
                    filename="sheet.log", filemode="w", level=logging.INFO
                )

            if sys.argv[1] == "get":
                get_sheet()
            elif sys.argv[1] == "set":
                set_sheet()
            elif sys.argv[1] == "test":
                test()

    if isinstance(CONFIG, dict):
        with open(_conf, "w") as conf:
            toml.dump(CONFIG, conf)

end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
