import pandas as pd
import sys

file_path = r"c:\Users\rlao1\AS_APP\as_app\견적서\다스 공구실 락볼트 수리비 견적.xlsx"
try:
    df = pd.read_excel(file_path, sheet_name=0)
    print("--- FIRST 50 ROWS ---")
    print(df.head(50).to_string())
except Exception as e:
    print(f"Error reading excel file: {e}")
