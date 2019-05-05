# otus_python_hw4
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
Time taken for tests:   21.686 seconds
Complete requests:      50000
Failed requests:        0
Non-2xx responses:      50000
Total transferred:      6900000 bytes
HTML transferred:       0 bytes
Requests per second:    2305.58 [#/sec] (mean)
Time per request:       43.373 [ms] (mean)
Time per request:       0.434 [ms] (mean, across all concurrent requests)
Transfer rate:          310.71 [Kbytes/sec] received

Connection Times (ms)
              min  mean[+/-sd] median   max
Connect:        0    0   0.2      0       5
Processing:     2   43   3.4     42      77
Waiting:        1   43   3.4     42      77
Total:          6   43   3.3     42      77

Percentage of the requests served within a certain time (ms)
  50%     42
  66%     43
  75%     44
  80%     45
  90%     47
  95%     49
  98%     53
  99%     55
 100%     77 (longest request)


```
