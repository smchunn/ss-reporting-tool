import sys
import os
import pandas as pd
import numpy as np

# Expected column order in output
OUTPUT_COLUMNS = [
    "STATUS",
    "ASSIGNMENT",
    "NOTES",
    "PN",
    "DESCRIPTION",
    "MAIN_PN",
    "CHAPTER",
    "SECTION",
    "CATEGORY",
    "ADD EFFECTIVITY",
    "VALIDATE EFFECTIVITY",
    "TRAX_HEADER_EFFECTIVE",
    "EFFECTIVITY_PN_INTERCHANGEABLE",
    "FLEET",
    "VENDOR",
    "CREATED DATE",
    "MODIFIED DATE",
    "COMPLETED DATE",
    "CLEARED BY",
    "IPC_MFR",
    "IPC_CHAPTER",
    "IPC_SECTION",
    "IPC_KWD",
]

VALID_STATUSES = {
    "Initial",
    "In-Work",
    "Assigned",
    "Issue",
    "Updated",
    "Re-Opened",
    "Validated",
    "Complete",
}

PAIRS = [
    ("other.xlsx", "pivot_rpt_epr_std_other.xlsx", "merge_rpt_epr_std_other.xlsx"),
    ("xpendbl_ata_00_26.xlsx", "pivot_rpt_epr_std_xpendbl_00_26.xlsx", "merge_rpt_epr_std_xpendbl_00_26.xlsx"),
    ("xpendbl_ata_27_99.xlsx", "pivot_rpt_epr_std_xpendbl_27_99.xlsx", "merge_rpt_epr_std_xpendbl_27_99.xlsx"),
]

def is_blank(val):
    # Treat NaN, None, empty strings, and 'nan'/'nat'/'none' strings as blank
    if val is None:
        return True
    if isinstance(val, float) and np.isnan(val):
        return True
    if isinstance(val, str):
        s = val.strip()
        if s == "" or s.lower() in {"nan", "nat", "none"}:
            return True
    return False

def to_str(val):
    if is_blank(val):
        return ""
    return str(val).strip()

def normalize_df(df):
    # Ensure all output columns exist
    for col in OUTPUT_COLUMNS:
        if col not in df.columns:
            df[col] = ""
    # Clean up values (remove NaNs, trim)
    for c in df.columns:
        df[c] = df[c].apply(lambda v: "" if is_blank(v) else str(v).strip())
    # Coerce PN and STATUS to strings explicitly
    df["PN"] = df["PN"].astype(str).str.strip()
    df["STATUS"] = df["STATUS"].astype(str).str.strip()
    return df

def parse_ac_cell(cell):
    """
    Parse newline-separated AC values, trim, ignore empties.
    ACs are always numeric per user. Deduplicate.
    Return a set of strings (preserve original).
    """
    if is_blank(cell):
        return set()
    text = str(cell).replace("\r\n", "\n").replace("\r", "\n")
    parts = [p.strip() for p in text.split("\n")]
    parts = [p for p in parts if p != ""]
    return set(parts)

def sort_acs_numerically(ac_iterable):
    """
    Sort ACs numerically ascending; keep original strings for display.
    If not purely digits, fallback to lexicographic.
    """
    def key_func(s):
        s2 = s.strip()
        return (0, int(s2)) if s2.isdigit() else (1, s2)
    return sorted(ac_iterable, key=key_func)

def parse_fleet_cell(cell):
    """
    Parse newline-separated fleets, trim, ignore empties.
    Return a set of strings (preserve original).
    """
    if is_blank(cell):
        return set()
    text = str(cell).replace("\r\n", "\n").replace("\r", "\n")
    parts = [p.strip() for p in text.split("\n")]
    return set(p for p in parts if p != "")

def build_index(df):
    """
    by_pn[pn] = {
        'status': row['STATUS'],
        'add': set(ac strings),
        'validate': set(ac strings),
        'fleets': set(fleet strings),
        'row': original row as dict (for metadata)
    }
    """
    by_pn = {}
    for _, row in df.iterrows():
        pn = to_str(row.get("PN", ""))
        if pn == "":
            continue
        status = to_str(row.get("STATUS", ""))
        add_acs = parse_ac_cell(row.get("ADD EFFECTIVITY", ""))
        val_acs = parse_ac_cell(row.get("VALIDATE EFFECTIVITY", ""))
        fleets = parse_fleet_cell(row.get("FLEET", ""))

        by_pn[pn] = {
            "status": status,
            "add": add_acs,
            "validate": val_acs,
            "fleets": fleets,
            "row": dict(row),
        }
    return by_pn

def merge_item_status(pn, ac, ss_info, rpt_info):
    """
    Item-level merge (rule 11) with Validated override and action precedence rule #8.
    Item identity is (PN, AC). Action chosen per presence; if conflict, choose RPT action.
    """
    ss_add = ss_info.get("add", set())
    ss_val = ss_info.get("validate", set())
    rpt_add = rpt_info.get("add", set())
    rpt_val = rpt_info.get("validate", set())

    in_ss = ac in ss_add or ac in ss_val
    in_rpt = ac in rpt_add or ac in rpt_val

    ss_action = "ADD" if ac in ss_add else ("VALIDATE" if ac in ss_val else None)
    rpt_action = "ADD" if ac in rpt_add else ("VALIDATE" if ac in rpt_val else None)

    # Action precedence per rule #8
    if in_ss and in_rpt and ss_action != rpt_action:
        final_action = rpt_action
    else:
        final_action = ss_action if ss_action is not None else rpt_action

    ss_status = ss_info.get("status", None)
    rpt_status = rpt_info.get("status", None)

    # Apply item-level status rules (11) with Validated override (Option B)
    if in_ss and not in_rpt:
        merged_status = "Validated" if ss_status == "Validated" else "Complete"
    elif in_rpt and not in_ss:
        merged_status = rpt_status
    else:
        # in both
        if ss_status == "Validated":
            merged_status = "Validated"
        elif rpt_status == ss_status:
            merged_status = ss_status
        elif ss_status == "Initial" and rpt_status == "Complete":
            merged_status = "Re-Opened"
        elif rpt_status == "Initial":
            merged_status = ss_status
        elif rpt_status == "Complete":
            merged_status = "Complete"
        else:
            merged_status = ss_status

    return merged_status, final_action

def synthesize_row_for_pn(pn, ss_by_pn, rpt_by_pn):
    """
    Create the final output row for a PN or return None to drop it.
    Implements row-level rules (12), resolved-row handling (10), row deletion (9),
    metadata precedence, CLEARED BY logic, and Fleet union.
    """
    ss_info = ss_by_pn.get(pn, {})
    rpt_info = rpt_by_pn.get(pn, {})

    # Collect all ACs present across ss and rpt
    acs_all = set()
    acs_all |= ss_info.get("add", set())
    acs_all |= ss_info.get("validate", set())
    acs_all |= rpt_info.get("add", set())
    acs_all |= rpt_info.get("validate", set())

    # If no ACs at all in both sources, delete the row (rule #9)
    if not acs_all:
        return None

    # Build items with merged statuses and final action
    items = []
    for ac in acs_all:
        merged_status, final_action = merge_item_status(pn, ac, ss_info, rpt_info)
        items.append({"ac": ac, "status": merged_status, "action": final_action})

    statuses_set = set(i["status"] for i in items)

    # Determine final status and which items to include in action columns
    if len(statuses_set) == 1:
        final_status = next(iter(statuses_set))
        final_items = list(items)  # include all items; if resolved, they will show per rule #10
    else:
        # 12.b Drop Complete
        remaining = [i for i in items if i["status"] != "Complete"]
        # 12.c If Validated items and others remain, drop Validated
        if any(i["status"] != "Validated" for i in remaining):
            remaining = [i for i in remaining if i["status"] != "Validated"]

        if remaining:
            non_initial = {i["status"] for i in remaining if i["status"] != "Initial"}
            if len(non_initial) > 1:
                final_status = "In-Work"
            elif len(non_initial) == 1:
                final_status = next(iter(non_initial))
            else:
                final_status = "Initial"
            final_items = remaining
        else:
            # All items resolved; Option C for mixed resolved
            if statuses_set == {"Validated"}:
                final_status = "Validated"
            else:
                final_status = "Complete"
            final_items = list(items)  # include resolved ACs (rule #10)

    # Build action columns
    add_acs = [i["ac"] for i in final_items if i["action"] == "ADD"]
    val_acs = [i["ac"] for i in final_items if i["action"] == "VALIDATE"]

    add_acs = sort_acs_numerically(set(add_acs))
    val_acs = sort_acs_numerically(set(val_acs))

    add_cell = "\n".join(add_acs) if add_acs else ""
    val_cell = "\n".join(val_acs) if val_acs else ""

    # Rule #9: If no action ACs remain (and not all-resolved because final_items would be empty in that case),
    # drop the row. All-resolved case includes resolved ACs above, so add_cell/val_cell would not both be empty.
    if add_cell == "" and val_cell == "":
        return None

    # Metadata rows for precedence logic
    ss_row = ss_info.get("row", {}) if ss_info else {}
    rpt_row = rpt_info.get("row", {}) if rpt_info else {}

    # Fleet union: newline-separated, unique, alphabetically sorted; blank if none
    ss_fleets = ss_info.get("fleets", set())
    rpt_fleets = rpt_info.get("fleets", set())
    all_fleets = sorted(set(ss_fleets) | set(rpt_fleets), key=lambda s: s)
    fleet_cell = "\n".join(all_fleets) if all_fleets else ""

    def meta_value(col):
        if col == "STATUS":
            return final_status
        if col == "PN":
            return pn
        if col == "ADD EFFECTIVITY":
            return add_cell
        if col == "VALIDATE EFFECTIVITY":
            return val_cell
        if col == "FLEET":
            return fleet_cell  # new requirement
        if col == "CLEARED BY":
            # Only when final row status is Complete and rpt has a value
            if final_status == "Complete":
                return to_str(rpt_row.get("CLEARED BY", ""))
            return ""

        # Other metadata: use ss where available; fill blanks from rpt
        ss_val = to_str(ss_row.get(col, "")) if ss_row else ""
        if ss_val != "":
            return ss_val
        rpt_val = to_str(rpt_row.get(col, "")) if rpt_row else ""
        return rpt_val

    final_row = {col: meta_value(col) for col in OUTPUT_COLUMNS}
    return final_row

def process_pair(folder, ss_file, rpt_file, out_file):
    ss_path = os.path.join(folder, ss_file)
    rpt_path = os.path.join(folder, rpt_file)

    # Per user: these will exist exactly; we fail fast if not present
    if not os.path.exists(ss_path):
        raise FileNotFoundError(f"Missing {ss_path}")
    if not os.path.exists(rpt_path):
        raise FileNotFoundError(f"Missing {rpt_path}")

    # Read as native types to avoid 'nan' strings; normalize explicitly later
    ss_df = pd.read_excel(ss_path)
    rpt_df = pd.read_excel(rpt_path)

    ss_df = normalize_df(ss_df)
    rpt_df = normalize_df(rpt_df)

    ss_by_pn = build_index(ss_df)
    rpt_by_pn = build_index(rpt_df)

    all_pns = sorted(set(ss_by_pn.keys()) | set(rpt_by_pn.keys()))

    final_rows = []
    for pn in all_pns:
        row = synthesize_row_for_pn(pn, ss_by_pn, rpt_by_pn)
        if row is not None:
            final_rows.append(row)

    out_df = pd.DataFrame(final_rows, columns=OUTPUT_COLUMNS) if final_rows else pd.DataFrame(columns=OUTPUT_COLUMNS)

    out_path = os.path.join(folder, out_file)
    out_df.to_excel(out_path, index=False)
    print(f"Wrote merged report: {out_path} (rows: {len(out_df)})")

def main():
    if len(sys.argv) < 2:
        print("Usage: python merge_effectivity.py <folder_path>")
        sys.exit(1)

    folder = sys.argv[1]
    for ss_file, rpt_file, out_file in PAIRS:
        process_pair(folder, ss_file, rpt_file, out_file)

if __name__ == "__main__":
    main()