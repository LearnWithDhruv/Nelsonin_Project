from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import logging
import pandas as pd
import time
import requests

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Run in headless mode for no UI
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
            
            if len(ingredients) >= 10:
                break

        if len(ingredients) == 0:
            logging.warning("No ingredients found. Please check the HTML structure and update the selectors.")
    else:
        logging.warning("Failed to find the ingredient elements. Please check the HTML structure.")
    
    return ingredients

def scrape_skinsort(ingredient, base_url, headers):
    try:
        formatted_ingredient = ingredient.replace(" ", "-").lower()
        response = requests.get(base_url + formatted_ingredient, headers=headers)
        if response.status_code != 200:
            print(f"Failed to retrieve page for {ingredient}: Status code {response.status_code}")
            return {}

        soup = BeautifulSoup(response.text, 'html.parser')

        classification = ', '.join([elem.get_text(strip=True) for elem in soup.find_all('div', class_='mr-2 font-semibold text-xs bg-warm-gray-100 lg:bg-white px-4 h-8 min-w-8 rounded-full items-center justify-center flex mt-2')]) if soup.find_all('div', class_='mr-2 font-semibold text-xs bg-warm-gray-100 lg:bg-white px-4 h-8 min-w-8 rounded-full items-center justify-center flex mt-2') else ''
        
        description = soup.find('div', class_='mv-content ingredient-description bg-white rounded-xl p-4 lg:p-0').get_text(strip=True) if soup.find('div', class_='mv-content ingredient-description bg-white rounded-xl p-4 lg:p-0') else ''
        
        compatibility = ', '.join([elem.get_text(strip=True) for elem in soup.find_all('div', class_='bg-white rounded-xl lg:max-w-sm')]) if soup.find_all('div', class_='bg-white rounded-xl lg:max-w-sm') else ''
        
        concerns = ', '.join([elem.get_text(strip=True) for elem in soup.find_all('div', class_='rounded-full text-xs lg:text-sm lg:hover:opacity-75 flex items-center bg-gradient-to-b from-red-100/70 to-orange-100/70 text-red-900 mr-2 mb-2 font-header py-1 font-semibold')]) if soup.find_all('div', class_='rounded-full text-xs lg:text-sm lg:hover:opacity-75 flex items-center bg-gradient-to-b from-red-100/70 to-orange-100/70 text-red-900 mr-2 mb-2 font-header py-1 font-semibold') else ''
        
        benefits = ', '.join([elem.get_text(strip=True) for elem in soup.find_all('div', class_='rounded-full text-xs lg:text-sm lg:hover:opacity-75 flex items-center bg-gradient-to-b from-emerald-100/70 to-green-100/70 text-emerald-900 mr-2 mb-2 font-header py-1 font-semibold')]) if soup.find_all('div', class_='rounded-full text-xs lg:text-sm lg:hover:opacity-75 flex items-center bg-gradient-to-b from-emerald-100/70 to-green-100/70 text-emerald-900 mr-2 mb-2 font-header py-1 font-semibold') else ''
        
        botanical_name = ', '.join([elem.get_text(strip=True) for elem in soup.find_all('span', class_='font-normal text-warm-gray-600')]) if soup.find_all('span', class_='font-normal text-warm-gray-600') else ''
        
        reference = ', '.join([elem.get_text(strip=True) for elem in soup.find_all('div', class_='rounded-xl flex flex-col bg-white lg:max-w-md')]) if soup.find_all('div', class_='rounded-xl flex flex-col bg-white lg:max-w-md') else ''
        
        regulatory_approval = "Data not available"
        environmental_impact = "Data not available"

        return {
            'Ingredient Name': ingredient,
            'Classification': classification,
            'Description': description,
            'Compatibility': compatibility,
            'Concerns': concerns,
            'Benefits': benefits,
            'Botanical Name': botanical_name,
            'Source_Urls': reference,
            'Regulatory Approval': regulatory_approval,
            'Environmental Impact': environmental_impact
        }
    
    except Exception as e:
        print(f"Failed to scrape Skinsort for {ingredient}: {e}")
        return {}

def save_to_csv(data, filename="ingredients_full_details.csv"):
    if data:
        df = pd.DataFrame(data)
        df.to_csv(filename, index=False)
        logging.info(f"CSV file '{filename}' has been created with {len(data)} records.")
    else:
        logging.warning("No data was scraped, no CSV file was created.")

if __name__ == "__main__":
    url = "https://skinsort.com/ingredients"
    
    driver = setup_driver()
    
    try:
        ingredients = scrape_ingredients(driver, url)
    finally:
        driver.quit()

    scraped_data = []
    base_url = 'https://skinsort.com/ingredients/'
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    for ingredient in ingredients:
        ingredient_data = scrape_skinsort(ingredient, base_url, headers)
        if ingredient_data:
            scraped_data.append(ingredient_data)
            print(f"Scraped data for {ingredient}")
        time.sleep(1)  

    save_to_csv(scraped_data)
