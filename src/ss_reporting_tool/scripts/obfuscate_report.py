import pandas as pd
import re

# Load the Excel file
df = pd.read_excel("rpt_ier.xlsx")

def convert_effectivity(cell):
    if pd.isna(cell):
        return cell
    lines = str(cell).split('\n')
    new_lines = []
    for line in lines:
        match = re.match(r'^\s*(\d{3})\s*$', line)
        if match:
            num = int(match.group(1))
            if 401 <= num <= 475:
                num -= 300
            new_lines.append(str(num))
        elif line.strip() == '':
            continue
        else:
            new_lines.append(line)
    return '\n'.join(new_lines)

def rotate_char(c):
    # Letters: rotate by 18, wrap around
    if 'A' <= c <= 'Z':
        return chr((ord(c) - ord('A') + 18) % 26 + ord('A'))
    elif 'a' <= c <= 'z':
        return chr((ord(c) - ord('a') + 18) % 26 + ord('a'))
    # Digits: add 3, wrap at 9
    elif '0' <= c <= '9':
        return str((int(c) + 3) % 10)
    else:
        return c

def rotate_string(cell):
    if pd.isna(cell):
        return cell
    return ''.join(rotate_char(c) for c in str(cell))

# Process effectivity columns
for col in ["ADD EFFECTIVITY", "VALIDATE EFFECTIVITY"]:
    if col in df.columns:
        df[col] = df[col].apply(convert_effectivity)

# Process string columns
string_cols = ["PN", "M/E_MFACT_REF", "IPC_MFACT_REF", "PART GROUP", "IPC PART GROUP", "PRIMARY_PN", "IPC_ITEM_KEY"]
for col in string_cols:
    if col in df.columns:
        df[col] = df[col].apply(rotate_string)

# Save to a new Excel file
df.to_excel("rpt_ier_converted.xlsx", index=False)