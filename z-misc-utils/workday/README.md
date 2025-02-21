**02/21/2025**
As I was doing my taxes for 2024, I was confused by some numbers, so I building a "2024 Full Financials" spreadsheet with the following sheets

The included Python `workday_aggregate_excels.py` helps me to build the Raw Income sheet since I can upload the CSV.

Sheets
- Income
  - pivot table loading values from Raw Income
- Raw Income
  - manually exported Workday payslips in XLSX
  - python aggregated
    - actual structured data with columns (`Gross Pay`, etc.)
    - calculated values like `Gross Pay per Month`
- Expenses
  - pivot table for expenses per month
- Raw Expenses
  - Lunch Money transactions CSV export
  - Rent payments manually written
- Overall
  - show Income/Expenses per month