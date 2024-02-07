from flask import Flask, render_template
from authlib.integrations.flask_client import OAuth
from config import FLASK_SECRET_KEY, SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
import requests

app = Flask(__name__)
app.config['SECRET_KEY'] = FLASK_SECRET_KEY

# Spotify OAuth setup for client credentials flow
oauth = OAuth(app)
spotify = oauth.register(
    name='spotify',
    client_id=SPOTIFY_CLIENT_ID,
    client_secret=SPOTIFY_CLIENT_SECRET,
    authorize_url=None,
    authorize_params=None,
    access_token_url='https://accounts.spotify.com/api/token',
    redirect_uri=None,
    client_kwargs={'scope': 'user-library-read'}  # Adjust the scope as needed
)

print("Spotify OAuth Object: ", spotify)

@app.route('/test-connection')
def spotify_index():
    # Fetch data from Spotify API using client credentials
    token_request_params = {
        'grant_type': 'client_credentials',
        'client_id': SPOTIFY_CLIENT_ID,
        'client_secret': SPOTIFY_CLIENT_SECRET,
    }

    print("Request being sent to Spotify token endpoint:")
    print(f"URL: {spotify.access_token_url}")
    print(f"Params: {token_request_params}")

    # Make the request and obtain the response
    response = requests.post(spotify.access_token_url, data=token_request_params)

    print("Response from Spotify token endpoint:")
    print(f"Status Code: {response.status_code}")
    print(f"Content: {response.text}")

    response_data = response.json()

    # TODO: Check if response_data includes access_token
    access_token = response_data['access_token']
    print(f"Access token: {access_token}")

    # Use the access token to make API requests
    categories_url = 'https://api.spotify.com/v1/browse/categories'
    headers = {'Authorization': f'Bearer {access_token}'}   
    params = {'limit': 20, 'offset': 0} 

    # TODO: Handle status code != 200
    categories_response = requests.get(categories_url, headers=headers)
    categories = categories_response.json().get('categories', {}).get('items', [])

    return render_template('category-index.html', categories=categories)

if __name__ == "__main__":
    app.run(debug=True)