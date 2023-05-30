import requests
import threading
import time
import os
from dotenv import load_dotenv

# Load Tinybird authentication token from local environment.
dotenv_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
load_dotenv(dotenv_path)
tinybird_token = os.environ.get('TINYBIRD_TOKEN')
tinybird_api_endpoint = 'https://api.tinybird.co/v0/pipes/reports.json' 

# Number of requests to make per minute. This determines the delay between creating a new request thread. 
REQUESTS_PER_MINUTE = 1000
# Calculate the delay between each request in seconds
delay = 60 / REQUESTS_PER_MINUTE

headers = {"Authorization": f"Bearer {tinybird_token}"}

# Set any API query parameters.
sensor_type = 'all'
max_results = 10 
params = {} 
params = {"sensor_type": sensor_type, "max_results": max_results}

def make_request():
    response = requests.get(tinybird_api_endpoint, headers=headers, params=params)
    # Process the response or perform any required actions here
    print(response.status_code)

# Loop to make requests
while True:
    # Create a new thread for each request
    threading.Thread(target=make_request).start()
    
    # Wait for the delay before making the next request
    time.sleep(delay)
