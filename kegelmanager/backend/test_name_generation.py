import xlrd
import random

def load_names_from_excel(file_path):
    """Load names and their cumulative frequencies from an Excel file."""
    book = xlrd.open_workbook(file_path)
    sheet = book.sheet_by_index(0)
    
    names = []
    frequencies = []
    
    for r in range(sheet.nrows):
        if r == 0:  # Skip header row if it exists
            continue
        
        name = sheet.cell_value(r, 0)
        frequency = sheet.cell_value(r, 1)
        
        names.append(name)
        frequencies.append(frequency)
    
    return names, frequencies

def select_random_name(names, frequencies):
    """Select a random name based on cumulative frequencies."""
    # Get the maximum cumulative frequency (last value)
    max_frequency = frequencies[-1]
    
    # Generate a random number between 0 and max_frequency
    random_value = random.uniform(0, max_frequency)
    
    # Find the first name with a cumulative frequency greater than the random value
    for i, freq in enumerate(frequencies):
        if random_value <= freq:
            return names[i]
    
    # Fallback (should not happen)
    return names[-1]

# Load names from Excel files
first_names, first_name_freqs = load_names_from_excel('Vornamen.xls')
last_names, last_name_freqs = load_names_from_excel('Nachnamen.xls')

print(f"Loaded {len(first_names)} first names and {len(last_names)} last names")

# Generate 20 random full names
print("\nGenerated random names:")
for _ in range(20):
    first_name = select_random_name(first_names, first_name_freqs)
    last_name = select_random_name(last_names, last_name_freqs)
    print(f"{first_name} {last_name}")
