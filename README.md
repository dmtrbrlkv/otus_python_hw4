# OTUServer
Thread pool architecture

## ab benchmark
### server 
```
python3 httpd.py -p8100 -w 100
```
### benchmark

```
ab -n 50000 -c 100 -r localhost:8100/
This is ApacheBench, Version 2.3 <$Revision: 1807734 $>
Copyright 1996 Adam Twiss, Zeus Technology Ltd, http://www.zeustech.net/
Licensed to The Apache Software Foundation, http://www.apache.org/

Benchmarking localhost (be patient)
Completed 5000 requests
Completed 10000 requests
Completed 15000 requests
Completed 20000 requests
Completed 25000 requests
Completed 30000 requests
Completed 35000 requests
Completed 40000 requests
Completed 45000 requests
Completed 50000 requests
Finished 50000 requests


Server Software:        SERVER
Server Hostname:        localhost
Server Port:            8100

Document Path:          /
Document Length:        0 bytes

Concurrency Level:      100
Time taken for tests:   21.089 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      6900000 bytes
HTML transferred:       0 bytes
Requests per second:    2370.87 [#/sec] (mean)
Time per request:       42.179 [ms] (mean)
Time per request:       0.422 [ms] (mean, across all concurrent requests)
Transfer rate:          319.51 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0   23 150.3      0    3046
Processing:     3   19   7.5     18     232
Waiting:        1   18   7.4     17     231
Total:          5   42 151.9     18    3074

Percentage of the requests served within a certain time (ms)
  50%     18
  66%     20
  75%     21
  80%     22
  90%     25
  95%     29
  98%   1024
  99%   1038
 100%   3074 (longest request)


```
