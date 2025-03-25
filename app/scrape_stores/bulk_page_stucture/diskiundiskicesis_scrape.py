import sys
import os
import json
import requests
import logging
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

current_directory = os.path.dirname(os.path.realpath(__file__))
target_directory_name = 'cloud-disc-golf-compare'
while current_directory:
    sys.path.append(current_directory)
    if os.path.basename(current_directory) == target_directory_name:
        break
    current_directory = os.path.dirname(current_directory)

from handle_db_connections import create_conn

def get_data_diskiundiskicesis():
    logger.info("Starting diskiundiskicesis scraper")
    
    try:
        # 1. Fetch page with timeout
        page_url = "https://www.diskiundiskicesis.lv/veikals?page=100"
        try:
            response = requests.get(page_url, timeout=10)
            response.raise_for_status()
        except requests.RequestException as e:
            logger.error(f"Request failed: {str(e)}")
            return []

        # 2. Parse HTML
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'id': 'wix-warmup-data'})

        if not script_tag:
            logger.warning("JSON-containing script not found")
            return []

        # 3. Parse JSON data
        try:
            data = json.loads(script_tag.string.strip())
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON: {str(e)}")
            return []

        # 4. Recursively find products
        def recursive_search(data, target_key):
            if isinstance(data, dict):
                for key, value in data.items():
                    if key == target_key:
                        return value
                    result = recursive_search(value, target_key)
                    if result is not None:
                        return result
            elif isinstance(data, list):
                for item in data:
                    result = recursive_search(item, target_key)
                    if result is not None:
                        return result
            return None

        products_data = recursive_search(data, 'productsWithMetaData')
        if not products_data or not products_data.get('list'):
            logger.warning("No products found in JSON data")
            return []
            
        products = products_data['list']
        all_products = []

        # 5. Process products
        for product in products:
            try:
                # Validate required fields
                if not all(key in product for key in ['name', 'formattedPrice', 'urlPart', 'media']):
                    logger.warning(f"Skipping incomplete product: {product.get('name', 'unknown')}")
                    continue

                # Parse title
                title = product.get('name', '').split('/')[0].rstrip()
                if not title:
                    continue

                # Parse price
                price_element = product.get('formattedComparePrice') or product.get('formattedPrice')
                try:
                    numeric_value = ''.join([char for char in price_element if char.isdigit() or char in (',', '.')])
                    currency_symbol = ''.join([char for char in price_element if not char.isdigit() and char not in (',', '.')]).lstrip()
                    amount = float(numeric_value.replace(",", "."))
                except (ValueError, AttributeError):
                    logger.warning(f"Invalid price format for product: {title}")
                    continue

                # Parse flight ratings
                flight_ratings = {'Speed': None, 'Glide': None, 'Turn': None, 'Fade': None}
                if '/' in product.get('name', ''):
                    name_parts = product['name'].split('/')
                    if len(name_parts) > 1:
                        rating_str = name_parts[-1].strip()
                        if '|' in rating_str:
                            ratings = rating_str.split('|')
                        else:
                            ratings = rating_str.split()
                        
                        if len(ratings) >= 4:
                            flight_ratings = {
                                'Speed': ratings[0].replace(',', '.'),
                                'Glide': ratings[1].replace(',', '.'),
                                'Turn': ratings[2].replace(',', '.'),
                                'Fade': ratings[3].replace(',', '.')
                            }

                # Validate media
                media = product.get('media', [{}])
                image_url = media[0].get("fullUrl") if media and isinstance(media, list) else None

                all_products.append({
                    'title': title,
                    'price': amount,
                    'currency': currency_symbol,
                    'flight_ratings': flight_ratings,
                    'link_to_disc': f"https://www.diskiundiskicesis.lv/product-page/{product['urlPart']}",
                    'image_url': image_url,
                    'store': "diskiundiskicesis.lv"
                })

            except Exception as e:
                logger.error(f"Error processing product: {str(e)}")
                continue

        # 6. Save to database
        if not all_products:
            logger.warning("No valid products found to save")
            return []

        connection = None
        try:
            connection = create_conn()
            with connection.cursor() as cursor:
                sql = """INSERT INTO product_table (...) VALUES (...) ON DUPLICATE KEY UPDATE ..."""
                data = [(p['title'], p['price'], ...) for p in all_products]
                cursor.executemany(sql, data)
                connection.commit()
                logger.info(f"Successfully saved {len(all_products)} products")
                return all_products

        except Exception as e:
            logger.error(f"Database error: {str(e)}")
            return []
            
        finally:
            if connection:
                connection.close()

    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return []