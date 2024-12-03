import sys
import os
import json
import requests

from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET

current_directory = os.path.dirname(os.path.realpath(__file__))
target_directory_name = 'disc_golf_equipment_price_comparator'
while current_directory:
    sys.path.append(current_directory)
    if os.path.basename(current_directory) == target_directory_name:
        break
    current_directory = os.path.dirname(current_directory)

from handle_db_connections import create_conn

def get_data_diskiundiskicesis():

    print("getting diskiundiskicesis page")

    page_url = "https://www.diskiundiskicesis.lv/veikals?page=100"

    response = requests.get(page_url)

    html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')

    ############################################################################################

    script_tag = soup.find('script', {'id': 'wix-warmup-data'})

    if script_tag:

        json_content = script_tag.string.strip()

        data = json.loads(json_content)

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

        products = recursive_search(data, 'productsWithMetaData').get('list')

    else:
        print("JSON-containing script not found.")

    ############################################################################################

    all_products = []

    for product in products:

        title = product.get('name').split('/')[0].rstrip()

        if product.get('formattedComparePrice') == '':
            price_element = product.get('formattedPrice')
        else:
            price_element = product.get('formattedComparePrice')
        numeric_value = ''.join([char for char in price_element if char.isdigit() or char == ',' or char == '.'])
        currency_symbol = ''.join([char for char in price_element if not char.isdigit() and char != ',' and char != '.']).lstrip()
        amount = float(numeric_value.replace(",", "."))

        flight_ratings = {}
        if 'name' in product and '/' in product['name']:
            name_parts = product.get('name').split('/')
            if len(name_parts) > 1:
                flight_rating_elements = name_parts[-1].strip().split(' ')
                flight_ratings['Speed'] = flight_rating_elements[0] 
                flight_ratings['Glide'] = flight_rating_elements[1] 
                flight_ratings['Turn'] = flight_rating_elements[2] 
                flight_ratings['Fade'] = flight_rating_elements[3] 

                if flight_ratings.get('Glide') == '|':
                    flight_rating_elements = name_parts[-1].strip().split('|')
                    flight_ratings['Speed'] = flight_rating_elements[0] 
                    flight_ratings['Glide'] = flight_rating_elements[1] 
                    flight_ratings['Turn'] = flight_rating_elements[2] 
                    flight_ratings['Fade'] = flight_rating_elements[3] 

                if ',' in flight_ratings.get('Speed'):
                    flight_ratings['Speed'] = flight_ratings.get('Speed').replace(',', '.')
                if ',' in flight_ratings.get('Glide'):
                    flight_ratings['Glide'] = flight_ratings.get('Glide').replace(',', '.')
                if ',' in flight_ratings.get('Turn'):
                    flight_ratings['Turn'] = flight_ratings.get('Turn').replace(',', '.')
                if ',' in flight_ratings.get('Fade'):
                    flight_ratings['Fade'] = flight_ratings.get('Fade').replace(',', '.')

        else:
            flight_ratings['Speed'] = None
            flight_ratings['Glide'] = None
            flight_ratings['Turn'] = None
            flight_ratings['Fade'] = None

        link_to_disc = "https://www.diskiundiskicesis.lv/product-page/" + product.get("urlPart")

        image_url = product.get('media')[0].get("fullUrl")

        ############################################################################################

        result = {
            'title': title,
            'price': amount,
            'currency': currency_symbol,
            'flight_ratings': flight_ratings,
            'link_to_disc': link_to_disc,
            'image_url': image_url,
            'store': "diskiundiskicesis.lv"
        }

        all_products.append(result)

    ############################################################################################

    connection = create_conn()

    try:

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
            
            data = [
                (
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
                )
                for product in all_products
            ]

            cursor.executemany(sql, data)
            connection.commit()

    finally:
        
        connection.close()