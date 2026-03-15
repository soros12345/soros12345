# Amazon vs eBay Price Comparison Application

A Flask-based web application that allows users to search and compare product prices between Amazon and eBay in real-time.

## Features

✅ **Search Products** - Search for products by keyword across both platforms
✅ **Price Comparison** - Side-by-side price comparison view
✅ **Real-time Data** - Live web scraping from Amazon and eBay
✅ **Responsive Design** - Works on desktop and mobile devices
✅ **User-Friendly Interface** - Clean and intuitive UI

## Project Structure

```
.
├── app.py                 # Flask application and API routes
├── price_scraper.py       # Web scraping logic for Amazon and eBay
├── requirements.txt       # Python dependencies
├── templates/
│   └── index.html        # Main web interface
└── static/
    └── style.css         # CSS styling
```

## Installation

### Prerequisites

- Python 3.7 or higher
- pip (Python package manager)

### Setup

1. Clone the repository:
```bash
git clone https://github.com/soros12345/soros12345.git
cd soros12345
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run the application:
```bash
python app.py
```

4. Open your browser and navigate to:
```
http://localhost:5000
```

## Usage

1. Enter a product name in the search box (e.g., "laptop", "headphones", "smartphone")
2. Click the "Search" button or press Enter
3. View side-by-side results from both Amazon and eBay
4. Click "View Product" to visit the product page

## API Endpoints

### POST /api/compare
Compare prices for a product across both platforms.

**Request:**
```json
{
  "query": "laptop"
}
```

**Response:**
```json
{
  "query": "laptop",
  "amazon": [
    {
      "platform": "Amazon",
      "title": "Product Name",
      "price": "$999.99",
      "url": "https://www.amazon.com/..."
    }
  ],
  "ebay": [
    {
      "platform": "eBay",
      "title": "Product Name",
      "price": "$899.99",
      "url": "https://www.ebay.com/..."
    }
  ]
}
```

### POST /api/search/amazon
Search only Amazon for products.

### POST /api/search/ebay
Search only eBay for products.

## Technologies Used

- **Backend:** Flask, Python 3
- **Web Scraping:** BeautifulSoup4, Requests
- **Frontend:** HTML5, CSS3, JavaScript
- **API:** RESTful API

## How It Works

1. User enters a search query
2. Backend makes HTTP requests to Amazon and eBay
3. BeautifulSoup parses the HTML responses
4. Product data is extracted (title, price, URL)
5. Results are formatted as JSON and sent to frontend
6. Frontend displays results in a comparison layout

## Limitations

- Web scraping may be rate-limited by platforms
- Product availability and prices change frequently
- Some products may not appear due to platform restrictions
- Requires internet connection

## Future Enhancements

- [ ] Add product images
- [ ] Store price history
- [ ] Email notifications for price drops
- [ ] Add more e-commerce platforms (Walmart, Target, etc.)
- [ ] Implement caching for faster results
- [ ] Add user accounts and favorites
- [ ] Create mobile app

## Legal Notice

This application is for educational purposes. Always respect the terms of service of the websites you're scraping. Some websites may prohibit automated scraping in their terms of service.

## License

This project is open source and available under the MIT License.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Support

For issues or questions, please open an issue on the GitHub repository.