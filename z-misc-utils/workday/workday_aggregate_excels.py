from pathlib import Path
import os
import pandas as pd
from pprint import pprint

#=================
#  CONSTANTS
#=================
dir_path: Path = Path("C:\\Users\\Timot\\Downloads\\workday_payslips\\workday_payslips")
output_csv_path = 'output.csv'

def find_all_label_positions(df: pd.DataFrame, key: str) -> list[tuple[int, int]]:
    """
    Finds all instances of the key in the DataFrame and returns their (row, column) indices.
    """
    positions = []
    for row_idx in range(df.shape[0]):
        for col_idx in range(df.shape[1]):
            if pd.notna(df.iat[row_idx, col_idx]) and key.lower() in str(df.iat[row_idx, col_idx]).lower():
                positions.append((row_idx, col_idx))
    return positions

def extract_tag_row(df: pd.DataFrame, tag: str, column_offset: int = 1, is_second_instance: bool = False) -> str | None:
    """
    Extracts the value from the row where the tag appears, adjusting for column offset.
    """
    tag_positions = find_all_label_positions(df, tag)
    if tag_positions:
        row_index, col_index = tag_positions[1] if is_second_instance and len(tag_positions) > 1 else tag_positions[0]
        target_col = col_index + column_offset
        return df.iat[row_index, target_col] if target_col < df.shape[1] else None
    return None

def extract_tag_column(df: pd.DataFrame, tag: str, row_offset: int = 1) -> str | None:
    """
    Extracts the value from the column where the tag appears, adjusting for row offset.
    """
    tag_positions = find_all_label_positions(df, tag)
    if tag_positions:
        row_index, col_index = tag_positions[0]
        target_row = row_index + row_offset
        return df.iat[target_row, col_index] if target_row < df.shape[0] else None
    return None

def aggregate_payslip_data(directory: Path, output_csv: str):
    all_data = []
    
    for file in os.listdir(directory):
        if file.endswith(".xlsx"):
            try:
                file_path = directory / file
                df = pd.read_excel(file_path, sheet_name=0, header=None, index_col=None)
                df.reset_index(drop=True, inplace=True)
                
                row = {
                    "General - Pay Period Begin": extract_tag_column(df, "Pay Period Begin"),
                    "General - Pay Period End": extract_tag_column(df, "Pay Period End"),
                    "General - Check Date": extract_tag_column(df, "Check Date"),
                    "General - Worked Hours": extract_tag_column(df, "Hours Worked"),
                    "General - Holiday Hours": extract_tag_row(df, "Holiday Pay", 2),
                    "General - Vacation Hours": extract_tag_row(df, "Vacation", 2),
                    "General - Gross Pay": extract_tag_column(df, "Gross Pay"),
                    "General - Net Pay": extract_tag_column(df, "Net Pay"),
                    "Taxes - Employee Taxes": extract_tag_column(df, "Employee Taxes"),
                    "Taxes - Federal Withholding": extract_tag_row(df, "Federal Withholding"),
                    "Taxes - State Withholding (MA)": extract_tag_row(df, "State Tax - MA"),
                    "Taxes - OASDI": extract_tag_row(df, "OASDI"),
                    "Taxes - Medicare": extract_tag_row(df, "Medicare"),
                    "Insurance - Medical": extract_tag_row(df, "Medical"),
                    "Insurance - Dental": extract_tag_row(df, "Dental"),
                    "Insurance - Vision": extract_tag_row(df, "Vision"),
                    "Insurance (Employer) - Medical": extract_tag_row(df, "Medical", is_second_instance=True),
                    "Insurance (Employer) - Dental": extract_tag_row(df, "Dental", is_second_instance=True),
                    "Insurance (Employer) - Vision": extract_tag_row(df, "Vision", is_second_instance=True),
                    "Insurance (Employer) - Basic Life and AD&D": extract_tag_row(df, "Basic Life and AD&D"),
                    "Insurance (Employer) - Short Term Disability": extract_tag_row(df, "Short Term Disability"),
                    "Insurance (Employer) - Long Term Disability": extract_tag_row(df, "Long Term Disability"),
                    "Tax-Advantaged Accounts (Employer) - 401(k) employer": extract_tag_row(df, "401(k) Match"),
                    "Tax-Advantaged Accounts (Employer) - HSA employer": extract_tag_row(df, "Health Savings Account - ER"),
                    "Tax-Advantaged Accounts - 401(k) employee": extract_tag_row(df, "401(k) Traditional"),
                    "Tax-Advantaged Accounts - HSA employee": extract_tag_row(df, "HSA"),
                    "Tax-Advantaged Accounts - ESPP": extract_tag_row(df, "ESPP"),
                    "Taxes - OASDI / Medicare Taxable Wages": extract_tag_row(df, "OASDI - Taxable Wages"),
                    "Taxes - Federal Withholding / State Tax Taxable Wages": extract_tag_row(df, "Federal Withholding - Taxable Wages"),
                }
                
                # pprint(row)
                all_data.append(row)
                print(f"Successfully processed '{file_path}'")
            except Exception as e:
                print(f"Error processing '{file_path}': {e}")
    
    if all_data:
        aggregated_df = pd.DataFrame(all_data)
        aggregated_df.to_csv(output_csv, index=False, encoding='utf-8')
        print(f"Aggregated CSV saved to '{output_csv}'")
    else:
        print("No valid payslip data found.")

aggregate_payslip_data(dir_path, output_csv_path)