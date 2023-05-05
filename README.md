# weather-api-example
A demo to illustrate how to go from an API design to implementing (and hosting) it on tinybird... 

The main topics here are:
* Coming up with a design for a single endpoint of an API used to get current and recent weather data. 
* Demonstrating how that design is translated to and implemented with Tinybird. 

While this example focuses on publishing weather data, the underlying concepts should apply to an other data domain. 

The first step was finding a data source to work with. After searching around, I landed on https://openweathermap.org/, with their free plan for the "Current weather and forecasts" service. It seems to offer a generous amount of API calls per minute, and the http://api.openweathermap.org/data/2.5/weather endpoint has been a pleasure to work with. 

Admittedly, this demo has its roots in an overall semi-silly design, where we are pulling data from a weather API just to turn around and make the data available from another weather API. Yet the patterns demonnstrated here apply to however you ingest your 'source' data into Tinybird. You could easily imagine some other generator of weather data standing in for OpenWeatherMap. 

## The building blocks of Tinybird

To get started, let's establish the terms we'll use to describe what we are building. 

The 'moving' pieces of Tinybird can be represented by these fundamental objects:
* Workspaces - an organizing object used to host Data Sources, Pipes, and Nodes. As well as the storage needed for the persisted data.   
* Data Sources - represents an archive of data that is continually receiving new data. Data Sources can be thought of as database tables. Time-to-lives can be set to limit the history retained. 
* Pipes - Data passes through a Pipe on the way to generating API Endpoint responses. The source of a Pipe is a Data Source. Pipes host one or more Nodes, which are linked together in a sequence. 
* Nodes - Nodes contain instructions for selecting, filtering, ordering, and joining data. These instructions are defined with SQL. Nodes are executed in order, meaning you can apply simple queries, one at a time, instead of needing to develop one complicated query. Nodes are also where API Endpoint query parameters are implemented using a scripting notation embedded in the SQL (see examples below).
* API Endpoint - Any Node can be published as an API Endpoint. 

Note that there are other important build blocks such as Auth Tokens and Organizations for when your use case needs multiple Workspaces. On top of that, there are APIs that support each of these objects. 

## Loading weather data into Tinybird.

The first step of implementing a Tinybird API Endpoint is creating a Data Source, and establishing an ingestiom process to provide 'fresh' data.  There are many ways to ingest data into Tinybird, and the one you'll use depends on how your data is generated. Real-time data is commonly published to kafka-based streams. Data is commonly loaded into data stores ranging from local databases to cloud-based data stores such as BigQuery and Snowflake. And one of the most common pathways is making API requests to a third-party generator and sending that data to Tinybird using the Events API. That is the pathway that drives this demo, requesting data from the OpenWeatherMap API, preparing a simple 'weather report' JSON object and posting it to the Events API.  


For this example, the 'weather report' JSON we are sending looks like this:

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

Creating a new Data Source by posting JSON with the new Data Source `weather_data` name:
```curl
curl \
      -X POST 'https://api.tinybird.co/v0/events?name=weather_data' \
      -H "Authorization: Bearer {TOKEN}" \
      -d $' {"timestamp": "2023-05-01 12:45:53","site_name": "New York City","temp_f": 59.65,"precip": 0.0,"humidity": 41,"pressure": 994,"wind_speed": 21.85,"wind_dir": 240,"clouds": 100,"description": "overcast clouds"}'
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
  * Let users request a specific `sensor_type`. Supported values: `temp`, `precip`, `wind`, `hunidity`, `pressure`, and `clouds`. Note that `wind` returns both velocity (mph) and direction (degrees).  
  * Let's have a `max_results` for giving users control on how much they retrieve. 
  * Let the user select a single `city` to get data for. 


### Example requests

In the form of example requests, here is the design:

The root URL for all of these examples is `https://api.tinybird.co/v0/pipes/weather_data.json`. In these examples, we will reference just the `/weather_data.json` portion along with the query parameters.

* Request the latest 1000 weather reports from around the US. 
```
/weather_data.json&max_results=1000
```

* Request precipitation reports from around the US.
```
/weather_data.json?sensor_type=precip
```

* Request just temperature data from the city of Minneapolis. 
```
weather_data?city=minneapolis&sensor_type=temp
```

* Request data for the city of Denver, and for May 3, 2023, midnight to midnight local time (MDT).
```
weather_data?city=denver&start_time=2023-05-03 06:00:00&end_time=2023-05-04 06:00:00
```

* Retrieve the top ten precipitation 1-hr totals over the past week. 
```
weather_data?sensor_type=precip&max_results=10
```
For the above request, we are baking in a 'special' convention, where if you specify use `sensor_type` AND set `max_results`, you will get the highest values for that sensor type. In all other cases (when `sensor_type` is NOT used), the data is ordered temporally in reverse chronological order. 

For the purposes of this demo, we now have the design of our first API Endpoint. We have landed on a set of query parameters that should provide users flexible ways to retrieve current and recent weather data from across the US. Now it's time to implement the API Endpoint on Tinybird. 



## Implementing API on Tinybird

One of the joys of designing endpoints with Tinybird is that you can iteratively apply simple SQL queries and sequence them in order. This enables you to essentially break up complicated queries into more simple building blocks. These multiple queries are written in separate Nodes, and those Nodes are sequenced together to create a data processing Pipe. When your queries are producing a data view of your liking, you can then publish that Node as an API Endpoint. 

For this example, the Pipe is named "weather_data" and its end result is publihed as the '/weather_data' endpoint. 

This Pipe is made up of the following nodes:

* city_and_period_of_interest: where the `city`, `start_time`, and `end_time` 
* sensor_type
* endpoint


### city_and_period_of_interest Node
In this Node, we are checking for the use of the `city`, `start_time`, and `end_time` parameters. All of these are checked for and applied in the WHERE clause. By applying these here, we can reduce the amount of data retrieved during this first query. This is where we apply the "period of interest" logic, where `start_time` defaults to seven days ago, and where `end_time` defaults to now(). 

Here is what that Node defintion looks like:

```sql
NODE city_and_period_of_interest
DESCRIPTION >
    Applying 'city', 'start_time', and 'end_time' query parameters. A case where we pull in every field and do not take this opportunity to drop fields. The fields arriving via the Event API have already been curated by a Python script.

SQL >

    %
    SELECT *
    FROM incoming_weather_data
    WHERE
        1=1
         {% if defined(city) %}
            AND lowerUTF8(site_name) LIKE lowerUTF8({{ String(city, description="Name of US City to retrieve data for.") }})
         {% end %}
         {% if defined(start_time) and defined(end_time) %}
             AND (toDateTime(timestamp) BETWEEN {{DateTime(start_time, description="Start date in format YYYY-MM-DD HH:MM:SS. Defaults to one week ago if not defined.")}}
             AND {{DateTime(end_time, description="End date in format YYYY-MM-DD HH:MM:00. Defaults to NOW if not defined.")}})
         {% end %}
         {% if not defined(start_time) and not defined(end_time) %}
            AND toDateTime(timestamp) BETWEEN addDays(now(),-7) AND now()
         {% end %}
         {% if defined(start_time) and not defined(end_time) %}
             AND toDateTime(timestamp) BETWEEN {{DateTime(start_time, description="Start date in format YYYY-MM-DD. Defaults to yesterday if not defined.")}}
             AND now()
         {% end %}
```

### sensor_type Node
In this Node, we check if the `sensor_type` parameter is used, and if it is, we use the setting to affect the SELECT fields. Here we have a if/else-if/else statement that SELECTs just type selected, or else includes all the types. 

```sql
NODE sensor_type
DESCRIPTION >
    Here we support the sensor_type query parameters. When used, just that data type is returned.

SQL >

    %
    SELECT
        timestamp,
        site_name,
        {% if defined(sensor_type) %}
            {% if String(sensor_type, description="Type of weather data to return. Options: temp, precip, wind, humidity, pressure, and clouds. ") == 'temp' %} temp_f
            {% elif sensor_type == 'precip' %} precip
            {% elif sensor_type == 'wind' %} wind_speed, wind_dir
            {% elif sensor_type == 'humidity' %} humidity
            {% elif sensor_type == 'pressure' %} pressure
            {% elif sensor_type == 'clouds' %} clouds
            {% end %}
        {% else %}
            temp_f,
            precip,
            wind_speed,
            wind_dir,
            humidity,
            pressure,
            clouds,
            description
        {% end %} 
    FROM city_and_period_of_interest
```

### endpoint Node

In this Node, we apply the `max_results` parameter. If the `sensor_type` parameter is not include, we just apply the `max_results` as the query LIMIT and ORDER by timestamp DESC. If the `sensor_type` is included, we do the extra work to ORDER BY the value of that type in descending order, while applying `max_results` as a LIMIT on those results. This convention enables the retrieval of the "top X" of highest temperatures, or precipitation, or whatever type, for the time period and location of interest. Or "top" values for the entire US over the last week.

```sql
NODE endpoint
DESCRIPTION >
    Here we apply the 'max_results' parameter, and if a sensor_type parameter is included, we order by descending values of that sensor type. So, sensor_type=temp&limit=10 will return the top highest temperatures for the period of interest.

SQL >
    %
    SELECT * FROM sensor_type
    {% if defined(sensor_type) and defined(max_results) %}
        {% if sensor_type == 'temp' %} 
          ORDER BY temp_f DESC
        {% elif sensor_type == 'precip' %} 
          ORDER BY precip DESC
        {% elif sensor_type == 'wind' %} 
          ORDER BY wind_speed DESC
        {% elif sensor_type == 'humidity' %} 
          ORDER BY humidity DESC	
        {% elif sensor_type == 'pressure' %} 
          ORDER BY pressure DESC
        {% elif sensor_type == 'clouds' %} 
          ORDER BY clouds DESC
        {% end %}
    {% else %}
      ORDER BY timestamp DESC
    {% end %} 
    {% if defined(max_results) %}
    LIMIT {{Int16(max_results, description="The maximum number of weather data points to return.")}}
    {% end %}

```
