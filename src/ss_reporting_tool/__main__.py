# ss-reporting-tool/src/ss_reporting_tool/__main__.py
from ss_reporting_tool.Table import Table
from ss_reporting_tool.Config import Config, CliArgs, load_config_dict_from_path
from ss_reporting_tool.api_wrapper import *
import os, logging
from datetime import datetime
import polars as pl
from polars import col, lit
from datetime import datetime, timezone
from ss_reporting_tool import setup, CFG, CFG_PATH


start_time = datetime.now()

# logging.basicConfig(level=logging.INFO)



def main():
    setup()
    if not isinstance(CFG, Config):
        return
    all_tables = CFG.tables
    ac_tables = [table for table in all_tables if "ac" in table.tags]
    eng_tables = [table for table in all_tables if "engine" in table.tags]

    if CFG.function == "get":
        get_sheet(all_tables)
    elif CFG.function == "set":
        set_sheet(all_tables)
    elif CFG.function == "update":
        update_sheet(all_tables)
    elif CFG.function == "dedupe":
        remove_duplicates(ac_tables, ["AC", "FLEET", "PN", "MAIN_PN", "VENDOR"])
    elif CFG.function == "dedupe_engine":
        remove_duplicates(eng_tables, ["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"])
    elif CFG.function == "feedback":
        feedback_loop(ac_tables, ["AC", "FLEET", "PN", "MAIN_PN", "VENDOR"])
    elif CFG.function == "feedback_engine":
        feedback_loop(eng_tables, ["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"])
    elif CFG.function == "reformat":
        reformat_sheet(all_tables)
    elif CFG.function == "lock":
        lock_columns(all_tables)
    elif CFG.function == "refresh_summary":
        refresh_summary(all_tables)
    elif CFG.function == "refresh_summary":
        refresh_summary(all_tables)


if __name__ == "__main__":
    main()


end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
