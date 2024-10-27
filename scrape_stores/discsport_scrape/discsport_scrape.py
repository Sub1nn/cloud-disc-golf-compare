import json
import requests
import sys
import os

from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from requests_html import HTMLSession

current = os.path.dirname(os.path.realpath(__file__))
parent = os.path.dirname(current)
sys.path.append(parent)

from handle_db_connections import create_conn

def get_all():

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

def save_a_page():

    page_url = "https://www.discsporteurope.com/en/midrange/results,1-200"

    response = requests.get(page_url)
        
    with open('discsport_scrape\discsport_normal_page.html', 'w', encoding='utf-8') as file:
        file.write(response.text)

def get_page_data():

    with open('discsport_scrape\discsport_normal_page.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    ############################################################################################

    all_products = []

    product_articles = soup.find_all('div', class_='spacer')

    for article in product_articles:

        name = article.find('h3', class_='catProductTitle').get_text(strip=True)

        price = article.find('span', class_='PricesalesPrice').get_text(strip=True)

        flight_ratings = {}
        speed_tag = article.find('a', class_='flight-speed')
        flight_ratings['Speed'] = speed_tag.find('span').get_text(strip=True) if speed_tag and speed_tag.find('span') else None

        glide_tag = article.find('a', class_='flight-glide')
        flight_ratings['Glide'] = glide_tag.find('span').get_text(strip=True) if glide_tag and glide_tag.find('span') else None

        turn_tag = article.find('a', class_='flight-turn')
        flight_ratings['Turn'] = turn_tag.find('span').get_text(strip=True) if turn_tag and turn_tag.find('span') else None

        fade_tag = article.find('a', class_='flight-fade')
        flight_ratings['Fade'] = fade_tag.find('span').get_text(strip=True) if fade_tag and fade_tag.find('span') else None

        link_to_disc_tag = article.find('a')
        link_to_disc = link_to_disc_tag['href'] if link_to_disc_tag else 'No link found'

        image_tag = article.find('img', class_='browseProductImage')
        image_url = image_tag['src'] if image_tag else 'No image found'

        result = {
            'title': name.lower(),
            'price': price,
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

get_page_data()