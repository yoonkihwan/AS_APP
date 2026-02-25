import re
from datetime import datetime

input_file = r'c:\Users\rlao1\AS_APP\수리견적서 부품.md'
output_file = r'c:\Users\rlao1\AS_APP\수리견적서 부품정리.md'

parts = {}

try:
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    current_year = 0
    valid_year = False
    
    for line in lines:
        if line.startswith('## 시트: '):
            # Extract year from sheet name
            match = re.search(r'(\d{4})[-年]?(\d{1,2})[-月]?(\d{1,2})', line)
            
            if match:
                current_year = int(match.group(1))
            elif '2025' in line:
                current_year = 2025
            elif '2024' in line:
                current_year = 2024
            elif '2026' in line:
                current_year = 2026
            else:
                 current_year = 0
            
            valid_year = current_year >= 2024
            continue
            
        if not valid_year:
            continue
            
        if line.startswith('|') and not line.startswith('| 부품명') and not line.startswith('| ---'):
            # Parse table row
            cols = [col.strip() for col in line.split('|')]
            if len(cols) >= 4:
                name = cols[1]
                code = cols[2].replace('`', '')
                price = cols[3]
                
                # Filter out generic/empty
                if "Overhaul Charge" in name or price == "" or name == "":
                     continue

                key = f"{name}_{code}"
                if key not in parts:
                    parts[key] = {
                        'name': name,
                        'code': code,
                        'price': price
                    }

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# 수리견적서 중복 제거 부품 목록 (2024 ~ 현재)\n\n")
        f.write("| 부품명/수리내역 | 부품코드 (Model) | 단가(원) |\n")
        f.write("| --- | --- | --- |\n")
        for key, p in parts.items():
            f.write(f"| {p['name']} | `{p['code']}` | {p['price']} |\n")

    print(f"File generated successfully: {output_file} with {len(parts)} unique parts.")

except Exception as e:
    print("Error:", e)
