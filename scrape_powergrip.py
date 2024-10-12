import requests
from xml.etree import ElementTree as ET
from bs4 import BeautifulSoup

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

def get_page_data():

    page_url = "https://powergrip.fi/tuote/sswizaer/gateway-eraser-wizard"

    response = requests.get(page_url)

    if response.status_code == 200:

        soup = BeautifulSoup(response.content, 'html.parser')

        product_header = soup.select_one('#product-page div.product-data header div div div span')
        if product_header:
            product_header_text = product_header.get_text(strip=True)
            print(f"Product Header: {product_header_text}")
        else:
            print("Product header not found.")

        stock_info = soup.select_one('#stock-in-store-tabs')
        if stock_info:
            stock_info_text = stock_info.get_text(strip=True)
            print(f"Stock Information: {stock_info_text}")
        else:
            print("Stock information not found.")
    else:
        print(f"Failed to retrieve the page: {response.status_code}")

get_page_data()