import pandas as pd
import glob
import os
import sys

input_folder = sys.argv[1]
output_folder = sys.argv[2]
output_file = os.path.join(output_folder, "EFFECTIVITY.xlsx")

output_columns = [
    "STATUS", "ASSIGNMENT", "NOTES", "PN", "DESCRIPTION", "MAIN_PN", "CHAPTER",
    "SECTION", "CATEGORY", "PRIORITY", "Add Effectivity", "Validate Effectivity",
    "TRAX_HEADER_EFFECTIVE", "EFFECTIVITY_PN_INTERCHANGEABLE", "FLEET", "VENDOR",
    "CREATED DATE", "MODIFIED DATE", "COMPLETED DATE"
]
required_columns = [
    "STATUS", "ASSIGNMENT", "NOTES", "PN", "DESCRIPTION", "MAIN_PN", "CHAPTER",
    "SECTION", "CATEGORY", "PRIORITY", "AC", "PROPOSED_ACTION", "TRAX_HEADER_EFFECTIVE",
    "EFFECTIVITY_PN_INTERCHANGEABLE", "FLEET", "VENDOR", "CREATED DATE", "MODIFIED DATE"
]

all_files = glob.glob(os.path.join(input_folder, "*.xlsx"))
if not all_files:
    print(f"No .xlsx files found in {input_folder}")
    sys.exit(1)

dfs = []
for f in all_files:
    df = pd.read_excel(f, dtype=str)
    df.columns = [c.strip().upper() for c in df.columns]
    for col in required_columns:
        if col not in df.columns:
            df[col] = ""
    df = df[required_columns]
    dfs.append(df)

df = pd.concat(dfs, ignore_index=True)
df["COMPLETED DATE"] = ""

def unique_or_fallback(series, fallback):
    vals = [v for v in series if pd.notna(v) and str(v).strip() != ""]
    if len(vals) == 1:
        return vals[0]
    elif len(set(vals)) == 1 and vals:
        return vals[0]
    elif not vals:
        return ""
    return fallback

def concat_unique(series):
    vals = [v for v in series if pd.notna(v) and str(v).strip() != ""]
    return "\n".join(sorted(set(vals))) if vals else ""

def effectivity(series, actions, action_value):
    result = sorted(set(
        ac for ac, act in zip(series, actions)
        if act == action_value and pd.notna(ac) and str(ac).strip() != ""
    ))
    return "\n".join(result)

def fleet_join(series):
    result = sorted(set([v for v in series if pd.notna(v) and str(v).strip() != ""]))
    return "\n".join(result)

grouped = df.groupby("PN", dropna=False).agg({
    "STATUS": lambda x: unique_or_fallback(x, "In-Work"),
    "ASSIGNMENT": concat_unique,
    "NOTES": concat_unique,
    "PN": "first",
    "DESCRIPTION": lambda x: unique_or_fallback(x, "Mixed"),
    "MAIN_PN": lambda x: unique_or_fallback(x, "Mixed"),
    "CHAPTER": lambda x: unique_or_fallback(x, "Mixed"),
    "SECTION": lambda x: unique_or_fallback(x, "Mixed"),
    "CATEGORY": lambda x: unique_or_fallback(x, "Mixed"),
    "AC": list,
    "PROPOSED_ACTION": list,
    "TRAX_HEADER_EFFECTIVE": lambda x: unique_or_fallback(x, "Mixed"),
    "EFFECTIVITY_PN_INTERCHANGEABLE": lambda x: unique_or_fallback(x, "Mixed"),
    "FLEET": fleet_join,
    "VENDOR": lambda x: unique_or_fallback(x, "Mixed"),
    "COMPLETED DATE": "first",
    "CREATED DATE": lambda x: unique_or_fallback(x, "Mixed"),
    "MODIFIED DATE": lambda x: unique_or_fallback(x, "Mixed"),
}).reset_index(drop=True)

grouped["Add Effectivity"] = grouped.apply(
    lambda row: effectivity(row["AC"], row["PROPOSED_ACTION"], "ADD_EFFECTIVITY"), axis=1)
grouped["Validate Effectivity"] = grouped.apply(
    lambda row: effectivity(row["AC"], row["PROPOSED_ACTION"], "VALIDATE_EFFECTIVITY"), axis=1)

grouped = grouped.drop(columns=["AC", "PROPOSED_ACTION"])
grouped = grouped[output_columns]

os.makedirs(output_folder, exist_ok=True)
grouped.to_excel(output_file, index=False)
print(f"Combined file written to {output_file}")