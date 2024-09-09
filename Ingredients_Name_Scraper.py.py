# import requests
# import pandas as pd

# # Step 1: Define the PubChem API URL
# base_url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/name"

# # Step 2: Prepare a list of sample ingredient names to fetch from the API
# sample_names = ['Aspirin', 'Caffeine', 'Acetaminophen', 'Ibuprofen', 'Lactic Acid']
# ingredients = []

# # Step 3: Loop through the sample ingredient names
# for name in sample_names:
#     url = f"{base_url}/{name}/synonyms/JSON"
#     response = requests.get(url)
    
#     if response.status_code == 200:
#         data = response.json()
#         synonyms = data.get('InformationList', {}).get('Information', [{}])[0].get('Synonym', [])
#         ingredients.extend(synonyms)
#     else:
#         print(f"Failed to retrieve data for {name}")
    
#     # To prevent making too many API requests, let's stop after a few items.
#     if len(ingredients) >= 1000:
#         break

# # Step 4: Save the ingredient names to a CSV file
# df = pd.DataFrame(ingredients, columns=["Ingredient Name"])
# df.to_csv("ingredients.csv", index=False)
# print("CSV file 'ingredients.csv' has been created.")


from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging
import pandas as pd
import time

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

def scrape_ingredients(driver, url):
    logging.info(f"Accessing {url}")
    driver.get(url)
    time.sleep(5)  

    soup = BeautifulSoup(driver.page_source, 'html.parser')
    
    ingredient_elements = soup.find_all('h4', class_='mb-1 leading-tight text-blue-gray-700 group-hover:underline font-header text-xl font-bold hover:underline whitespace-normal overflow-hidden')

    ingredients = []
    if ingredient_elements:
        for element in ingredient_elements:
            name = element.get_text(strip=True)
            ingredients.append(name)
            
            if len(ingredients) >= 1000:
                break

        if len(ingredients) == 0:
            logging.warning("No ingredients found. Please check the HTML structure and update the selectors.")
    else:
        logging.warning("Failed to find the ingredient elements. Please check the HTML structure.")
    
    return ingredients

def save_to_csv(ingredients, filename="ingredients.csv"):
    if ingredients:
        df = pd.DataFrame(ingredients, columns=["Ingredient Name"])
        df.to_csv(filename, index=False)
        logging.info(f"CSV file '{filename}' has been created with {len(ingredients)} ingredients.")
    else:
        logging.warning("No ingredients were scraped, no CSV file was created.")

if __name__ == "__main__":
    url = "https://skinsort.com/ingredients"
    
    driver = setup_driver()
    
    try:
        ingredients = scrape_ingredients(driver, url)
        
        save_to_csv(ingredients)
    finally:
        driver.quit()
