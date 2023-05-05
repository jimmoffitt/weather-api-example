# weather-api-example
A demo to illustrate how to go from an API design to implementing (and hosting) it on tinybird...

The first step was finding a data source to work with. After searching around, I landed on https://openweathermap.org/, with their free plan for the "Current weather and forecasts" service. It seems to offer a generous amount of API calls per minute, and the http://api.openweathermap.org/data/2.5/weather endpoint has been a pleasure to work with. 

Admittedly, this demo has its roots in an overall semi-silly design, where we are pulling data from a weather API just to turn around and make the data available from another weather API. 

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

The root URL for all of these examples is `https://api.tinybird.co/v0/pipes/weather_data.json`. In these examples, we will reference just the `/weather_data.json` portion along with the query parameters.

* Request the latest 1000 weather reports from around the US. 
```
/weather_data.json&max_results=1000
```

* Request temperature reports only from around the US.
```
/weather_data.json?sensor_type=temp
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
For the above request, we are baking in a 'special' convention, where if you specify use `sensor_type` AND set `max_results`, you will get the highest values for that sensor type. 

## Implementing API on Tinybird

{introduction to the Tinybird concepts of Workspaces, Data Sources, Pipes, and Nodes.}

One of the joys of designing endpoints with Tinybird is that you can iteratively apply simple SQL queries and chain them together. This enables you to essentially break up complicated queries into more simple building blocks. These multiple queries are written in separate Nodes, and those nodes are chained together to create a data processing Pipe. When your queries are producing a data view of your liking, you can then publish that last Node in the Pipe as an API Endpoint. 

For this example, the Pipe is named "weather_data" and its end result is publihed as the '/weather_data' endpoint. 

This Pipe is made up of the following nodes:

* city_and_period_of_interest
* sensor_type
* endpoint


### city_and_period_of_interest Node

### sensor_type Node

### endpoint Node


