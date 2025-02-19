from flask import Flask, render_template
import requests
import os
from dotenv import load_dotenv
import ssl
from urllib3.poolmanager import PoolManager
from requests.adapters import HTTPAdapter

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Marvel API credentials
PUBLIC_KEY = os.getenv('MARVEL_PUBLIC_KEY')
PRIVATE_KEY = os.getenv('MARVEL_PRIVATE_KEY')
BASE_URL = 'https://gateway.marvel.com/v1/public/characters'

# Create a custom SSL context
def create_custom_ssl_context():
    ssl_context = ssl.create_default_context()
    # Lower security level if needed (for testing only)
    ssl_context.set_ciphers('DEFAULT@SECLEVEL=1')
    return ssl_context

# Create a custom HTTP adapter
class CustomHTTPAdapter(HTTPAdapter):
    def init_poolmanager(self, *args, **kwargs):
        kwargs['ssl_context'] = create_custom_ssl_context()
        return super().init_poolmanager(*args, **kwargs)

# Function to fetch characters from Marvel API
def fetch_characters(total_pages=18):
    import hashlib
    import time

    all_characters = []
    limit = 100  # Maximum number of characters per request

    for page in range(total_pages):
        offset = page * limit
        ts = str(time.time())
        hash_str = hashlib.md5(f"{ts}{PRIVATE_KEY}{PUBLIC_KEY}".encode()).hexdigest()

        params = {
            'apikey': PUBLIC_KEY,
            'ts': ts,
            'hash': hash_str,
            'limit': limit,
            'offset': offset
        }

        try:
            session = requests.Session()
            session.mount('https://', CustomHTTPAdapter())
            response = session.get(BASE_URL, params=params)

            if response.status_code == 200:
                characters = response.json()['data']['results']
                all_characters.extend(characters)
                # If the number of characters returned is less than the limit, break the loop
                if len(characters) < limit:
                    break
            else:
                print(f"Error fetching characters: {response.status_code}")
                break
        except requests.exceptions.SSLError as e:
            print(f"SSL Error: {e}")
            break

    return all_characters


# Route to display characters
@app.route('/')
def index():
    total_pages = 18  # Adjust this number based on how many pages you want to fetch
    characters = fetch_characters(total_pages)
    return render_template('index.html', characters=characters)


# Run the Flask app
if __name__ == '__main__':
    app.run(debug=True)
