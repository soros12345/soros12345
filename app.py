from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/')
def home():
    return "index.html"

@app.route('/api/compare', methods=['POST'])
def compare():
    data = request.json
    query = data.get('query')
    # Assuming price_scraper is a module you have that handles scraping
    results = price_scraper.compare_prices(query)
    return jsonify(results)

if __name__ == '__main__':
    app.run(debug=True)