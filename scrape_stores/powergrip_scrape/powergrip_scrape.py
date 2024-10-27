import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup
from requests_html import HTMLSession

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

    page_url = "https://powergrip.fi/tuote/opsinu24/latitude-64-opto-sinus"

    session = HTMLSession()

    response = session.get(page_url)

    response.html.render(sleep=1)

    html_content = response.html.html

    with open('powergrip_scrape\powergrip_dynamic_page.html', 'w', encoding='utf-8') as file:
        file.write(html_content)

def get_page_data():

    with open('powergrip_scrape\powergrip_dynamic_page.html', 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    ############################################################################################

    product_div = soup.find('div', class_='product-title')
    product_name = product_div.get_text(strip=True)  
    product_brand = soup.find('div', class_='product-manufacturer').get_text(strip=True)

    name = product_brand + " " + product_name

    product_header = soup.select_one('#product-page div.product-data header div div div span')
    
    price = product_header.get_text(strip=True)

    '''
    
    ul_element = soup.find('ul', {'id': 'stock-in-store-tabs'})

    if ul_element:

        check_icons = ul_element.find_all('i', {'class': 'fa fa-check fa-fw text-pg-lime'})

        # Determine if any such elements exist
        available = len(check_icons) > 0

        # Now `available` will be True if any such <i> elements are found
        print(available)

    '''

    ############################################################################################
    
    ratings_div = soup.find('div', class_='product-flight-ratings')

    flight_ratings = {}

    translation_map = {
        'Nopeus': 'Speed',
        'Liito': 'Glide',
        'Vakaus': 'Turn',
        'Feidi': 'Fade'
    }

    for li in ratings_div.find_all('li'):
        label = li.find('span', class_='label').get_text(strip=True)
        value = li.find('span', class_='value').get_text(strip=True)
        translated_label = translation_map.get(label, label) 
        flight_ratings[translated_label] = value

    ############################################################################################

    image_tag = soup.find('img', id='product-image-17318')

    image_url = image_tag['src']

    ############################################################################################

    result = {
        'title': name,
        'price': price,
        'flight_ratings': flight_ratings,
        'image_url': image_url
    }

    print(result)

get_page_data()