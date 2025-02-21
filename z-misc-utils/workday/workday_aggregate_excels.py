import calendar
import os
from pathlib import Path
from pprint import pprint

import pandas as pd

#=================
#  CONSTANTS
#=================
dir_path: Path = Path("C:\\Users\\Timot\\Downloads\\workday_payslips\\workday_payslips")
output_csv_path = 'output_paystubs.csv'
agg_output_csv_path = 'output_agg_paystubs.csv'

#=================
#  UTILS
#=================
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

#=================
#  MAIN
#=================
def build_paystub_list_df(directory: Path) -> pd.DataFrame:
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
    
    return pd.DataFrame(all_data)


def build_paystub_stats_df(paystub_list_df: pd.DataFrame) -> pd.DataFrame:
    """
    Builds df with values per month
    - Gross Pay
    - Net Pay
    - Taxes
    - Insurance
    - 401(k) Total
    - HSA Total
    - ESPP Total

    The current paystubs are biweekly and go between months, this code prorates the values by the month using the number of days in that month
    """
    # Convert 'Pay Period Begin' and 'Pay Period End' to datetime
    paystub_list_df['Pay Period Begin'] = pd.to_datetime(paystub_list_df['General - Pay Period Begin'])
    paystub_list_df['Pay Period End'] = pd.to_datetime(paystub_list_df['General - Pay Period End'])
    
    # Initialize columns for the amounts
    paystub_list_df['Gross Pay'] = 0
    paystub_list_df['Net Pay'] = 0
    paystub_list_df['Taxes'] = 0
    paystub_list_df['Insurance'] = 0
    paystub_list_df['401(k) Employee'] = 0
    paystub_list_df['HSA Employee'] = 0
    paystub_list_df['401(k) Employer Match'] = 0
    paystub_list_df['HSA Employer Match'] = 0
    paystub_list_df['ESPP Total'] = 0
    
    # Iterate through each row to calculate amounts
    for idx, row in paystub_list_df.iterrows():
        # Calculate the number of days in the pay period
        days_in_period = (row['Pay Period End'] - row['Pay Period Begin']).days + 1  # Include the end day
        # Extract the start and end month
        start_month = row['Pay Period Begin'].month
        end_month = row['Pay Period End'].month

        if start_month == end_month:  # Same month means add to month if present
            paystub_list_df.at[idx, 'Gross Pay'] += row['General - Gross Pay']
            paystub_list_df.at[idx, 'Net Pay'] += row['General - Net Pay']
            paystub_list_df.at[idx, 'Taxes'] += row['Taxes - Employee Taxes']
            paystub_list_df.at[idx, 'Insurance'] += row['Insurance - Medical']
            paystub_list_df.at[idx, '401(k) Employee'] += row['Tax-Advantaged Accounts - 401(k) employee']
            paystub_list_df.at[idx, 'HSA Employee'] += row['Tax-Advantaged Accounts - HSA employee']
            paystub_list_df.at[idx, '401(k) Employer Match'] += row['Tax-Advantaged Accounts (Employer) - 401(k) employer']
            paystub_list_df.at[idx, 'HSA Employer Match'] += row['Tax-Advantaged Accounts (Employer) - HSA employer']
            paystub_list_df.at[idx, 'ESPP Total'] += row['Tax-Advantaged Accounts - ESPP']
            continue
        
        # Calculate the days in each month for prorating
        start_day_of_month = row['Pay Period Begin'].day
        end_day_of_month = row['Pay Period End'].day
        days_in_start_month = calendar.monthrange(row['Pay Period Begin'].year, start_month)[1] - start_day_of_month + 1
        days_in_end_month = end_day_of_month
        
        # Prorate for the start month
        prorate_rate = days_in_start_month / days_in_period

        paystub_list_df.at[idx, 'Gross Pay'] += row['General - Gross Pay'] * prorate_rate
        paystub_list_df.at[idx, 'Net Pay'] += row['General - Net Pay'] * prorate_rate
        paystub_list_df.at[idx, 'Taxes'] += row['Taxes - Employee Taxes'] * prorate_rate
        paystub_list_df.at[idx, 'Insurance'] += row['Insurance - Medical'] * prorate_rate
        paystub_list_df.at[idx, '401(k) Employee'] += row['Tax-Advantaged Accounts - 401(k) employee'] * prorate_rate
        paystub_list_df.at[idx, 'HSA Employee'] += row['Tax-Advantaged Accounts - HSA employee'] * prorate_rate
        paystub_list_df.at[idx, '401(k) Employer Match'] += row['Tax-Advantaged Accounts (Employer) - 401(k) employer'] * prorate_rate
        paystub_list_df.at[idx, 'HSA Employer Match'] += row['Tax-Advantaged Accounts (Employer) - HSA employer'] * prorate_rate
        paystub_list_df.at[idx, 'ESPP Total'] += row['Tax-Advantaged Accounts - ESPP'] * prorate_rate
        
        # Prorate for the end month
        prorate_rate = days_in_end_month / days_in_period
        paystub_list_df.at[idx, 'Gross Pay'] += row['General - Gross Pay'] * prorate_rate
        paystub_list_df.at[idx, 'Net Pay'] += row['General - Net Pay'] * prorate_rate
        paystub_list_df.at[idx, 'Taxes'] += row['Taxes - Employee Taxes'] * prorate_rate
        paystub_list_df.at[idx, 'Insurance'] += row['Insurance - Medical'] * prorate_rate
        paystub_list_df.at[idx, '401(k) Employee'] += row['Tax-Advantaged Accounts - 401(k) employee'] * prorate_rate
        paystub_list_df.at[idx, 'HSA Employee'] += row['Tax-Advantaged Accounts - HSA employee'] * prorate_rate
        paystub_list_df.at[idx, '401(k) Employer Match'] += row['Tax-Advantaged Accounts (Employer) - 401(k) employer'] * prorate_rate
        paystub_list_df.at[idx, 'HSA Employer Match'] += row['Tax-Advantaged Accounts (Employer) - HSA employer'] * prorate_rate
        paystub_list_df.at[idx, 'ESPP Total'] += row['Tax-Advantaged Accounts - ESPP'] * prorate_rate
    
    # Now, group by month and aggregate the values
    paystub_list_df['Month'] = paystub_list_df['Pay Period Begin'].dt.to_period('M')
    stats_df = paystub_list_df.groupby('Month').agg({
        'Gross Pay': 'sum',
        'Net Pay': 'sum',
        'Taxes': 'sum',
        'Insurance': 'sum',
        '401(k) Employee': 'sum',
        'HSA Employee': 'sum',
        '401(k) Employer Match': 'sum',
        'HSA Employer Match': 'sum',
        'ESPP Total': 'sum'
    }).reset_index()

    # Round the specified columns to 2 decimal places
    stats_df[['Gross Pay', 'Net Pay', 'Taxes', 'Insurance', '401(k) Employee', 'HSA Employee', '401(k) Employer Match', 'HSA Employer Match', 'ESPP Total']] = stats_df[['Gross Pay', 'Net Pay', 'Taxes', 'Insurance', '401(k) Employee', 'HSA Employee', '401(k) Employer Match', 'HSA Employer Match', 'ESPP Total']].round(2)

    return stats_df



paystub_list_df: pd.DataFrame = build_paystub_list_df(dir_path)
paystub_list_df.to_csv(output_csv_path, index=False, encoding='utf-8')
print(f"Paystubs CSV saved to '{output_csv_path}'")

build_paystub_stats_df(paystub_list_df).to_csv(agg_output_csv_path, index=False, encoding='utf-8')
print(f"Aggregated Paystubs CSV saved to '{agg_output_csv_path}'")

