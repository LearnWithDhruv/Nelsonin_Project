from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import time
import pandas as pd
import logging
import requests
import json
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    return driver

# Function to get product links from search results
def get_product_links(driver, search_url, num_products):
    driver.get(search_url)
    time.sleep(3)
    
    product_links = set()
    while len(product_links) < num_products:
        soup = BeautifulSoup(driver.page_source, 'html.parser')
        product_list = soup.find_all('a', {'class': 'a-link-normal s-no-outline'})
        
        for link in product_list:
            if len(product_links) >= num_products:
                break
            href = link.get('href')
            full_url = f"https://www.amazon.in{href}"
            product_links.add(full_url)
        
        try:
            next_button = driver.find_element(By.CSS_SELECTOR, 'li.a-last a')
            if next_button:
                next_button.click()
                time.sleep(3)
            else:
                break
        except:
            break 
    
    return list(product_links)

def scrape_product_page(driver, url, category, subcategory):
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    product_name = soup.find('span', {'id': 'productTitle'}).text.strip() if soup.find('span', {'id': 'productTitle'}) else "N/A"

    brand = "N/A"
    brand_element = soup.find('a', {'id': 'bylineInfo'}) or soup.find('span', {'class': 'author notFaded'})
    if brand_element:
        brand = brand_element.text.strip()

    price = "N/A"
    price_whole = soup.find('span', {'class': 'a-price-whole'})
    price_fraction = soup.find('span', {'class': 'a-price-fraction'})
    if price_whole and price_fraction:
        price = f"{price_whole.text.strip()}.{price_fraction.text.strip()}"

    description = "N/A"
    description_element = soup.find('div', {'id': 'productDescription'}) or soup.find('div', {'id': 'feature-bullets'})
    if description_element:
        description = description_element.text.strip()

    ingredients = "N/A"

    ingredient_patterns = [
        r'ingredients?:\s*(.*?)(?=\n|\r|\<)',
        r'composition:\s*(.*?)(?=\n|\r|\<)',
        r'key ingredients:\s*(.*?)(?=\n|\r|\<)'
    ]

    def extract_ingredients(text):
        for pattern in ingredient_patterns:
            match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
            if match:
                return match.group(1).strip()
        return "N/A"

    product_details = soup.find('div', {'id': 'productDetails_feature_div'})
    if product_details:
        details_text = product_details.get_text(separator=' ', strip=True).lower()
        ingredients = extract_ingredients(details_text)

    if ingredients == "N/A" and description_element:
        desc_text = description_element.get_text(separator=' ', strip=True).lower()
        ingredients = extract_ingredients(desc_text)

    if ingredients == "N/A":
        bullets = soup.find('div', {'id': 'feature-bullets'})
        if bullets:
            bullet_text = bullets.get_text(separator=' ', strip=True).lower()
            ingredients = extract_ingredients(bullet_text)

    images = [img['src'] for img in soup.find_all('img', {'class': 'a-dynamic-image'})]
    customer_ratings = soup.find('span', {'class': 'a-icon-alt'}).text.strip() if soup.find('span', {'class': 'a-icon-alt'}) else "N/A"

    manufacturer = "N/A"
    seller = "N/A"
    packaging = "N/A"
    details_section = soup.find('div', {'id': 'detailBullets_feature_div'})
    if details_section:
        for li in details_section.find_all('li'):
            text = li.text.lower()
            if 'manufacturer' in text:
                manufacturer = li.find('span', {'class': 'a-text-bold'}).find_next_sibling('span').text.strip()
            elif 'seller' in text:
                seller = li.find('span', {'class': 'a-text-bold'}).find_next_sibling('span').text.strip()
            elif 'packaging' in text:
                packaging = li.find('span', {'class': 'a-text-bold'}).find_next_sibling('span').text.strip()

    video_url = "N/A"
    video_element = soup.find('div', {'id': 'videoBlock_feature_div'})
    if video_element:
        video_url = "Video available (URL not directly accessible)"

    logging.info(f"Scraped data for URL: {url}")
    logging.info(f"Ingredients: {ingredients}")

    return {
        'ProductName': product_name,
        'Brand': brand,
        'Category': category,
        'Subcategory': subcategory,
        'Description': description,
        'Price': price,
        'Ingredients': ingredients,
        'Images': ', '.join(images),
        'CustomerRatings': customer_ratings,
        'Manufacturer': manufacturer,
        'Seller': seller,
        'ProductPackaging': packaging,
        'ProductVideo': video_url,
        'SourceURL': url
    }

def save_to_csv(products, filename='product_catalog_12.csv'):
    df = pd.DataFrame(products)
    df.to_csv(filename, index=False)
    logging.info(f"Product catalog saved to {filename}")

def send_to_api(product_data):
    url = 'http://localhost:5000/add_product'
    headers = {'Content-Type': 'application/json'}
    try:
        response = requests.post(url, data=json.dumps(product_data), headers=headers)
        if response.status_code == 201:
            print("Products added successfully")
        else:
            print(f"Failed to add product: {response.json()}")
    except Exception as e:
        print(f"Error sending product to API: {e}")

if __name__ == "__main__":
    categories = [
        {'search_url': 'https://www.amazon.in/s?k=hair+care', 'category': 'Hair Care', 'subcategory': 'Shampoo'},
        {'search_url': 'https://www.amazon.in/s?k=skin+care', 'category': 'Skin Care', 'subcategory': 'Face Wash'},
        {'search_url': 'https://www.amazon.in/s?k=body+care', 'category': 'Body Care', 'subcategory': 'Body Lotion'},
        {'search_url': 'https://www.amazon.in/s?k=lip+care', 'category': 'Lip Care', 'subcategory': 'Lip Balm'},
        {'search_url': 'https://www.amazon.in/s?k=foot+care', 'category': 'Foot Care', 'subcategory': 'Foot Cream'},
    ]

    driver = setup_driver()
    all_scraped_products = []

    for category in categories:
        product_links = get_product_links(driver, category['search_url'], num_products=30)
        logging.info(f"Found {len(product_links)} products for category: {category['category']}")

        for link in product_links:
            try:
                product_data = scrape_product_page(driver, link, category['category'], category['subcategory'])
                all_scraped_products.append(product_data)
                logging.info(f"Scraped: {product_data['ProductName']}")
                time.sleep(2) 
            except Exception as e:
                logging.error(f"Error processing {link}: {e}")

    driver.quit()
    save_to_csv(all_scraped_products)

