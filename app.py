from flask import Flask, render_template, request, jsonify
import sqlite3
import os

app = Flask(__name__)
DATABASE = 'inventory.db'

def get_db_connection():
    """Create a database connection"""
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize the database with schema and sample data"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Create products table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            category TEXT NOT NULL,
            quantity INTEGER NOT NULL,
            price REAL NOT NULL,
            description TEXT
        )
    ''')
    
    # Check if database is empty
    cursor.execute('SELECT COUNT(*) FROM products')
    if cursor.fetchone()[0] == 0:
        # Insert 20 sample products
        sample_products = [
            ('Laptop Pro 15"', 'Electronics', 15, 1299.99, 'High-performance laptop with 16GB RAM'),
            ('Wireless Mouse', 'Electronics', 45, 29.99, 'Ergonomic wireless mouse with USB receiver'),
            ('Mechanical Keyboard', 'Electronics', 30, 89.99, 'RGB backlit mechanical keyboard'),
            ('USB-C Hub', 'Electronics', 60, 49.99, '7-in-1 USB-C multiport adapter'),
            ('Monitor 27"', 'Electronics', 20, 349.99, '4K UHD monitor with HDR support'),
            ('Office Chair', 'Furniture', 12, 299.99, 'Ergonomic office chair with lumbar support'),
            ('Standing Desk', 'Furniture', 8, 599.99, 'Electric height-adjustable standing desk'),
            ('Desk Lamp', 'Furniture', 25, 39.99, 'LED desk lamp with adjustable brightness'),
            ('Bookshelf', 'Furniture', 10, 149.99, '5-tier wooden bookshelf'),
            ('File Cabinet', 'Furniture', 15, 199.99, '3-drawer locking file cabinet'),
            ('Notebook A5', 'Stationery', 100, 4.99, 'Hardcover ruled notebook, 200 pages'),
            ('Pen Set', 'Stationery', 80, 12.99, 'Premium ballpoint pen set, 10 pieces'),
            ('Sticky Notes', 'Stationery', 150, 3.99, 'Colorful sticky notes pack, 6 colors'),
            ('Stapler', 'Stationery', 40, 8.99, 'Heavy-duty stapler with 1000 staples'),
            ('Paper Clips', 'Stationery', 200, 2.99, 'Assorted paper clips, 500 count'),
            ('Coffee Maker', 'Appliances', 18, 79.99, '12-cup programmable coffee maker'),
            ('Water Bottle', 'Accessories', 90, 19.99, 'Insulated stainless steel water bottle'),
            ('Backpack', 'Accessories', 35, 59.99, 'Laptop backpack with USB charging port'),
            ('Headphones', 'Electronics', 25, 149.99, 'Noise-cancelling wireless headphones'),
            ('Webcam HD', 'Electronics', 22, 69.99, '1080p HD webcam with built-in microphone')
        ]
        
        cursor.executemany('''
            INSERT INTO products (name, category, quantity, price, description)
            VALUES (?, ?, ?, ?, ?)
        ''', sample_products)
        
        conn.commit()
    
    conn.close()

@app.route('/')
def index():
    """Render the main page"""
    return render_template('index.html')

@app.route('/api/products', methods=['GET'])
def get_products():
    """Get all products"""
    conn = get_db_connection()
    products = conn.execute('SELECT * FROM products ORDER BY category, name').fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in products])

@app.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product"""
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    conn.close()
    
    if product is None:
        return jsonify({'error': 'Product not found'}), 404
    
    return jsonify(dict(product))

@app.route('/api/products', methods=['POST'])
def add_product():
    """Add a new product"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid or missing JSON data'}), 400
    
    if not all(k in data for k in ('name', 'category', 'quantity', 'price')):
        return jsonify({'error': 'Missing required fields'}), 400
    
    # Validate data types and ranges
    try:
        quantity = int(data['quantity'])
        price = float(data['price'])
        if quantity < 0:
            return jsonify({'error': 'Quantity must be non-negative'}), 400
        if price < 0:
            return jsonify({'error': 'Price must be non-negative'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid quantity or price format'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO products (name, category, quantity, price, description)
        VALUES (?, ?, ?, ?, ?)
    ''', (data['name'], data['category'], quantity, price, data.get('description', '')))
    conn.commit()
    product_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': product_id, 'message': 'Product added successfully'}), 201

@app.route('/api/products/<int:product_id>', methods=['PUT'])
def update_product(product_id):
    """Update a product"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid or missing JSON data'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Check if product exists
    product = cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    
    # Validate quantity and price if provided
    quantity = data.get('quantity', product['quantity'])
    price = data.get('price', product['price'])
    
    try:
        quantity = int(quantity)
        price = float(price)
        if quantity < 0:
            conn.close()
            return jsonify({'error': 'Quantity must be non-negative'}), 400
        if price < 0:
            conn.close()
            return jsonify({'error': 'Price must be non-negative'}), 400
    except (ValueError, TypeError):
        conn.close()
        return jsonify({'error': 'Invalid quantity or price format'}), 400
    
    # Update product
    cursor.execute('''
        UPDATE products
        SET name = ?, category = ?, quantity = ?, price = ?, description = ?
        WHERE id = ?
    ''', (
        data.get('name', product['name']),
        data.get('category', product['category']),
        quantity,
        price,
        data.get('description', product['description']),
        product_id
    ))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product updated successfully'})

@app.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    """Delete a product"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product deleted successfully'})

if __name__ == '__main__':
    # Initialize database on first run
    if not os.path.exists(DATABASE):
        init_db()
    
    # Set debug mode from environment variable, default to False for security
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
