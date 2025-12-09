from flask import Flask, render_template, request, jsonify, send_from_directory
import sqlite3
import os
from werkzeug.utils import secure_filename
import uuid

app = Flask(__name__)
DATABASE = 'inventory.db'
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# Create upload directory if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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
            description TEXT,
            image_filename TEXT
        )
    ''')
    
    # Add image_filename column if it doesn't exist (for existing databases)
    try:
        cursor.execute('ALTER TABLE products ADD COLUMN image_filename TEXT')
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass
    
    # Create reviews table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_id INTEGER NOT NULL,
            rating INTEGER NOT NULL CHECK(rating >= 1 AND rating <= 5),
            comment TEXT,
            reviewer_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
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
        INSERT INTO products (name, category, quantity, price, description, image_filename)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (data['name'], data['category'], quantity, price, data.get('description', ''), data.get('image_filename')))
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
        SET name = ?, category = ?, quantity = ?, price = ?, description = ?, image_filename = ?
        WHERE id = ?
    ''', (
        data.get('name', product['name']),
        data.get('category', product['category']),
        quantity,
        price,
        data.get('description', product['description']),
        data.get('image_filename', product['image_filename']),
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
    
    # Get product to delete its image
    product = cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    
    if product is None:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    
    # Delete image file if exists
    if product['image_filename']:
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], product['image_filename'])
        if os.path.exists(image_path):
            try:
                os.remove(image_path)
            except Exception as e:
                print(f"Error deleting image: {e}")
    
    cursor.execute('DELETE FROM products WHERE id = ?', (product_id,))
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Product deleted successfully'})

@app.route('/api/upload-image', methods=['POST'])
def upload_image():
    """Upload a product image"""
    if 'image' not in request.files:
        return jsonify({'error': 'No image file provided'}), 400
    
    file = request.files['image']
    
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    if not allowed_file(file.filename):
        return jsonify({'error': 'Invalid file type. Allowed types: png, jpg, jpeg, gif, webp'}), 400
    
    # Generate unique filename
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4()}.{ext}"
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    
    try:
        file.save(filepath)
        return jsonify({
            'message': 'Image uploaded successfully',
            'filename': filename,
            'url': f'/uploads/{filename}'
        }), 201
    except Exception as e:
        return jsonify({'error': f'Failed to save image: {str(e)}'}), 500

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """Serve uploaded images"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/products/<int:product_id>/reviews', methods=['GET'])
def get_product_reviews(product_id):
    """Get all reviews for a specific product"""
    conn = get_db_connection()
    reviews = conn.execute(
        'SELECT * FROM reviews WHERE product_id = ? ORDER BY created_at DESC',
        (product_id,)
    ).fetchall()
    conn.close()
    
    return jsonify([dict(row) for row in reviews])

@app.route('/api/products/<int:product_id>/reviews', methods=['POST'])
def add_review(product_id):
    """Add a review for a product"""
    data = request.get_json()
    
    if not data:
        return jsonify({'error': 'Invalid or missing JSON data'}), 400
    
    if 'rating' not in data:
        return jsonify({'error': 'Rating is required'}), 400
    
    try:
        rating = int(data['rating'])
        if rating < 1 or rating > 5:
            return jsonify({'error': 'Rating must be between 1 and 5'}), 400
    except (ValueError, TypeError):
        return jsonify({'error': 'Invalid rating format'}), 400
    
    # Check if product exists
    conn = get_db_connection()
    product = conn.execute('SELECT * FROM products WHERE id = ?', (product_id,)).fetchone()
    if product is None:
        conn.close()
        return jsonify({'error': 'Product not found'}), 404
    
    # Set reviewer name to "Anonymous" if not provided or empty
    reviewer_name = data.get('reviewer_name', '').strip()
    if not reviewer_name:
        reviewer_name = 'Anonymous'
    
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reviews (product_id, rating, comment, reviewer_name)
        VALUES (?, ?, ?, ?)
    ''', (product_id, rating, data.get('comment', ''), reviewer_name))
    conn.commit()
    review_id = cursor.lastrowid
    conn.close()
    
    return jsonify({'id': review_id, 'message': 'Review added successfully'}), 201

@app.route('/api/products/<int:product_id>/reviews/stats', methods=['GET'])
def get_review_stats(product_id):
    """Get review statistics for a product"""
    conn = get_db_connection()
    
    stats = conn.execute('''
        SELECT 
            COUNT(*) as total_reviews,
            AVG(rating) as average_rating,
            SUM(CASE WHEN rating = 5 THEN 1 ELSE 0 END) as five_star,
            SUM(CASE WHEN rating = 4 THEN 1 ELSE 0 END) as four_star,
            SUM(CASE WHEN rating = 3 THEN 1 ELSE 0 END) as three_star,
            SUM(CASE WHEN rating = 2 THEN 1 ELSE 0 END) as two_star,
            SUM(CASE WHEN rating = 1 THEN 1 ELSE 0 END) as one_star
        FROM reviews
        WHERE product_id = ?
    ''', (product_id,)).fetchone()
    
    conn.close()
    
    return jsonify(dict(stats))

@app.route('/api/reviews/<int:review_id>', methods=['DELETE'])
def delete_review(review_id):
    """Delete a review"""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reviews WHERE id = ?', (review_id,))
    
    if cursor.rowcount == 0:
        conn.close()
        return jsonify({'error': 'Review not found'}), 404
    
    conn.commit()
    conn.close()
    
    return jsonify({'message': 'Review deleted successfully'})

if __name__ == '__main__':
    # Initialize database on first run
    if not os.path.exists(DATABASE):
        init_db()
    else:
        # Run migration for existing databases
        init_db()
    
    # Set debug mode from environment variable, default to False for security
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    app.run(debug=debug_mode, host='0.0.0.0', port=5000)
