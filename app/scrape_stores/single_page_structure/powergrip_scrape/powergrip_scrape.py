import sys
import os
import requests

from bs4 import BeautifulSoup
from xml.etree import ElementTree as ET
from requests_html import HTMLSession

current_directory = os.path.dirname(os.path.realpath(__file__))
target_directory_name = 'disc_golf_equipment_price_comparator'
while current_directory:
    sys.path.append(current_directory)
    if os.path.basename(current_directory) == target_directory_name:
        break
    current_directory = os.path.dirname(current_directory)

from handle_db_connections import create_conn

def get_all_pages():

    all_urls = []

    sitemap_url = "https://powergrip.fi/sitemap.xml"

    response = requests.get(sitemap_url)

    if response.status_code == 200:

        sitemap_xml = ET.fromstring(response.content)
        
        urls = [
            url_elem.text for url_elem in sitemap_xml.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if url_elem.text.startswith("https://powergrip.fi/tuote/")
        ]
        
        for url in urls:
            all_urls.append(url)

    else:
        print(f"Failed to retrieve sitemap: {response.status_code}")

    return all_urls

def save_a_page_for_testing():

    page_url = "https://powergrip.fi/tuote/opdiam/latitude-64-opto-diamond"

    session = HTMLSession()

    response = session.get(page_url)

    response.html.render(sleep = 1)
    
    html_content = response.html.html
        
    with open('app\scrape_stores\single_page_structure\powergrip_scrape\powergrip_normal_page.html', 'w', encoding='utf-8') as file:
        file.write(html_content)

def get_page_data(all_urls):

    #with open('app\scrape_stores\single_page_structure\powergrip_scrape\powergrip_normal_page.html', 'r', encoding='utf-8') as file:
        #html_content = file.read()

    connection = create_conn()

    for url in all_urls:

        page_url = url
        session = HTMLSession()
        response = session.get(page_url)
        response.html.render(timeout = 20, sleep = 1)
        html_content = response.html.html
        soup = BeautifulSoup(html_content, 'html.parser')

        ############################################################################################

        title_element = soup.find('div', class_='product-title')
        title = title_element.get_text(strip=True)  

        if soup.find('div', class_='price-tag offer-price'):
            product_element = soup.find('div', class_='price-tag offer-price')
            price = product_element.get_text(strip=True)
        else:
            product_element = soup.find('div', class_='price-tag normal-price')
            price = product_element.get_text(strip=True)
        price = price.replace(' ', '')
        numeric_value = ''.join(char for char in price if char.isdigit() or char in ',.')
        currency_symbol = ''.join(char for char in price if not char.isdigit() and char not in ',.').replace("$", "€")

        '''
        
        ul_element = soup.find('ul', {'id': 'stock-in-store-tabs'})

        if ul_element:

            check_icons = ul_element.find_all('i', {'class': 'fa fa-check fa-fw text-pg-lime'})

            # Determine if any such elements exist
            available = len(check_icons) > 0

            # Now `available` will be True if any such <i> elements are found
            print(available)

        '''
        
        ratings_element = soup.find('div', class_='product-flight-ratings')
        flight_ratings = {}
        translation_map = {
            'Nopeus': 'Speed',
            'Liito': 'Glide',
            'Vakaus': 'Turn',
            'Feidi': 'Fade'
        }
        for li in ratings_element.find_all('li'):
            rating_label = li.find('span', class_='label').get_text(strip=True)
            ratings_value = li.find('span', class_='value').get_text(strip=True)
            translated_label = translation_map.get(rating_label, rating_label) 
            flight_ratings[translated_label] = ratings_value

        image_element = soup.find('img', class_='product-main-image img-fluid')
        image_url = image_element['src']

        ############################################################################################

        product = {
            'title': title,
            'price': numeric_value,
            'currency': currency_symbol,
            'flight_ratings': flight_ratings,
            'link_to_disc': page_url,
            'image_url': image_url,
            'store': "powergrip.fi"
        }

        print(product)

        ############################################################################################

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
            ]

            cursor.executemany(sql, data)
            connection.commit()

    connection.close()

all_urls = get_all_pages()
get_page_data(all_urls)