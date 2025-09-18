import sys
import os
import pandas as pd

def pivot_rpt(rpt_path, output_path):
    # Output columns as in ss
    ss_columns = [
        "STATUS", "ASSIGNMENT", "NOTES", "PN", "DESCRIPTION", "MAIN_PN", "CHAPTER", "SECTION", "CATEGORY",
        "ADD EFFECTIVITY", "VALIDATE EFFECTIVITY", "TRAX_HEADER_EFFECTIVE", "EFFECTIVITY_PN_INTERCHANGEABLE",
        "FLEET", "VENDOR", "CREATED DATE", "MODIFIED DATE", "COMPLETED DATE",
        "Cleared By", "IPC_MFR", "IPC_CHAPTER", "IPC_SECTION", "IPC_KWD"
    ]

    # Only FLEET is handled specially (never "Mixed") - everything else as previous
    metadata_cols = [
        "ASSIGNMENT", "NOTES", "DESCRIPTION", "MAIN_PN", "CHAPTER", "SECTION", "CATEGORY",
        "TRAX_HEADER_EFFECTIVE", "EFFECTIVITY_PN_INTERCHANGEABLE", "VENDOR", "Cleared By",
        "IPC_MFR", "IPC_CHAPTER", "IPC_SECTION", "IPC_KWD"
    ]
    # Mapping from ss column name to rpt column name
    col_map = {
        "STATUS": "STATUS",
        "ASSIGNMENT": "Assignment",
        "NOTES": "Notes",
        "PN": "PN",
        "DESCRIPTION": "DESCRIPTION",
        "MAIN_PN": "MAIN_PN",
        "CHAPTER": "CHAPTER",
        "SECTION": "SECTION",
        "CATEGORY": "CATEGORY",
        "TRAX_HEADER_EFFECTIVE": "TRAX_HEADER_EFFECTIVE",
        "EFFECTIVITY_PN_INTERCHANGEABLE": "EFFECTIVITY_PN_INTERCHANGEABLE",
        "FLEET": "FLEET",
        "VENDOR": "VENDOR",
        "Cleared By": "CLEARED BY",
        "IPC_MFR": "IPC_MFR",
        "IPC_CHAPTER": "IPC_CHAPTER",
        "IPC_SECTION": "IPC_SECTION",
        "IPC_KWD": "IPC_KWD",
        # Dates and actions mapped separately
        "CREATED DATE": None,
        "MODIFIED DATE": None,
        "COMPLETED DATE": None,
        "ADD EFFECTIVITY": None,
        "VALIDATE EFFECTIVITY": None
    }

    rpt = pd.read_excel(rpt_path, dtype=str).fillna("")
    # Normalize action and AC columns
    rpt["Action"] = rpt["Action"].str.upper().str.strip()
    rpt["AC"] = rpt["AC"].str.strip()

    records = []
    for pn, grp in rpt.groupby("PN"):
        row = {"PN": pn}

        # Actions: sorted unique ACs for each
        for actcol, actval in [("ADD EFFECTIVITY", "ADD_EFFECTIVITY"),
                               ("VALIDATE EFFECTIVITY", "VALIDATE_EFFECTIVITY")]:
            acs = grp.loc[grp["Action"] == actval, "AC"].dropna().unique()
            # Alphanumeric sort
            def pad_val(x): return int(x) if x.isdigit() else x
            acs_sorted = sorted(set(acs), key=pad_val)  # Remove dups, sort
            row[actcol] = "\n".join(acs_sorted) if acs_sorted else ""

        # Only keep rows with an action
        if not row["ADD EFFECTIVITY"] and not row["VALIDATE EFFECTIVITY"]:
            continue

        # FLEET: list all unique, sorted, never "Mixed"
        fleets = grp["FLEET"].dropna().unique()
        fleets_sorted = sorted(set(fleets))
        row["FLEET"] = "\n".join(fleets_sorted) if fleets_sorted else ""

        # STATUS
        statuses = set(grp["STATUS"].dropna().unique())
        if statuses == {"Initial"}:
            row["STATUS"] = "Initial"
        elif "Complete" in statuses:
            row["STATUS"] = "Complete"
        else:
            row["STATUS"] = "Initial"

        # Metadata columns: Use value if one, blank if none, "Mixed" if >1
        for mc in metadata_cols:
            vals = grp[col_map[mc]].dropna().unique().tolist()
            if len(vals) == 1:
                row[mc] = vals[0]
            elif len(vals) == 0:
                row[mc] = ""
            else:
                row[mc] = "Mixed"
        # Dates always blank
        row["CREATED DATE"] = ""
        row["MODIFIED DATE"] = ""
        row["COMPLETED DATE"] = ""

        records.append(row)

    outdf = pd.DataFrame(records, columns=ss_columns)
    outdf.to_excel(output_path, index=False)
    print(f"Pivoted rpt written to {output_path}")

if __name__ == "__main__":
    # Usage: python pivot_rpt_multi.py <inputfolder>
    if len(sys.argv) < 2:
        print("Usage: python pivot_rpt_multi.py <inputfolder>")
        sys.exit(1)

    inputfolder = sys.argv[1]

    # Process the three specified files independently
    file_names = [
        "rpt_epr_std_other.xlsx",
        "rpt_epr_std_xpendbl_00_26.xlsx",
        "rpt_epr_std_xpendbl_27_99.xlsx",
    ]

    for fname in file_names:
        rpt_path = os.path.join(inputfolder, fname)
        if not os.path.exists(rpt_path):
            raise FileNotFoundError(f"Input file not found: {rpt_path}")
        output_path = os.path.join(inputfolder, f"pivot_{fname}")
        pivot_rpt(rpt_path, output_path)