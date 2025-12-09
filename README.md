# JuhasFlies - Inventory Management System

A modern, easy-to-use web application for managing retail store inventory.

## Features

- 📦 Browse and view all products in a clean, modern interface
- ➕ Add new products with details (name, category, price, quantity, description)
- ✏️ Edit existing products
- 🗑️ Delete products
- 🔢 Update product quantities with quick increment/decrement buttons
- 🔍 Search products by name, category, or description
- 🏷️ Filter products by category
- 📊 View real-time statistics (total products, items, categories, inventory value)
- 📱 Responsive design that works on desktop and mobile devices

## Pre-populated Database

The application comes with a test database containing 20 sample products across different categories:
- Electronics (laptops, monitors, headphones, etc.)
- Furniture (chairs, desks, bookshelves, etc.)
- Stationery (notebooks, pens, paper clips, etc.)
- Appliances
- Accessories

## Installation & Setup

### Prerequisites
- Python 3.7 or higher
- pip (Python package installer)

### Steps

1. Clone the repository:
```bash
git clone https://github.com/teljoj/JuhasFlies.git
cd JuhasFlies
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your web browser and navigate to:
```
http://localhost:5000
```

The database will be automatically created and populated with 20 sample products on first run.

## Usage

### Browsing Products
- All products are displayed in a card-based grid layout
- Each card shows product details including name, category, price, quantity, and description
- Use the search bar to find specific products
- Use the category filter to view products from a specific category

### Adding Products
1. Click the "➕ Add Product" button
2. Fill in the product details (all fields except description are required)
3. Click "Save Product"

### Editing Products
1. Click the "✏️ Edit" button on any product card
2. Modify the product details
3. Click "Save Product"

### Updating Quantity
- Use the **−** and **+** buttons for quick adjustments
- Or directly type a new quantity in the input field

### Deleting Products
1. Click the "🗑️ Delete" button on any product card
2. Confirm the deletion

## Technology Stack

- **Backend**: Python Flask
- **Database**: SQLite
- **Frontend**: HTML5, CSS3, Vanilla JavaScript
- **Design**: Modern, gradient-based UI with responsive layout

## API Endpoints

The application provides a RESTful API:

- `GET /api/products` - Get all products
- `GET /api/products/<id>` - Get a specific product
- `POST /api/products` - Create a new product
- `PUT /api/products/<id>` - Update a product
- `DELETE /api/products/<id>` - Delete a product

## Development

The application runs in debug mode by default. To run in production mode, modify the `app.run()` call in `app.py`:

```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

## License

This project is created for educational purposes.
