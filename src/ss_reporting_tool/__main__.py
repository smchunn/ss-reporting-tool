# ss-reporting-tool/src/ss_reporting_tool/__main__.py
from ss_reporting_tool.Config import Config, setup, cli_args
from ss_reporting_tool.Report import Report
from ss_reporting_tool.Summary import Summary
from ss_reporting_tool.api_wrapper import *
import os, logging
import polars as pl
from polars import col, lit
from datetime import datetime, timezone


start_time = datetime.now()


def main():
    CFG = setup()
    if not isinstance(CFG, Config):
        return
    reports = [table for table in CFG.tables if isinstance(table, Report)]
    summary = [table for table in CFG.tables if isinstance(table, Summary)]
    if CFG.function == "get":
        get_sheet(CFG, reports)
    elif CFG.function == "set":
        set_sheet(CFG, reports)
    elif CFG.function == "update_col_type":
        update_col_type(CFG, reports)
    elif CFG.function == "update_col_desc":
        update_col_desc(CFG, reports)
    elif CFG.function == "feedback":
        feedback_loop(CFG, reports, ["AC", "FLEET", "PN", "MAIN_PN", "VENDOR"])
    elif CFG.function == "reformat":
        reformat_sheet(CFG, reports)
    elif CFG.function == "lock":
        lock_columns(CFG, reports)
    elif CFG.function == "add_col":
        add_cols(CFG, reports)
    elif CFG.function == "update_column":
        update_column(CFG, reports)
    elif CFG.function == "create_references":
        create_references(CFG, reports)
    elif CFG.function == "create_summary":
        create_summary(CFG, summary)


if __name__ == "__main__":
    main()

end_time = datetime.now()
print("Duration: {}".format(end_time - start_time))
