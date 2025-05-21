# ss-reporting-tool/src/ss_reporting_tool/__main__.py
from ss_reporting_tool.Config import Config, setup, cli_args
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Summary import Summary
from ss_reporting_tool.api_wrapper import *
import os, logging
from datetime import datetime
import polars as pl
from polars import col, lit
from datetime import datetime, timezone


start_time = datetime.now()


def main():
    CFG = setup()
    if not isinstance(CFG, Config):
        return
    ac_reports = [
        table
        for table in CFG.tables
        if isinstance(table, Report) and "ac" in table.tags
    ]
    eng_reports = [
        table
        for table in CFG.tables
        if isinstance(table, Report) and "engine" in table.tags
    ]
    effect_summaries = [
        table
        for table in CFG.tables
        if isinstance(table, Summary)
        if "effect" in table.tags
    ]
    interchg_summary_tables = [
        table
        for table in CFG.tables
        if isinstance(table, Summary)
        if "interchg" in table.tags
    ]
    if CFG.function == "get":
        get_sheet(CFG, ac_reports)
    elif CFG.function == "set":
        set_sheet(CFG, ac_reports)
    elif CFG.function == "update":
        update_sheet(CFG, ac_reports)
    elif CFG.function == "dedupe":
        remove_duplicates(CFG, ac_reports, ["AC", "FLEET", "PN", "MAIN_PN", "VENDOR"])
    elif CFG.function == "dedupe_engine":
        remove_duplicates(
            CFG, eng_reports, ["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"]
        )
    elif CFG.function == "feedback":
        feedback_loop(CFG, ac_reports, ["AC", "FLEET", "PN", "MAIN_PN", "VENDOR"])
    elif CFG.function == "feedback_engine":
        feedback_loop(CFG, eng_reports, ["AC", "FLEET", "PN", "NHA", "TOP", "LEVEL"])
    elif CFG.function == "reformat":
        reformat_sheet(CFG, ac_reports)
    elif CFG.function == "lock":
        lock_columns(CFG, ac_reports)


if __name__ == "__main__":
    main()

end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
