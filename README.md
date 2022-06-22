
## Install

Docker 4.8.2
NextFlow 22.04.4


## Assumptions

- 5' to 3' sequence reads
- Each transcript is unique and do not multimap or have duplicate entries.
- Each alignment and query files are for a given sample/individual. So these are always in pairs.
- Number of transcripts index to query will be in hundreds and thousands of rows
- Number of transcript alignments will be in hundreds of millions of rows


## Strengths
- Memory Efficiency - Since the alignment data will be order of hundreds of millions of rows, I used vaex for my implementation. Vaex provides efficient way to load data in memory by first converting the data to hdf5 which is memory mappable file format. This allows one to load hundreds of millions of rows within local computer with small memory footprint and be able to filter data on that. 
- CPU Efficiency - I used vaex and multiprocessing tools to improve cpu efficiency. Vaex handles the parallelization by using multiprocessing at its core. I have also used multiprocessing to quickly generate test data.
- Unit testing of methods
- Created docker container of tool and used that to run the process in NextFlow.
- Documentation of methods
- Using GitFlow paradigm for tool development
- Tested the implementation with simulated data - 30M alignment rows and 10-1000 row queries. All testing was performed on local computer with 8 cpu and 16 gb memory.

## Weakness
- Haven't tested accuracy with large dataset. Only tested with handfull of small test data
- Tool is designed to handle large alignment file and small set of queries. However, if queries are going to be in several thousands and millions then will need to revisit the implementation.


## Installation

**Clone repo**

`git clone https://github.com/virenar/vaex_exercise`

`git checkout feature/va/vaex_implementation`


**Build docker container**

`cd vaex_exercise/module/query`

`docker build -t query .`

## Example

Test data is created in `vaex_exercise/data` directory

To run directly from docker image. First go the repo directory `cd vaex_exercise`.

**To run `query_vaex.py` directly from docker container**

`docker run -it -v $PWD:$PWD -w $PWD --entrypoint /bin/bash --privileged=true query:latest -c 'python3 /scripts/query_vaex.py -a data/small_test/sample_alignment.txt -q data/small_test/sample_query.txt'`


**To run `query_pandas.py` directly from docker container**

`docker run -it -v $PWD:$PWD -w $PWD --entrypoint /bin/bash --privileged=true query:latest -c 'python3 /scripts/query_pandas.py -a data/small_test/sample_alignment.txt -q data/small_test/sample_query.txt'`

**To run nextflow (only `query_pandas.py` integrated. See Notes below)**

Once nextflow installed, make sure you are using version 22.04.4

`nextflow run main.nf --alignment data/small_test/sample_alignment.txt --query data/small_test/sample_alignment.txt`

## Output

**query_pandas and query_vaex tool output**

Output for both vaex and pandas is stored in `query_results/query_<tool>_results_<date_timestamp>.txt`

**Nextflow output**

Output is stored in `result/query_output_{date_timestamp}/QUERY_PANDAS/<Tool_output>`

## Unit Testing

`cd vaex_exercise`

**To run unit test for query_pandas.py**

`docker run -it -v $PWD:$PWD -w $PWD --entrypoint /bin/bash query:latest -c 'pytest /scripts/query_pandas.py -vv'`

Expected output
```
========================================================================= test session starts =========================================================================
platform linux -- Python 3.8.13, pytest-5.2.1, py-1.11.0, pluggy-0.13.1 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /scripts
plugins: anyio-3.6.1
collected 2 items                                                                                                                                                     

../../../scripts/query_pandas.py::test_indexing_sequences PASSED                                                                                                [ 50%]
../../../scripts/query_pandas.py::test_query PASSED                                                                                                             [100%]

========================================================================== 2 passed in 0.77s ==========================================================================

```


**To run unit test for query_vaex.py**

`docker run -it -v $PWD:$PWD -w $PWD --entrypoint /bin/bash query:latest -c 'pytest /scripts/query_vaex.py -vv'`

Expected output
```
========================================================================= test session starts =========================================================================
platform linux -- Python 3.8.13, pytest-5.2.1, py-1.11.0, pluggy-0.13.1 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /scripts
plugins: anyio-3.6.1
collected 1 item                                                                                                                                                      

../../../scripts/query_vaex.py::test_process_query_to_ref_position PASSED                                                                                       [100%]

========================================================================== 1 passed in 3.59s ==========================================================================

```


## Performance

Testing performed on local computer with 8 CPU and 16GB Memory.

| Dataset | Alignment Rows | Query Rows | Realtime - Pandas Implementation (csv input) | Realtime - Vaex Implementation (memory mappable input) |
| --- | --- | --- | --- | --- |
| Test 1 | 3000 | 10 | 2.119s | 4.703s |
| Test 2 | 300000 | 10 | 1m 12.803s | 6.129s |
| Test 3** | 30000000 | 10 | Out of memory | 36.154s |
| Test 4** | 30000000 | 100 | Out of memory | 44.091s |
| Test 5** | 30000000 | 1000 | Out of memory | 7m 38.289s |

** dataset not included in `data` directory. Test data notebook is included (`notebooks/test_data.ipynb`) for one to recreate the test data 


## Note

  I wanted to wrap the tool into NextFlow to really monitor resource utilization and compare vaex and pandas implementation. With pandas implementation, I was able to configure successfully. However with vaex implementation, I was not able to successfully configure vaex tool docker in NextFlow. Docker daemon seems to not exit properly and will need to look at it further. But thats why you will see NextFlow code around.