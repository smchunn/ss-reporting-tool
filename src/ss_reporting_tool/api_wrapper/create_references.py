from ss_reporting_tool.Config import Config
from ss_reporting_tool.Utils import threader
import ss_api
import json
import os
import logging


def create_references(cfg: Config, tables: list):
    def _create_references(table):
        print(f"Creating cross-sheet references for table: {table.name} (ID: {table.id})")

        settings_dir = cfg.settings_dir

        reference_sheet_path = os.path.join(cfg.settings_dir, "reference_sheet.json")
        with open(reference_sheet_path, "r") as f:
            reference_sheet_data = json.load(f)
            destination_sheet_id = reference_sheet_data.get("destination_sheet_id")

        col_refs_path = os.path.join(settings_dir, "column_references.json")
        with open(col_refs_path, "r") as f:
            column_references = json.load(f)

        columns = ss_api.get_columns(sheet_id=table.id)
        if isinstance(columns, dict):
            columns = columns.get("data", None)
        if not columns:
            print(f"Error getting columns for '{table.name} (ID: {table.id})'")
            return

        for ref in column_references:
            ref_name = ref.get("ref_name")
            col_name = ref.get("col_name")
            if not ref_name or not col_name:
                logging.warning(f"Invalid reference entry: {ref}")
                continue

            source_column_id = None
            for col in columns:
                if col.get("title") == col_name:
                    source_column_id = col.get("id")
                    break

            if not source_column_id:
                logging.error(f"Column '{col_name}' not found in sheet {table.id}")
                continue

            try:
                ref_full_name = f"{table.name} {ref_name}"
                print(f"Creating cross-sheet reference '{ref_full_name}' for column '{col_name}' in sheet {table.id}")
                logging.info(f"Calling create_cross_sheet_reference with destination_sheet_id={destination_sheet_id}, source_sheet_id={table.id}, source_column_id={source_column_id}")
                ss_api.create_cross_sheet_reference(
                    destination_sheet_id=destination_sheet_id,
                    source_sheet_id=table.id,
                    source_column_id=source_column_id,
                    name=ref_full_name,
                )
            except Exception as e:
                logging.error(f"Failed to create cross-sheet reference '{ref_full_name}' for sheet {table.id}: {e}")

    print("Creating cross-sheet references ...")
    threader(_create_references, tables, cfg.threadcount)
