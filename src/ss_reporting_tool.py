import os, logging
import toml, json
import ss_api
import concurrent.futures, threading
import polars as pl
from datetime import datetime
from os.path import isfile
from polars import col, lit
from datetime import datetime, timezone
from typing import List, Dict, Callable, Union


start_time = datetime.now()


logging.basicConfig(level=logging.INFO)






def main():
    Table.config = Config()
    if Table.config.function == "get":
        get_sheet()
    elif Table.config.function == "set":
        set_sheet()
    elif Table.config.function == "update":
        update_sheet()
    elif Table.config.function == "dedupe":
        remove_dupes()
    elif Table.config.function == "dedupe_engine":
        remove_dupes_engine()
    elif Table.config.function == "feedback":
        feedback_loop()
    elif Table.config.function == "feedback_engine":
        feedback_loop_engine()
    elif Table.config.function == "reformat":
        reformat_sheet()
    elif Table.config.function == "lock":
        lock_columns()
    elif Table.config.function == "refresh_summary":
        refresh_summary()


if __name__ == "__main__":
    main()


end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
