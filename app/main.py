
import json
from flask import Flask, render_template, jsonify, request, session, redirect, url_for
from flask_oauthlib.client import OAuth
from app.handle_credentials import get_secret
from app.handle_db_connections import create_conn, read_query


app = Flask(__name__, static_folder="static", template_folder="templates")

app.secret_key = 'random_secret_key'
app.config['GOOGLE_ID'] = get_secret("google_id")
app.config['GOOGLE_SECRET'] = get_secret("google_secret")

oauth = OAuth(app)
google = oauth.remote_app(
    'google',
    consumer_key=app.config['GOOGLE_ID'],
    consumer_secret=app.config['GOOGLE_SECRET'],
    request_token_params={'scope': 'email'},
    base_url='https://www.googleapis.com/oauth2/v1/',
    request_token_url=None,
    access_token_method='POST',
    access_token_url='https://accounts.google.com/o/oauth2/token',
    authorize_url='https://accounts.google.com/o/oauth2/auth',
)

@app.route('/login')
def login():
    return google.authorize(callback=url_for('authorized', _external=True))

@app.route('/logout')
def logout():
    session.pop('google_token', None)
    return redirect(url_for('product_grid'))

@app.route('/auth/callback')
def authorized():
    try:
        response = google.authorized_response()
    except:
        return redirect(url_for('home'))

    if response is None or response.get('access_token') is None:
        return 'Login failed!'

    session['google_token'] = (response['access_token'], '')
    me = google.get('userinfo').__dict__
    me = json.loads(me.get("raw_data"))

    query = """
    INSERT INTO users (id, e_mail, picture_url, product_history)
    SELECT %s, %s, %s, %s
    WHERE NOT EXISTS (SELECT 1 FROM users WHERE id = %s);
    """
    insert_statements = [(me.get("id"), me.get("email"), me.get("picture"), 
                          json.dumps({'product_history': []}), me.get("id"))]
    
    connection = create_conn()

    execute_insert(connection, query, insert_statements)

    session['user_email'] = me.get("email")
    session['id'] = me.get("id")

    return redirect(url_for('product_grid'))

@google.tokengetter
def get_google_oauth_token():
    return session.get('google_token')

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/products")
def product_grid():

    sql_query = """
    SELECT * FROM main_schema.product_table 
    WHERE speed IS NOT NULL AND glide IS NOT NULL AND turn IS NOT NULL AND fade IS NOT NULL;
    """

    connection = create_conn()
    products = execute_select(connection, sql_query)
    products = [process_product(product) for product in products if "karte" not in product.get("title", "").lower()]

    filtered_products = filter_products(products, request.args)
    sorted_products = sort_products(filtered_products, request.args.get('sort', ''))

    page, per_page = int(request.args.get('page', 1)), 25
    paginated_products = paginate_products(sorted_products, page, per_page)

    unique_stores = set(product['store'] for product in products)

    return render_template(
        'product_grid.html',
        products=paginated_products,
        search_query=request.args.get('search', ''),
        selected_price_range=request.args.get('price_range', ''),
        selected_speed=request.args.get('speed', ''),
        selected_glide=request.args.get('glide', ''),
        selected_turn=request.args.get('turn', ''),
        selected_fade=request.args.get('fade', ''),
        selected_stores=request.args.getlist('store'),
        unique_stores=unique_stores,
        sort_option=request.args.get('sort', ''),
        page=page,
        total_pages=(len(sorted_products) + per_page - 1) // per_page,
        pages_to_display=range(page, min(page + 3, ((len(sorted_products) + per_page - 1) // per_page) + 1)),
        session=session
    )

@app.route('/profile', methods=['POST', 'GET'])
def profile():
    session_id = session.get('id')

    sql_query = "SELECT product_history FROM users WHERE id = %s"
    connection = create_conn()
    user_json = execute_select(connection, sql_query, (session_id,))
    product_history = json.loads(user_json[0].get("product_history")).get("product_history")

    products = get_products_by_ids(connection, product_history)
    products = [process_product(product) for product in products if "karte" not in product.get("title", "").lower()]

    page, per_page = int(request.args.get('page', 1)), 25
    paginated_products = paginate_products(products, page, per_page)

    me = google.get('userinfo').__dict__
    me = json.loads(me.get("raw_data"))
    user = {'email': me.get("email"), 'picture': me.get("picture")}

    return render_template(
        'profile.html', 
        products=paginated_products,
        page=page,
        total_pages=(len(products) + per_page - 1) // per_page,
        pages_to_display=range(page, min(page + 3, ((len(products) + per_page - 1) // per_page) + 1)),
        user=user
    )

@app.route('/add-to-wishlist', methods=['POST'])
def add_to_wishlist():
    product_data = request.get_json()
    session_id = session.get('id')

    sql_query = "SELECT product_history FROM users WHERE id = %s"
    connection = create_conn()
    user_json = execute_select(connection, sql_query, (session_id,))
    product_history = json.loads(user_json[0].get("product_history"))
    
    if product_data.get("unique_id") not in product_history["product_history"]:
        product_history["product_history"].append(product_data.get("unique_id"))

    query = "UPDATE users SET product_history = %s WHERE id = %s"
    connection = create_conn()
    execute_insert(connection, query, [(json.dumps(product_history), session_id)])

    return "Product added to wishlist!"

@app.route('/remove-from-wishlist', methods=['POST'])
def remove_from_wishlist():
    product_data = request.get_json()
    session_id = session.get('id')

    sql_query = "SELECT product_history FROM users WHERE id = %s"
    connection = create_conn()
    user_json = execute_select(connection, sql_query, (session_id,))
    product_history = json.loads(user_json[0].get("product_history"))
    
    unique_id_to_remove = product_data.get("unique_id")
    if unique_id_to_remove in product_history["product_history"]:
        product_history["product_history"].remove(unique_id_to_remove)

    query = "UPDATE users SET product_history = %s WHERE id = %s"
    connection = create_conn()
    execute_insert(connection, query, [(json.dumps(product_history), session_id)])

    return redirect(url_for('profile'))

# Helper functions
def process_product(product):
    if product.get('speed') is not None:
        product['speed'] = float(product['speed'])
        product['glide'] = float(product['glide'])
        product['turn'] = float(product['turn'])
        product['fade'] = float(product['fade'])
    return product

def filter_products(products, args):
    filtered = products

    query = args.get('search', '').lower()
    if query:
        filtered = [p for p in filtered if query in p['title'].lower()]

    try:
        min_price = float(args.get('price_min', 0))
    except ValueError:
        min_price = 0

    try:
        max_price = float(args.get('price_max', float('inf')))
    except ValueError:
        max_price = float('inf')

    filtered = [p for p in filtered if min_price <= float(p['price']) <= max_price]

    for attr in ['speed', 'glide', 'turn', 'fade']:
        try:
            min_val = float(args.get(f'{attr}_min', -float('inf')))
        except ValueError:
            min_val = -float('inf')

        try:
            max_val = float(args.get(f'{attr}_max', float('inf')))
        except ValueError:
            max_val = float('inf')

        filtered = [p for p in filtered if min_val <= float(p.get(attr, 0)) <= max_val]

    selected_stores = args.getlist('store')
    if selected_stores:
        filtered = [p for p in filtered if p['store'] in selected_stores]

    return filtered

def sort_products(products, sort_option):
    if sort_option == 'price_lowest':
        return sorted(products, key=lambda x: float(x['price']))
    elif sort_option == 'price_highest':
        return sorted(products, key=lambda x: float(x['price']), reverse=True)
    elif sort_option == 'title':
        return sorted(products, key=lambda x: x['title'].lower())
    elif sort_option == 'store':
        return sorted(products, key=lambda x: x['store'].lower())
    elif sort_option in ['glide_lowest', 'glide_highest', 'speed_lowest', 'speed_highest', 
                         'turn_lowest', 'turn_highest', 'fade_lowest', 'fade_highest']:
        attribute, direction = sort_option.split('_')
        return sorted(products, 
                      key=lambda x: float(x.get(attribute, 0)), 
                      reverse=(direction == 'highest'))
    
    return products

def paginate_products(products, page, per_page):
    start = (page - 1) * per_page
    end = start + per_page
    return products[start:end]

def get_products_by_ids(connection, product_ids):

    if not product_ids:
        return []

    placeholders = ', '.join(['%s'] * len(product_ids))
    sql_query = f"""
        SELECT *
        FROM product_table
        WHERE unique_id IN ({placeholders})
    """
    
    connection = create_conn()
    results = execute_select(connection, sql_query, product_ids)
    return results

if __name__ == "__main__":
    app.run(debug=False)