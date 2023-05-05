import time
import requests
from dotenv import load_dotenv
dotenv_path = os.path.join(os.path.dirname(__file__), 'config', '.env')
load_dotenv(dotenv_path)

tinybird_api_endpoint = "https://api.tinybird.co/v0/pipes/weather_data.json"
tinybird_token = os.environ.get('TINYBIRD_TOKEN')
#start_time = "2023-05-01T00:00"
#end_time = "2023-05-01T12:00"

while True:
    headers = {"Authorization": f"Bearer {tinybird_token}"}
    params = {"sensor_type": 'temp', "max_results": 10}
    params = {}
    #params = {"start_date": start_date, "end_date": end_date, "max_results": max_results, "sensor_type": sensor_type}
    response = requests.get(tinybird_api_endpoint, headers=headers, params=params)
    print(response.json())
    time.sleep(4)  # wait (seconds) before making the next request
