import pandas as pd
import re

file_path = r'c:\Users\rlao1\AS_APP\견적서\다스 공구실 락볼트 수리비 견적.xlsx'
output_path = r'c:\Users\rlao1\AS_APP\수리견적서 부품.md'

try:
    xls = pd.ExcelFile(file_path)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# 다스 공구실 락볼트 수리비 견적 - 부품 목록\n\n")
        
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(xls, sheet_name=sheet_name, header=None)
            
            # Find the header row (contains 'Description' or '부품명' or 'Model')
            header_row_idx = -1
            for row_idx, row in df.iterrows():
                row_str = " ".join([str(val).lower() for val in row.values])
                if 'description' in row_str or 'model' in row_str or 'unit price' in row_str or '품명' in row_str:
                    header_row_idx = row_idx
                    break
            
            f.write(f"## 시트: {sheet_name}\n\n")
            
            if header_row_idx == -1:
                f.write("> 부품 목록 형식을 찾을 수 없습니다.\n\n")
                continue
                
            # Assume col 0: Name, col 1: Code, col 5: Price based on preview.
            # We better dynamically find columns if possible, but let's stick to the heuristic.
            header_row = df.iloc[header_row_idx]
            desc_col = -1
            code_col = -1
            price_col = -1
            
            for col_idx, val in enumerate(header_row):
                val_str = str(val).lower()
                if 'description' in val_str or '품명' in val_str:
                    desc_col = col_idx
                elif 'model' in val_str or '규격' in val_str or '코드' in val_str:
                    code_col = col_idx
                elif 'unit price' in val_str or '단가' in val_str:
                    price_col = col_idx
            
            # Fallback based on known preview
            if desc_col == -1: desc_col = 0
            if code_col == -1: code_col = 1
            if price_col == -1: price_col = 5
            
            parts_found = []
            
            # Parse from row below header up to TOTAL or empty rows
            for row_idx in range(header_row_idx + 1, len(df)):
                row = df.iloc[row_idx]
                
                # Check for stop words
                row_str = " ".join([str(val).lower() for val in row.values])
                if 'total' in row_str or '네고가' in row_str or '합계' in row_str:
                    break
                
                # Extract columns
                part_name = str(row.iloc[desc_col]) if len(row) > desc_col else "nan"
                part_code = str(row.iloc[code_col]) if len(row) > code_col else "nan"
                price_val = str(row.iloc[price_col]) if len(row) > price_col else "nan"
                
                if part_name.lower() == 'nan' or part_name.strip() == '':
                    continue
                
                # Try to parse price
                try:
                    price_clean = re.sub(r'[^\d]', '', price_val)
                    price_int = int(price_clean) if price_clean else 0
                except:
                    price_int = 0
                    
                # Rule out labor/overhaul if needed, but let's just output everything with a price or code
                # Or output everything that looks like a part!
                if price_int > 0:
                    parts_found.append({
                        'name': part_name.strip(),
                        'code': part_code.strip() if part_code.lower() != 'nan' else '',
                        'price': price_int
                    })
            
            if parts_found:
                f.write("| 부품명/수리내역 | 부품코드 (Model) | 단가(원) |\n")
                f.write("| --- | --- | --- |\n")
                for p in parts_found:
                    f.write(f"| {p['name']} | `{p['code']}` | {p['price']:,} |\n")
            else:
                f.write("> 등록된 부품을 찾을 수 없습니다.\n")
                
            f.write("\n")

    print(f"File generated successfully: {output_path}")

except Exception as e:
    print("Error:", e)
