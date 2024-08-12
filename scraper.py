from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import logging
import re
import time
import requests, json

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

def extract_ingredients(driver, url):
    try:
        driver.get(url)
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
        time.sleep(5)
        soup = BeautifulSoup(driver.page_source, 'html.parser')

        ingredients = "N/A"

        def extract_ingredients_from_section(section):
            if not section:
                return None
            text = section.get_text(separator=' ', strip=True).lower()
            patterns = [
                r'ingredients?\s*[:\-]\s*(.*?)(?=\.\s|$)',
                r'composition\s*[:\-]\s*(.*?)(?=\.\s|$)',
                r'key ingredients?\s*[:\-]\s*(.*?)(?=\.\s|$)'
            ]
            for pattern in patterns:
                match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
                if match:
                    return match.group(1).strip()
            return None

        possible_sections = [
            soup.find('div', {'id': 'productDetails_feature_div'}),
            soup.find('div', {'id': 'feature-bullets'}),
            soup.find('div', {'id': 'importantInformation'}),
            soup.find('div', {'id': 'productDescription'}),
            soup.find('div', {'id': 'aplus'}),
            soup.find('div', {'id': 'descriptionAndDetails'})
        ]

        for section in possible_sections:
            if section:
                ingredients = extract_ingredients_from_section(section)
                if ingredients:
                    break

        if ingredients != "N/A":
            ingredients = re.sub(r'\s+', ' ', ingredients)
            ingredients = ingredients.strip()
        
        return ingredients if ingredients else "Ingredients not found"
    except Exception as e:
        logging.exception(f"Error extracting ingredients for URL {url}: {e}")
        return f"Error: {str(e)}"

def scrape_product_page(driver, url, category, subcategory):
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')

    product_name = soup.find('span', {'id': 'productTitle'}).text.strip() if soup.find(
        'span', {'id': 'productTitle'}) else "N/A"

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
    description_element = soup.find('div', {'id': 'productDescription'}) or soup.find('div',
                                                                                      {'id': 'feature-bullets'})
    if description_element:
        description = description_element.get_text(separator=' ', strip=True)

    ingredients = extract_ingredients(driver, url)

    images = [img['src'] for img in soup.find_all('img', {'class': 'a-dynamic-image'})]
    customer_ratings = soup.find('span', {'class': 'a-icon-alt'}).text.strip() if soup.find(
        'span', {'class': 'a-icon-alt'}) else "N/A"

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
        'product_name': product_name,
        'brand': brand,
        'category': category,
        'sub_category': subcategory,
        'description': description,
        'price': price,
        'ingredients': ingredients,
        'images': ', '.join(images),
        'customer_ratings': customer_ratings,
        'manufacturer': manufacturer,
        'seller': seller,
        'product_packaging': packaging,
        'product_video': video_url,
        'source_url': url
    }

def save_to_csv(products, filename='product_catalog_14.csv'):
    """Saves the scraped product data to a CSV file."""
    df = pd.DataFrame(products)
    df.to_csv(filename, index=False)
    logging.info(f"Product catalog saved to {filename}")

def send_to_api(product_data):
    """Sends product data to an external API."""
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
        product_links = get_product_links(driver, category['search_url'], num_products=2)
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
