# weather-api-example
A demo to illustrate how to go from an API design to implementing (and hosting) it on tinybird...

## API Endpoint design

Important notes:
* All timestamps are in UTC.

In the form of example requests, here is the design:

Request the latest 1000 weather reports from around the US. 
```
https://api.tinybird.co/v0/pipes/weather_data.json&max_results=1000
```

Request temperature reports only from around the US.

```
https://api.tinybird.co/v0/pipes/weather_data.json?sensor_type=temp
```


```
weather_data?city=denver&start_time=2023-05-03 06:00:00&end_time=2023-05-04 06:00:00
```

```
weather_data?city=minneapolis&sensor_type=precip&max_results=10
```


```
weather_data?city=minneapolis&sensor_type=temp
```
