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
    SELECT * FROM  disc_golf_db.product_table WHERE speed IS NOT NULL AND glide IS NOT NULL AND turn IS NOT NULL AND fade IS NOT NULL;
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

    unique_stores = set(product['store'] for product in products)

    filtered_products = products
    if query:
        filtered_products = [product for product in products if query.lower() in product['title'].lower()]
        
    min_price = request.args.get('price_min', '')
    max_price = request.args.get('price_max', '')
    if min_price or max_price:
        
        if min_price == '':
            min_price = '0'
        if max_price == '':
            max_price = '1000'

        try:
            min_price = float(min_price)
            max_price = float(max_price)
            filtered_products = [
                product for product in filtered_products
                if min_price <= float(product['price']) <= max_price
            ]
        except ValueError:
            print("Invalid price range input")

    min_speed = request.args.get('speed_min')
    max_speed = request.args.get('speed_max')
    if min_speed or max_speed:

        if min_speed == '':
            min_speed = '0'
        if max_speed == '':
            max_speed = '10'

        try:
            min_speed = float(min_speed)
            max_speed = float(max_speed)
            filtered_products = [
                product for product in filtered_products
                if min_speed <= float(product['speed']) <= max_speed
            ]
        except ValueError:
            print("Invalid speed range input")

    min_glide = request.args.get('glide_min')
    max_glide = request.args.get('glide_max')
    if min_glide or max_glide:

        if min_glide == '':
            min_glide = '0'
        if max_glide == '':
            max_glide = '10'

        try:
            min_glide = float(min_glide)
            max_glide = float(max_glide)
            filtered_products = [
                product for product in filtered_products
                if min_glide <= float(product['glide']) <= max_glide
            ]
        except ValueError:
            print("Invalid glide range input")

    min_turn = request.args.get('turn_min')
    max_turn = request.args.get('turn_max')
    if min_turn or max_turn:

        if min_turn == '':
            min_turn = '-10'
        if max_turn == '':
            max_turn = '10'

        try:
            min_turn = float(min_turn)
            max_turn = float(max_turn)
            filtered_products = [
                product for product in filtered_products
                if min_turn <= float(product['turn']) <= max_turn
            ]
        except ValueError:
            print("Invalid turn range input")

    min_fade = request.args.get('fade_min')
    max_fade = request.args.get('fade_max')
    if min_fade or max_fade:

        if min_fade == '':
            min_fade = '0'
        if max_fade == '':
            max_fade = '10'
        
        try:
            min_fade = float(min_fade)
            max_fade = float(max_fade)
            filtered_products = [
                product for product in filtered_products
                if min_fade <= float(product['fade']) <= max_fade
            ]
        except ValueError:
            print("Invalid fade range input")

    if selected_stores:
        filtered_products = [
            product for product in filtered_products
            if product['store'] in selected_stores
        ]

    if sort_option == 'price_lowest':
        filtered_products.sort(key=lambda x: float(x['price']))
    elif sort_option == 'price_highest':
        filtered_products.sort(key=lambda x: float(x['price']), reverse=True)
    elif sort_option == 'title':
        filtered_products.sort(key=lambda x: x['title'].lower())
    elif sort_option == 'store':
        filtered_products.sort(key=lambda x: x['store'].lower())
    elif sort_option == 'glide_lowest':
        filtered_products.sort(key=lambda x: float(x.get('glide', 0.0)))
    elif sort_option == 'glide_highest':
        filtered_products.sort(key=lambda x: float(x.get('glide', 0.0)), reverse=True)
    elif sort_option == 'speed_lowest':
        filtered_products.sort(key=lambda x: float(x.get('speed', 0.0)))
    elif sort_option == 'speed_highest':
        filtered_products.sort(key=lambda x: float(x.get('speed', 0.0)), reverse=True)
    elif sort_option == 'turn_lowest':
        filtered_products.sort(key=lambda x: float(x.get('turn', 0.0)))
    elif sort_option == 'turn_highest':
        filtered_products.sort(key=lambda x: float(x.get('turn', 0.0)), reverse=True)
    elif sort_option == 'fade_lowest':
        filtered_products.sort(key=lambda x: float(x.get('fade', 0.0)))
    elif sort_option == 'fade_highest':
        filtered_products.sort(key=lambda x: float(x.get('fade', 0.0)), reverse=True)

    # pagination parameters
    page = request.args.get('page', 1, type=int)
    per_page = 25

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