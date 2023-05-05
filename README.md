# weather-api-example
A demo to illustrate how to go from an API design to implementing (and hosting) it on tinybird...

The first step was finding a data source to work with. 

## Loading weather data into Tinybird.

The JSON we are sending looks like this:

```json
{
	"timestamp": "2023-05-04 18:07:08",
	"site_name": "New York City",
	"temp_f": 52.12,
	"precip": 0.0,
	"humidity": 79,
	"pressure": 1017,
	"wind_speed": 10.36,
	"wind_dir": 190,
	"clouds": 100,
	"description": "overcast clouds"
}

```


Sending these weather report JSON objects to Tinybird via the Events API.
``` python
 # Send the JSON object to the Tinybird Events API
 headers = {"Authorization": f"Bearer {tinybird_token}", "Content-Type": "application/json"}
 response = requests.post(tinybird_url, headers=headers, data=json_data)
```    

## API Endpoint design

### Endpoints 
* One `/weather_data.json` endpoint that returns weather data. 

### Query parameters 
  * We are serving temporal data, so will want `start_time` and `end_time` query parameters.
    * `start_time` defaults to 7 days ago. 
    * `end_time` defaults to the time of the request time (i.e. now).  
    * So one week of data is returned if you do not specify these.
    * Note: All timestamps are in UTC.
  * Let's users request a specific `sensor_type`. Supported values: `temp`, `precip`, `wind`, `hunidity`, `pressure`, and `clouds`. Note that `wind` returns both velocity (mph) and direction (degrees).  
  * Let's have a `max_results` for giving users controls on how much they retrieve. 
  * Let the user select a single `city` to get data for. 


### Example requests

In the form of example requests, here is the design:

* Request the latest 1000 weather reports from around the US. 
```
https://api.tinybird.co/v0/pipes/weather_data.json&max_results=1000
```

* Request temperature reports only from around the US.
```
https://api.tinybird.co/v0/pipes/weather_data.json?sensor_type=temp
```

* Request just temperature data from the city of Minneapolis. 
```
weather_data?city=minneapolis&sensor_type=temp
```

* Request data for the city of Denver, and for May 3, 2023, midnight to midnight local time (MDT).
```
weather_data?city=denver&start_time=2023-05-03 06:00:00&end_time=2023-05-04 06:00:00
```

* Show me the top ten precipitation 1-hr totals over the past week. 
```
weather_data?city=minneapolis&sensor_type=precip&max_results=10
```

## Implementing API on Tinybird

