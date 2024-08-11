import os
import re
import csv
import shutil
from selenium.webdriver.chrome.options import Options
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

chrome_driver_path = shutil.which("chromedriver")

# Set Chrome options
options = Options()
options.add_argument('--headless')  # Run in headless mode if needed
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

# Create the ChromeDriver service
service = Service(executable_path=chrome_driver_path)

# Initialize the Chrome WebDriver
driver = webdriver.Chrome(service=service, options=options)

print('driver found')

# Navigate to the target URL
driver.get("https://xgn.karnataka.gov.in/CSHARP/ALLConsentOrder.aspx")

# Initialize variables
pg_no = 1
data_folder = "./data"
existing_rows = []
new_data = []

# Ensure the data directory exists
os.makedirs(data_folder, exist_ok=True)

# Read existing CSV data from files in numerical order
def numerical_sort(value):
    parts = re.findall(r'\d+', value)
    return int(parts[0]) if parts else 0

file_names = sorted(
    [f for f in os.listdir(data_folder) if f.startswith("page_") and f.endswith(".csv")],
    key=numerical_sort
)

for file_name in file_names:
    with open(os.path.join(data_folder, file_name), mode='r') as file:
        csv_reader = csv.reader(file)
        next(csv_reader)  # Skip header
        for row in csv_reader:
            if row:  # Skip empty rows
                existing_rows.append(tuple(row))  # Use tuple for faster lookup

# Function to check if a row exists in existing data
def is_duplicate(row):
    return tuple(row) in existing_rows

# Scrape the table and handle pagination
while True:
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.ID, "dgPro")))
    print('scraping')
    table = driver.find_element(By.ID, "dgPro")
    rows = table.find_elements(By.TAG_NAME, "tr")

    found_duplicate = False
    for row in rows[2:]:  # Skip the first two header rows
        cols = [col.text.strip() for col in row.find_elements(By.TAG_NAME, 'td')]

        if is_duplicate(cols):
            found_duplicate = True
            break
        else:
            new_data.append(cols)
    
    if found_duplicate:
        break

    pg_no += 1
    try:
        link = driver.find_element(By.LINK_TEXT, str(pg_no))
    except NoSuchElementException:
        try:
            link = driver.find_elements(By.LINK_TEXT, '...')[0 if pg_no == 11 else 1]
        except IndexError:
            break
    link.click()

driver.quit()

# Combine new data with existing data
combined_data = new_data + [list(row) for row in existing_rows]

# Function to write data to CSV files
def write_to_csv(data, file_index):
    output_file = os.path.join(data_folder, f"page_{file_index}.csv")
    with open(output_file, 'w', newline='') as csv_file:
        writer = csv.writer(csv_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_ALL)
        
        # Writing the headers
        headers = ['Inw', 'Industry Name', 'Industry Colour', 'Regional Office', 'Inw Dt', 'Inw Type', 'Inw Status', 'Insp ID', 'Grt Dt', 'Consent No', 'Uploaded Doc', 'Validity', 'e_outwardval']
        writer.writerow(headers)
        
        for row in data:
            writer.writerow(row)

# Write the combined data to CSV files, each with a maximum of 100 entries
file_index = 1
for i in range(0, len(combined_data), 100):
    write_to_csv(combined_data[i:i+100], file_index)
    file_index += 1
