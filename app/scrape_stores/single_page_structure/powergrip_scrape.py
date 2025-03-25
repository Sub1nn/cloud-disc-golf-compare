import sys
import os
import requests
import time
import logging
from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
from requests_html import HTMLSession
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

current_directory = os.path.dirname(os.path.realpath(__file__))
target_directory_name = 'cloud-disc-golf-compare'
while current_directory:
    sys.path.append(current_directory)
    if os.path.basename(current_directory) == target_directory_name:
        break
    current_directory = os.path.dirname(current_directory)

from handle_db_connections import create_conn

def get_all_pages_powergrip():
    """Fetch all product URLs from Powergrip sitemap"""
    all_urls = []
    sitemap_url = "https://powergrip.fi/sitemap.xml"

    try:
        response = requests.get(sitemap_url, timeout=10)
        response.raise_for_status()
        
        sitemap_xml = ET.fromstring(response.content)
        today = datetime.now()
        current_month = today.month
        current_year = today.year

        if current_month == 1:
            previous_month = 12
            previous_year = current_year - 1
        else:
            previous_month = current_month - 1
            previous_year = current_year
        
        for url_element in sitemap_xml.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}url'):
            loc = url_element.find('{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            lastmod = url_element.find('{http://www.sitemaps.org/schemas/sitemap/0.9}lastmod')
            
            if loc is not None and lastmod is not None:
                url = loc.text
                try:
                    lastmod_date = datetime.strptime(lastmod.text.split('T')[0], '%Y-%m-%d')
                    if ((lastmod_date.year == current_year and lastmod_date.month == current_month) or 
                        (lastmod_date.year == previous_year and lastmod_date.month == previous_month)):
                        if url.startswith("https://powergrip.fi/tuote/"):
                            all_urls.append(url)
                except ValueError:
                    continue

        logger.info(f"Found {len(all_urls)} product URLs from sitemap")
        return all_urls

    except Exception as e:
        logger.error(f"Failed to fetch sitemap: {str(e)}")
        return []

def get_data_powergrip(all_urls):
    """Scrape product data from Powergrip URLs"""
    if not all_urls:
        logger.warning("No URLs provided to scraper")
        return

    connection = None
    try:
        connection = create_conn()
        session = HTMLSession(browser_args=[
            '--no-sandbox',
            '--single-process',
            '--disable-dev-shm-usage'
        ])

        for url in all_urls:
            try:
                logger.info(f"Processing: {url}")
                
                # Fetch page with retry logic
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        response = session.get(url, timeout=30)
                        response.html.render(timeout=30, sleep=2)
                        html_content = response.html.html
                        break
                    except Exception as e:
                        if attempt == max_retries - 1:
                            raise
                        time.sleep(5)
                        continue

                soup = BeautifulSoup(html_content, 'html.parser')

                # Extract title with validation
                title_element = soup.find('div', class_='product-title')
                if not title_element:
                    logger.warning(f"Skipping - no title found: {url}")
                    continue
                title = title_element.get_text(strip=True)

                # Extract price with validation
                price_element = (soup.find('div', class_='price-tag offer-price') or 
                                soup.find('div', class_='price-tag normal-price'))
                if not price_element:
                    logger.warning(f"Skipping - no price found: {url}")
                    continue
                    
                price = price_element.get_text(strip=True).replace(' ', '')
                try:
                    numeric_value = ''.join(char for char in price if char.isdigit() or char in ',.')
                    currency_symbol = ''.join(char for char in price if not char.isdigit() and char not in ',.').replace("$", "€")
                    float(numeric_value.replace(",", "."))  # Validate numeric value
                except ValueError:
                    logger.warning(f"Invalid price format: {price} in {url}")
                    continue

                # Extract flight ratings with validation
                flight_ratings = {'Speed': None, 'Glide': None, 'Turn': None, 'Fade': None}
                ratings_element = soup.find('div', class_='product-flight-ratings')
                
                if ratings_element:
                    translation_map = {
                        'Nopeus': 'Speed',
                        'Liito': 'Glide',
                        'Vakaus': 'Turn',
                        'Feidi': 'Fade'
                    }
                    for li in ratings_element.find_all('li'):
                        try:
                            rating_label = li.find('span', class_='label').get_text(strip=True)
                            ratings_value = li.find('span', class_='value').get_text(strip=True)
                            translated_label = translation_map.get(rating_label, rating_label) 
                            flight_ratings[translated_label] = ratings_value
                        except AttributeError:
                            continue

                # Extract image URL with validation
                image_element = soup.find('img', class_='product-main-image')
                image_url = image_element['src'] if image_element and 'src' in image_element.attrs else None

                # Prepare product data
                product = {
                    'title': title,
                    'price': numeric_value,
                    'currency': currency_symbol,
                    'flight_ratings': flight_ratings,
                    'link_to_disc': url,
                    'image_url': image_url,
                    'store': "powergrip.fi"
                }

                # Save to database
                with connection.cursor() as cursor:
                    sql = """
                    INSERT INTO product_table (title, price, currency, speed, glide, turn, fade, link_to_disc, image_url, store)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    ON DUPLICATE KEY UPDATE
                    price = VALUES(price),
                    currency = VALUES(currency),
                    speed = VALUES(speed),
                    glide = VALUES(glide),
                    turn = VALUES(turn),
                    fade = VALUES(fade),
                    link_to_disc = VALUES(link_to_disc),
                    image_url = VALUES(image_url);
                    """
                    
                    cursor.execute(sql, (
                        product['title'],
                        product['price'],
                        product['currency'],
                        product['flight_ratings']['Speed'],
                        product['flight_ratings']['Glide'],
                        product['flight_ratings']['Turn'],
                        product['flight_ratings']['Fade'],
                        product['link_to_disc'],
                        product['image_url'],
                        product['store']
                    ))
                    connection.commit()

                logger.info(f"Saved: {title}")

            except Exception as e:
                logger.error(f"Failed to process {url}: {str(e)}")
                continue

    except Exception as e:
        logger.error(f"Scraper failed: {str(e)}")
    finally:
        if connection:
            connection.close()
        if 'session' in locals():
            session.close()