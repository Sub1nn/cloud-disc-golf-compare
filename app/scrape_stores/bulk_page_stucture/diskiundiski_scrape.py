import sys
import os
import hashlib
import requests

from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET

current_directory = os.path.dirname(os.path.realpath(__file__))
app_directory = os.path.abspath(os.path.join(current_directory, '..', '..'))
sys.path.append(app_directory)

from handle_db_connections import create_conn

def get_data_diskiundiskicesis():

    url_placeholder = 1

    while True:

        all_products = []

        print("getting diskiundiski page")

        page_url = f"https://diskiundiski.lv/collections/all?page={url_placeholder}"

        response = requests.get(page_url)

        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        ############################################################################################

        products = soup.find_all('div', class_='o-layout__item u-1/2 u-1/3@tab u-1/4-grid-desk')

        if products == []:
            break

        for product in products:

            title = product.find('product-card-title').get_text().split('/')[0].rstrip()

            price_element = product.find('span', class_='money').get_text()
            numeric_value = ''.join([char for char in price_element if char.isdigit() or char == ',' or char == '.'])
            currency_symbol = ''.join([char for char in price_element if not char.isdigit() and char != ',' and char != '.']).lstrip()
            amount = float(numeric_value.replace(",", "."))

            flight_ratings = {}
            if '/' in product.find('product-card-title').get_text():
                name_parts = product.find('product-card-title').get_text().split('/')
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

            link_to_disc = "https://diskiundiski.lv" + product.find('a')['href']

            image_url = "https://" + product.find("img", class_="product-card__img")['src'].replace("//", "")

            ############################################################################################

            result = {
                'title': title,
                'price': amount,
                'currency': currency_symbol,
                'flight_ratings': flight_ratings,
                'link_to_disc': link_to_disc,
                'image_url': image_url,
                'store': "diskiundiski.lv"
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

get_data_diskiundiskicesis()