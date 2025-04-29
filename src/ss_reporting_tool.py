from src.Table import Table
from src.Config import Config
from src.api_wrapper import *
import os, logging
from datetime import datetime
import polars as pl
from polars import col, lit
from datetime import datetime, timezone


start_time = datetime.now()

logging.basicConfig(level=logging.INFO)


def main():
    Table.config = Config()
    cfg: Config = Table.config
    all_tables = cfg.tables
    ac_tables = [table for table in cfg.tables if table.tags.contains("ac")]
    eng_tables = [table for table in cfg.tables if table.tags.contains("engine")]

    if Table.config.function == "get":
        get_sheet(all_tables, cfg)
    elif Table.config.function == "set":
        set_sheet(all_tables, cfg)
    elif Table.config.function == "update":
        update_sheet(all_tables, cfg)
    elif Table.config.function == "dedupe":
        remove_duplicates(ac_tables, cfg, ["AC", "FLEET", "PN", "MAIN_PN", "VENDOR"])
    elif Table.config.function == "dedupe_engine":
        remove_duplicates(eng_tables, cfg, ["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"])
    elif Table.config.function == "feedback":
        feedback_loop(ac_tables, cfg, ["AC", "FLEET", "PN", "MAIN_PN", "VENDOR"])
    elif Table.config.function == "feedback_engine":
        feedback_loop(eng_tables, cfg, ["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"])
    elif Table.config.function == "reformat":
        reformat_sheet(all_tables, cfg)
    elif Table.config.function == "lock":
        lock_columns(all_tables, cfg)
    elif Table.config.function == "refresh_summary":
        refresh_summary(all_tables, cfg)


if __name__ == "__main__":
    main()


end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
