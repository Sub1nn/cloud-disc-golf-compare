from flask import Flask, render_template, request

from handle_credentials import get_secret
from handle_db_connections import create_conn, read_query

app = Flask(__name__)

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/products")
def product_grid():

    connection = create_conn()

    sql_query = """
    SELECT * FROM product_table WHERE speed IS NOT NULL;
    """
    products = []
    read_products = read_query(connection, sql_query)
    for i in read_products:

        if "karte" in i.get("title"):
            continue

        if i.get('speed') == None:
            products.append(i)
            continue
        i['speed'] = float(i.get('speed'))
        i['glide'] = float(i.get('glide'))
        i['turn'] = float(i.get('turn'))
        i['fade'] = float(i.get('fade'))
        products.append(i)

    query = request.args.get('search', '') 
    price_range = request.args.get('price_range', '') 
    speed = request.args.get('speed', '')
    glide = request.args.get('glide', '') 
    turn = request.args.get('turn', '') 
    fade = request.args.get('fade', '')  
    selected_stores = request.args.getlist('store')
    sort_option = request.args.get('sort', '')

    # pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 25

    unique_stores = set(product['store'] for product in products)

    filtered_products = products
    if query:
        filtered_products = [product for product in products if query.lower() in product['title'].lower()]
    
    if price_range:
        min_price, max_price = price_range.split('-')
        filtered_products = [
            product for product in filtered_products
            if float(product['price']) >= float(min_price)
            and float(product['price']) <= float(max_price)
        ]

    if speed:
        filtered_products = [
            product for product in filtered_products
            if product['speed'] == int(speed)
        ]

    if glide:
        filtered_products = [
            product for product in filtered_products
            if product['glide'] == int(glide)
        ]

    if turn:
        filtered_products = [
            product for product in filtered_products
            if product['turn'] == int(turn)
        ]

    if fade:
        filtered_products = [
            product for product in filtered_products
            if product['fade'] == int(fade)
        ]

    if selected_stores:
        filtered_products = [
            product for product in filtered_products
            if product['store'] in selected_stores
        ]

    if sort_option == 'price':
        filtered_products.sort(key=lambda x: float(x['price']))
    elif sort_option == 'title':
        filtered_products.sort(key=lambda x: x['title'].lower())

    # pagination
    total_items = len(filtered_products)
    total_pages = (total_items + per_page - 1) // per_page

    start = (page - 1) * per_page
    end = start + per_page
    paginated_products = filtered_products[start:end]

    # determine the pages to display in pagination
    pages_to_display = [p for p in range(page, min(page + 3, total_pages + 1))]

    return render_template(
        'product_grid.html', 
        products=paginated_products,
        search_query=query,
        selected_price_range=price_range,
        selected_speed=str(speed),
        selected_glide=str(glide),
        selected_turn=str(turn),
        selected_fade=str(fade),
        selected_stores=selected_stores,
        unique_stores=unique_stores,
        sort_option=sort_option,
        page=page,
        total_pages=total_pages,
        pages_to_display=pages_to_display
    )

if __name__ == "__main__":
    app.run(debug=False)