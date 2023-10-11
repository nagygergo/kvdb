# RPC

## Commands
### Requests

As part of a single connection the user is only allowed to send exactly one request. Receiving the `FIN` flag signals that the request is fully sent, and it will only be fully parsed at that time.

`SET <key> <value>` - Sets the value of the key in the kvdb

`GET <key>`

`DELETE <key>`


### Requests for reusing connections

If the connection is reused, then commands will be only interpreted if `\n` is sent as a closing byte. If it's not sent, and the connection is interrupted, then the command is discarded. 

`REUSECONN` - Tells the server that multiple commands will be sent over the connection.

`SET <key> <value>\n`

`GET <key>\n`

`DELETE <key>\n` 
### Responses

`<value>` - Successful response for `GET` request.
`000:UnknownError` - Unknown error happened on server side


# Benchmarking

Redis as reference
```
$ redis-benchmark -t set -r 100000 -n 1000000
====== SET ======
  1000000 requests completed in 13.86 seconds
  50 parallel clients
  3 bytes payload
  keep alive: 1

99.76% `<=` 1 milliseconds
99.98% `<=` 2 milliseconds
100.00% `<=` 3 milliseconds
100.00% `<=` 3 milliseconds
72144.87 requests per second
```

This naive kvdb implementation with a an approximation of the above test:

| Type       | Name   | # reqs | # fails  | Avg | Min | Max | Med | req/s   | failures/s |
| ---------- | ------ | ------ | -------- | --- | --- | --- | --- | ------- | ---------- |
| kvdbrpc    | delete | 33873  | 0(0.00%) | 4   | 0   | 27  | 4   | 1708.20 | 0.00       |
| kvdbrpc    | get    | 33883  | 0(0.00%) | 4   | 0   | 31  | 4   | 1708.71 | 0.00       |
| kvdbrpc    | set    | 33900  | 0(0.00%) | 4   | 0   | 31  | 4   | 1709.56 | 0.00       |
| Aggregated | N/A    | 101656 | 0(0.00%) | 4   | 0   | 31  | 4   | 5126.47 | 0.00       |


Response time percentiles (approximated)

| Type       | Name   | 50% | 66% | 75% | 80% | 90% | 95% | 98% | 99% | 99.9% | 99.99% | 100% | # reqs |
| ---------- | ------ | --- | --- | --- | --- | --- | --- | --- | --- | ----- | ------ | ---- | ------ |
| kvdbrpc    | delete | 4   | 5   | 6   | 6   | 7   | 7   | 8   | 8   | 15    | 27     | 27   | 33873  |
| kvdbrpc    | get    | 4   | 5   | 6   | 6   | 7   | 7   | 8   | 9   | 15    | 31     | 31   | 33883  |
| kvdbrpc    | set    | 4   | 5   | 6   | 6   | 7   | 7   | 8   | 9   | 17    | 31     | 31   | 33900  |
| Aggregated | N/A    | 4   | 5   | 6   | 6   | 7   | 7   | 8   | 9   | 16    | 31     | 31   | 101656 |

Improvement ideas:
- Allowing multiple commands to be transmitted over a single connection
- Message sender to send full message size with command, simplifying reading into memory