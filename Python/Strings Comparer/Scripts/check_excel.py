import openpyxl
import os

def check_excel(file_path):
    if not os.path.exists(file_path):
        print(f"File {file_path} not found")
        return
    wb = openpyxl.load_workbook(file_path, read_only=True)
    sheet = wb.active
    print(f"File: {os.path.basename(file_path)}")
    for row in sheet.iter_rows(min_row=1, max_row=1, values_only=True):
        print(f"Headers: {row}")
    wb.close()

base_path = '/Users/elluminati/Documents/Documents/Experimenting/Python/Strings Comparer'
check_excel(os.path.join(base_path, 'app-common-string.xlsx'))
check_excel(os.path.join(base_path, 'customer-app-string.xlsx'))
