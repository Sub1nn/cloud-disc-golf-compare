import sys
import os
import hashlib

from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
from requests_html import HTMLSession

current_directory = os.path.dirname(os.path.realpath(__file__))
target_directory_name = 'cloud-disc-golf-compare'
while current_directory:
    sys.path.append(current_directory)
    if os.path.basename(current_directory) == target_directory_name:
        break
    current_directory = os.path.dirname(current_directory)

from handle_db_connections import create_conn

def get_data_discking():

    url_placeholder = 1

    while True:

        all_products = []

        print("getting discking page")

        page_url = f"https://kiekkokingi.fi/collections/uudet-frisbeegolfkiekot?page={url_placeholder}&grid_list=grid-view"

        session = HTMLSession()

        response = session.get(page_url)

        response.html.render(timeout=20, sleep=2)
        
        html_content = response.html.html

        soup = BeautifulSoup(html_content, 'html.parser')

        ############################################################################################

        products = soup.find_all('article', class_='productitem')

        if products == []:
            break

        for product in products:

            title = product.find('h2', class_='productitem--title').get_text(strip=True)

            price_element = product.find_all('span', class_='money')
            if len(price_element) > 1:
                price_element = price_element[1].get_text(strip=True).replace(' ', '')
            else: 
                price_element = price_element[0].get_text(strip=True).replace(' ', '')
            numeric_value = ''.join([char for char in price_element if char.isdigit() or char == ',' or char == '.']).replace(',', '.')
            currency_symbol = ''.join([char for char in price_element if not char.isdigit() and char != ',' and char != '.']).strip()
            numeric_amount = float(numeric_value)
                        
            flight_ratings = {}
            flight_ratings_list = product.find_all('div', class_='tooltip')
            flight_ratings['Speed'] = flight_ratings_list[0].contents[0].strip() if len(flight_ratings_list) > 0 else None
            flight_ratings['Glide'] = flight_ratings_list[1].contents[0].strip() if len(flight_ratings_list) > 0 else None
            flight_ratings['Turn'] = flight_ratings_list[2].contents[0].strip() if len(flight_ratings_list) > 0 else None
            flight_ratings['Fade'] = flight_ratings_list[3].contents[0].strip() if len(flight_ratings_list) > 0 else None  

            link_to_disc_element = product.find('a', class_='productitem--image-link')
            link_to_disc = link_to_disc_element['href'] if link_to_disc_element else 'No link found'

            image_element = product.find('img', class_='productitem--image-primary')
            image_url = image_element['src'] if image_element else 'No image found'

            result = {
                'title': title,
                'price': numeric_amount,
                'currency': currency_symbol,
                'flight_ratings': flight_ratings,
                'link_to_disc': "https://kiekkokingi.fi/" + link_to_disc,
                'image_url': image_url,
                'store': "kiekkokingi.fi"
            }

            combined = f"{result.get('title')}_{result.get('store')}"
            combined = combined.lower().replace(' ', '')
            unique_id = hashlib.sha256(combined.encode()).hexdigest()

            result["unique_id"] = unique_id

            all_products.append(result)

        url_placeholder = url_placeholder + 1

        ############################################################################################

        connection = create_conn()

        try:

            with connection.cursor() as cursor:

                sql = """
                INSERT INTO product_table (unique_id, title, price, currency, speed, glide, turn, fade, link_to_disc, image_url, store)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                unique_id = VALUES(unique_id),
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
                        product['unique_id'],
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

get_data_discking()