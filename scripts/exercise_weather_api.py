import time
import requests
from dotenv import load_dotenv
load_dotenv()

tinybird_api_endpoint = "https://api.tinybird.co/v0/pipes/weather_data.json"
tinybird_token = os.environ.get('TINYBIRD_TOKEN')

while True: #Just keep making requests... 
    headers = {"Authorization": f"Bearer {tinybird_token}"}
    #params = {"start_date": start_date, "end_date": end_date, "max_results": max_results, "sensor_type": sensor_type}
    #params = {"sensor_type": 'temp', "max_results": 10}
    params = {}
    
    response = requests.get(tinybird_api_endpoint, headers=headers, params=params)
    print(response.json())
    time.sleep(4)  # wait (seconds) before making the next request
