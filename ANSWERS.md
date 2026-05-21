# ANSWERS.md

## 1. How to run

You need Python 3.7 or above. No pip installs required.

1) First generate a test log file:
```
python scripts/generate_logs.py
```
2) Then run the analyzer:
```
python analyzer.py logs/sample.log
```

Pass any log file path as the argument.



## 2. Stack choice

I went with plain Python 3 and no external libraries. The standard library has everything needed for this, re for regex, json for parsing JSON lines, collections for counting things. It also means the tool just works on any machine with Python without needing to install anything.
A worse choice would have been something like  C++ or C. I have never done such work using these 2 languages and by using Python i didnt have to depend on external libraries or other stack options.


## 3. One real edge case

The response time can come in three formats: `142ms`, `0.142s`, or just `142`. Without handling this, comparing response times across entries breaks completely. A line with `0.142s` would look 1000 times faster than `142ms` because we'd be comparing 0.142 vs 142 as raw numbers.
This is handled in the `parse_response_time` function in `analyzer.py` around line 23. It checks for the `ms` suffix first, then the `s` suffix and multiplies by 1000 to convert, then falls back to treating a bare number as milliseconds. If this wasn't there, the slowest endpoint report would be wrong and some entries would just be dropped from the stats entirely.


## 4. AI usage

I used Claude while building this.

I asked it to help me figure out what functions to write and what the overall structure should look like. It suggested breaking things into separate parse functions for timestamp, response time, and status code, and then a main parse loop that tries JSON first and falls back to regex. That structure made sense so I kept it.
I also asked it for help writing the regex pattern to match a standard log line. It gave me something that worked but used `.*` in a few places which was too greedy and would eat into adjacent fields. I changed those to `\S+` so each capture group only takes one whitespace-separated token. I also used it for debugging and sample logs.


## 5. Honest gap

The slowest endpoints report uses average response time. Averages are not great for this because one really slow request can pull the average up and make an endpoint look bad, or a bunch of slow requests can be hidden behind fast ones. The right thing to do would be showing the 95th or 99th percentile instead. With another day I would sort the response times per endpoint and compute percentiles, it is not a hard change just did not get to it.
