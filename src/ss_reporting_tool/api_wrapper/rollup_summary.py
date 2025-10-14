from ss_reporting_tool.Config import Config
from ss_reporting_tool.Summary import Summary
from ss_reporting_tool.Utils import threader
import os
import json
from typing import List
import ss_api

def rollup_summary(cfg: Config, tables: List[Summary]):
    """
    Create and build summary sheets in Smartsheet for each summary table with a "rollup" tag,
    using filter combinations and parameters from summary_settings/parameters.json.

    Args:
        cfg (Config): Configuration object containing settings_dir and other config.
        tables (List[Summary]): List of Summary objects or tables to process.

    Returns:
        None
    """
    parameters_path = os.path.join(cfg.settings_dir, "parameters.json")
    try:
        with open(parameters_path, "r") as f:
            parameters_settings = json.load(f)
        print(f"Loaded parameters settings: {parameters_settings}")
    except Exception as e:
        print(f"Failed to load parameters settings from {parameters_path}: {e}")
        parameters_settings = {}

    # Filter tables with "rollup" tag
    rollup_tables = [table for table in tables if "rollup" in table.tags]
    print(f"Filtered rollup tables: {[table.name for table in rollup_tables]}")

    def _rollup_summary(table: Summary):
        if not hasattr(table, "metadata") or not isinstance(table.metadata, dict):
            table.metadata = {}
        table.metadata["settings_path"] = parameters_path
        # Reload settings after updating metadata
        table.settings = table.load_settings()

        # Track the current row index for insertion, starting at 2 (second row)
        current_row_index = 2

        # Fetch sheet columns to map titles to IDs
        print(f"Fetching columns for sheet ID: {table.id}")
        sheet_columns = ss_api.get_columns(table.id)
        if not sheet_columns or "data" not in sheet_columns:
            print(f"Failed to fetch columns for sheet {table.name} with ID {table.id}")
            return
        col_title_to_id = {col["title"]: col["id"] for col in sheet_columns.get("data", [])}
        print(f"Column title to ID mapping: {col_title_to_id}")

        # Get the second column ID (start column)
        if sheet_columns and "data" in sheet_columns and len(sheet_columns["data"]) > 1:
            start_col_id = sheet_columns["data"][1]["id"]
        else:
            print("Warning: Sheet does not have a second column, defaulting to first column")
            start_col_id = sheet_columns["data"][0]["id"] if sheet_columns and "data" in sheet_columns and len(sheet_columns["data"]) > 0 else None

        print(f"Using start_col_id: {start_col_id}")

        # Fetch existing rows to update
        sheet_data = ss_api.get_sheet(table.id)
        if not sheet_data or "rows" not in sheet_data:
            print(f"Failed to fetch rows for sheet {table.name} with ID {table.id}")
            return
        existing_rows = sheet_data["rows"]
        print(f"Existing rows count: {len(existing_rows)}")

        # Prepare updates list
        updates = []
        new_rows = []

        for combo in parameters_settings.get("filter_combinations", []):
            group_by = combo.get("group_by", [])
            metrics = combo.get("metrics", [])

            print(f"Processing filter combination: group_by={group_by}, metrics={metrics}")

            # Build header row values
            header_row_values = [group_by[0]] if group_by else []
            if group_by:
                first_group_values = parameters_settings.get("parameters", {}).get(group_by[0], [])
                header_row_values.extend(first_group_values)

            # Prepare header text
            header_text = " | ".join(header_row_values)
            print(f"Constructed header text: {header_text}")

            # Determine row to update or create new
            if current_row_index - 1 < len(existing_rows):
                row_to_update = existing_rows[current_row_index - 1]
                row_id = row_to_update["id"]
                # Prepare header cell update
                header_cell = {
                    "columnId": start_col_id,
                    "value": header_text,
                }
                header_row_update = {
                    "id": row_id,
                    "toTop": False,
                    "toBottom": False,
                    "cells": [header_cell],
                }
                updates.append(header_row_update)
            else:
                # Create new row for header
                header_cells = [{"columnId": start_col_id, "value": header_text}]
                new_rows.append({"toBottom": True, "cells": header_cells})

            # Prepare data rows updates
            data_rows = []
            if len(group_by) > 1:
                second_group_values = parameters_settings.get("parameters", {}).get(group_by[1], [])
                for val in second_group_values:
                    data_rows.append([val])

            for i, row_vals in enumerate(data_rows):
                row_text = row_vals[0] if row_vals else ""
                row_index = current_row_index + 1 + i
                if row_index - 1 < len(existing_rows):
                    row_to_update = existing_rows[row_index - 1]
                    row_id = row_to_update["id"]
                    data_cell = {
                        "columnId": start_col_id,
                        "value": row_text,
                    }
                    data_row_update = {
                        "id": row_id,
                        "toTop": False,
                        "toBottom": False,
                        "cells": [data_cell],
                    }
                    updates.append(data_row_update)
                else:
                    # Create new row for data
                    data_cells = [{"columnId": start_col_id, "value": row_text}]
                    new_rows.append({"toBottom": True, "cells": data_cells})

            # Add empty row for spacing
            spacing_row_index = current_row_index + 1 + len(data_rows)
            if spacing_row_index - 1 < len(existing_rows):
                row_to_update = existing_rows[spacing_row_index - 1]
                row_id = row_to_update["id"]
                empty_row_update = {
                    "id": row_id,
                    "toTop": False,
                    "toBottom": False,
                    "cells": [],
                }
                updates.append(empty_row_update)
            else:
                # Create new empty row
                new_rows.append({"toBottom": True, "cells": []})

            # Update current_row_index for next table
            current_row_index += 2 + len(data_rows)

        # Batch update existing rows
        if updates:
            print(f"Prepared updates for sheet {table.name}:")
            for update in updates:
                print(update)
            ss_api.update_sheet(table.id, updates)
            print(f"Updated {len(updates)} rows in sheet {table.name}")

        # Add new rows if any
        if new_rows:
            print(f"Adding {len(new_rows)} new rows to sheet {table.name}")
            ss_api.add_rows(table.id, new_rows)

        table.build_and_refresh()

    threader(_rollup_summary, rollup_tables, cfg.threadcount)
