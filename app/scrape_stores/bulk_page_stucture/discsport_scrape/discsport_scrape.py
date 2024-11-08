import sys
import os
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

def save_a_page():

    page_url = "https://www.discsporteurope.com/en/midrange/results,1-200"

    response = requests.get(page_url)
        
    with open('app\scrape_stores\discsport_scrape\discsport_normal_page.html', 'w', encoding='utf-8') as file:
        file.write(response.text)

def get_page_data():

    #with open('app\scrape_stores\discsport_scrape\discsport_normal_page.html', 'r', encoding='utf-8') as file:
        #html_content = file.read()

    page_url = "https://www.discsporteurope.com/en/midrange/results,1-200"

    response = requests.get(page_url)

    html_content = response.text

    soup = BeautifulSoup(html_content, 'html.parser')

    ############################################################################################

    all_products = []

    products = soup.find_all('div', class_='spacer')

    for product in products:

        title = product.find('h3', class_='catProductTitle').get_text(strip=True)

        price_element = product.find('span', class_='PricesalesPrice').get_text(strip=True).replace(' ', '')
        numeric_value = ''.join([char for char in price_element if char.isdigit() or char == ',' or char == '.'])
        currency_symbol = ''.join([char for char in price_element if not char.isdigit() and char != ',' and char != '.'])
        amount = float(numeric_value.replace(",", "."))

        flight_ratings = {}
        speed_tag = product.find('a', class_='flight-speed')
        flight_ratings['Speed'] = speed_tag.find('span').get_text(strip=True) if speed_tag and speed_tag.find('span') else None
        glide_tag = product.find('a', class_='flight-glide')
        flight_ratings['Glide'] = glide_tag.find('span').get_text(strip=True) if glide_tag and glide_tag.find('span') else None
        turn_tag = product.find('a', class_='flight-turn')
        flight_ratings['Turn'] = turn_tag.find('span').get_text(strip=True) if turn_tag and turn_tag.find('span') else None
        fade_tag = product.find('a', class_='flight-fade')
        flight_ratings['Fade'] = fade_tag.find('span').get_text(strip=True) if fade_tag and fade_tag.find('span') else None

        link_to_disc_element = product.find('a')
        link_to_disc = link_to_disc_element['href'] if link_to_disc_element else 'No link found'

        image_element = product.find('img', class_='browseProductImage')
        image_url = image_element['src'] if image_element else 'No image found'

        result = {
            'title': title,
            'price': amount,
            'currency': currency_symbol,
            'flight_ratings': flight_ratings,
            'link_to_disc': "https://www.discsporteurope.com" + link_to_disc,
            'image_url': "https://www.discsporteurope.com" + image_url,
            'store': "discsporteurope.com"
        }

        all_products.append(result)

    print(all_products)

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

get_page_data()