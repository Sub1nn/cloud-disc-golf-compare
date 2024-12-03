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

def get_data_par3():

    url_placeholder = 1

    while True:

        all_products = []

        print("getting par3 page")

        page_url = f"https://www.par3.lv/disku-golfa-inventars/page/{url_placeholder}/"
        
        response = requests.get(page_url)

        html_content = response.text

        soup = BeautifulSoup(html_content, 'html.parser')

        ############################################################################################

        parent_div = soup.find('div', class_="products row row-small large-columns-4 medium-columns-3 small-columns-2 has-equal-box-heights")

        if not parent_div:
            break

        products = parent_div.find_all('div', recursive=False)

        for product in products:

            title = product.find('a', class_='woocommerce-LoopProduct-link woocommerce-loop-product__link').get_text(strip=True)

            if product.find('bdi') is not None:
                price_element = product.find_all('bdi')
                if len(price_element) > 1:
                    price_element = price_element[1].get_text(strip=True).replace(' ', '')
                else: 
                    price_element = price_element[0].get_text(strip=True).replace(' ', '')
            else:
                continue
            numeric_value = ''.join([char for char in price_element if char.isdigit() or char == ',' or char == '.'])
            currency_symbol = ''.join([char for char in price_element if not char.isdigit() and char != ',' and char != '.'])
            amount = float(numeric_value.replace(",", "."))

            flight_ratings = {}
            flight_rating_element = product.find('div', class_='box-text box-text-products text-center grid-style-2')
            flight_ratings['Speed'] = flight_rating_element.find('span', class_ = "attribute-Ātrums").get_text(strip=True) if flight_rating_element and flight_rating_element.find('span', class_ = "attribute-Ātrums") else None
            flight_ratings['Glide'] = flight_rating_element.find('span', class_ = "attribute-Planēšana").get_text(strip=True) if flight_rating_element and flight_rating_element.find('span', class_ = "attribute-Planēšana") else None
            flight_ratings['Turn'] = flight_rating_element.find('span', class_ = "attribute-Trajektorijas novirze").get_text(strip=True) if flight_rating_element and flight_rating_element.find('span', class_ = "attribute-Trajektorijas novirze") else None
            flight_ratings['Fade'] = flight_rating_element.find('span', class_ = "attribute-Nozemēšanās novirze").get_text(strip=True) if flight_rating_element and flight_rating_element.find('span', class_ = "attribute-Nozemēšanās novirze") else None

            if flight_ratings.get('Speed') == '':
                flight_ratings['Speed'] = None
            if flight_ratings.get('Glide') == '':
                flight_ratings['Glide'] = None
            if flight_ratings.get('Turn') == '':
                flight_ratings['Turn'] = None
            if flight_ratings.get('Fade') == '':
                flight_ratings['Fade'] = None

            link_to_disc_element = product.find('a')
            link_to_disc = link_to_disc_element['href'] if link_to_disc_element else 'No link found'

            image_element = product.find('img')
            if image_element and "data:image" not in image_element['src']:
                image_url = image_element['src']
            elif image_element and "data:image" in image_element['src']:
                image_url = image_element['nitro-lazy-src']

            result = {
                'title': title,
                'price': amount,
                'currency': currency_symbol,
                'flight_ratings': flight_ratings,
                'link_to_disc': link_to_disc,
                'image_url': image_url,
                'store': "par3.lv"
            }

            all_products.append(result)

        url_placeholder = url_placeholder + 1

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