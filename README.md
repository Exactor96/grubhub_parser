# GrubHub Parser

I have a lot of different improvements for this code, that can be useful only in specific cases, but I need to know more
about the task, infrastructure, etc.

## Solution Explanation

For the base idea of the solution - I tried to use minimum third-party libraries and make the easiest solution.

For this solution I used: `aiohttp` as a third-party library for HTTP requests, it supports asynchronous mode, 
that's why I chose this library. It's the only necessary library for this parser. Other libraries like 
`CSV`, `asyncio`, `urllib` were taken from the standard python library. 
For deployment, this parser only needs a Python 3 (checked with 3.10) and a package manager for python (pip) 
for installing `aiohttp` as the only requirement.


## FIle Structure
* `main.py` Program file and entrypoint
* `README.md` File with descriptions
* `*.csv` Collected data that stored in csv files. Pattern: `<restaurant_id>.csv`
* `test.sh` Bash script for fast testing parser

## Run the parser

```python3 main.py <grubhub-url>```

## Example:

```python3 main.py 'https://www.grubhub.com/restaurant/impeckable-wings-901-nw-24th-st-san-antonio/3159434?hidemenuitem=false'```

## Architecture Explanation
For this solution was chosen CLI architecture because this parser was first of all created to show how to get necessary
data and can easily be modified for something more complex. For requests used an asynchronous HTTP library that speeds
up data collection.

### How it works
1. Authorizing (here parser needs to get an access token, don't require login or password)
2. Sending a request for collecting restaurant base information and menu list
3. Extracting data for the first section of the CSV file
4. For getting modifiers for each menu item, will send an additional HTTP request. Here happens all optimization.
5. CConcurrently running each request and waiting for modifiers' data extracted in each coroutine
6. Deleting non-unique values
7. Save the first section
8. Save the second section
## Scalability
This code can be easily scaled, but first of all, it needs to be modified for async processing multiple URLs. 
For storing URLs better use a database(Postgres), it helps to store only unique URLs and is safer than files or etc. 
For storing results of parser better use same Postgres or MongoDB, depending on GrubHub's schema change.

Next, better CPU utilization can be used with multiprocessing, it helps to make hybrid parallelism 
(asyncio + multiprocessing). Each process takes for example 100-1000 URLs for parsing (for 1 CPU core it's very easy)
and each part can run on a different core (vertical scalability). ***Be careful with RAM usage***.

Next, Kubernetes can help to run this parser on multiple nodes and the message broker can help to synchronize 
all instances of the parser. (horizontal scalability)

## Monitoring
For monitoring can be used `sentry`, `graphana` or a custom solution. The main feature of this code - is the usage of subscript on
dict/json objects. It automatically raises the exception `KeyError` if the scheme of response changed. It means that process 
returns non-zero code. That easily helps detect the problem with the parser and doesn't collect broken data. For alerting system
webhook of slack/telegram/etc. can be used for manual parsing shutdown.

