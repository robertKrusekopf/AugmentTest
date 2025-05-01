import xlrd

# Open the Excel files
nachnamen_book = xlrd.open_workbook('Nachnamen.xls')
vornamen_book = xlrd.open_workbook('Vornamen.xls')

# Get the first sheet from each workbook
nachnamen_sheet = nachnamen_book.sheet_by_index(0)
vornamen_sheet = vornamen_book.sheet_by_index(0)

# Print column headers for last names
print("Nachnamen columns:", [nachnamen_sheet.cell_value(0, c) for c in range(nachnamen_sheet.ncols)])

# Print first few rows of last names
print("\nNachnamen first few rows:")
for r in range(1, min(5, nachnamen_sheet.nrows)):
    print([nachnamen_sheet.cell_value(r, c) for c in range(nachnamen_sheet.ncols)])

# Print column headers for first names
print("\nVornamen columns:", [vornamen_sheet.cell_value(0, c) for c in range(vornamen_sheet.ncols)])

# Print first few rows of first names
print("\nVornamen first few rows:")
for r in range(1, min(5, vornamen_sheet.nrows)):
    print([vornamen_sheet.cell_value(r, c) for c in range(vornamen_sheet.ncols)])
