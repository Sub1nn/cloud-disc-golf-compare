import json
import requests
import sys
import os

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from handle_db_connections import create_conn
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from requests_html import HTMLSession

def site_map_process():

    sitemap_url = "https://powergrip.fi/sitemap.xml"

    response = requests.get(sitemap_url)

    if response.status_code == 200:

        sitemap_xml = ET.fromstring(response.content)
        
        urls = [
            url_elem.text for url_elem in sitemap_xml.findall('.//{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
            if url_elem.text.startswith("https://powergrip.fi/tuote/")
        ]
        
        for url in urls:
            print(url)

    else:
        print(f"Failed to retrieve sitemap: {response.status_code}")

def save_a_page_for_testing():

    page_url = "https://discking.eu/collections/new-disc-golf-discs?grid_list=grid-view"

    session = HTMLSession()

    response = session.get(page_url)

    response.html.render(sleep = 1)
    
    html_content = response.html.html

    with open('discking_scrape\discking_dynamic_page.html', 'w', encoding='utf-8') as file:
        file.write(html_content)

def get_page_data_for_testing():

    with open('discking_scrape\discking_dynamic_page.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    ############################################################################################

    all_products = []

    product_articles = soup.find_all('article', class_='productitem')

    for article in product_articles:

        name = article.find('h2', class_='productitem--title').get_text(strip=True)

        price = article.find('span', class_='money').get_text(strip=True)

        flight_ratings = {}
        flight_ratings_list = article.find_all('div', class_='tooltip')
        flight_ratings['Speed'] = flight_ratings_list[0].contents[0].strip() if len(flight_ratings_list) > 0 else 'N/A'
        flight_ratings['Glide'] = flight_ratings_list[1].contents[0].strip() if len(flight_ratings_list) > 0 else 'N/A'
        flight_ratings['Turn'] = flight_ratings_list[2].contents[0].strip() if len(flight_ratings_list) > 0 else 'N/A'
        flight_ratings['Fade'] = flight_ratings_list[3].contents[0].strip() if len(flight_ratings_list) > 0 else 'N/A'  

        #manufacturer_tag = article.find('h3', class_='productitem--vendor')
        #manufacturer = manufacturer_tag.get_text(strip=True) if manufacturer_tag else 'Unknown Manufacturer'

        link_to_disc_tag = article.find('a', class_='productitem--image-link')
        link_to_disc = link_to_disc_tag['href'] if link_to_disc_tag else 'No link found'

        image_tag = article.find('img', class_='productitem--image-primary')
        image_url = image_tag['src'] if image_tag else 'No image found'

        result = {
            'title': name.lower(),
            'price': price,
            'flight_ratings': flight_ratings,
            #'vendor': manufacturer,
            'link_to_disc': "https://discking.eu" + link_to_disc,
            'image_url': image_url,
            'store': "discking.eu"
        }

        all_products.append(result)

    print(all_products)

    ############################################################################################

    connection = create_conn()

    try:
        with connection.cursor() as cursor:

            sql = """
            INSERT INTO product_table (title, price, speed, glide, turn, fade, link_to_disc, image_url, store)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE
            price = VALUES(price),
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
        
get_page_data_for_testing()