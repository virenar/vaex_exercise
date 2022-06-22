
## Install

Docker 4.8.2



## Assumptions

- 5' to 3' sequence reads
- Each transcript is unique and do not multimap or have duplicate entries.
- Each alignment and query files are for a given sample/individual. So these are always in pairs.
- Number of transcripts index to query will be in hundreds and thousands of rows
- Number of transcript alignments will be in hundreds of millions


## Strengths
- Memory Efficiency - Since the alignment data will be order of hundreds of millions of rows, I used vaex for my implementation. Vaex provides efficient way to load data in memory by first converting the data to hdf5 columnar based storage. This allows one to load hundreds of millions of rows within local computer of 16 gb. and be able to filter on that data. 
- CPU Efficiency - I used vaex and multiprocessing tools to improve cpu efficiency. Vaex handles the parallelization by using multiprocessing at its core. I have also used multiprocessing to quickly generate test data.
- Unit testing of methods
- Created docker container of tool and used that to run the process in NextFlow.
- Documentation of methods
- Using GitFlow paradigm for tool development
- CI/CD implemented
- Tested the implementation with simulated data - 30M alignment rows and 10-1000 row queries. All testing was performed on local computer with 8 cpu and 16 gb. memory.

## Weakness
- Haven't tested accuracy with large dataset. Only tested with handfull of small test data
- Tool is designed to handle large alignment file and small set of queries. However, if queries are going to be in several thousands and millions then will need to revisit the implementation.


## Example

**Clone repo**

`git clone https://github.com/virenar/vaex_exercise`

`git checkout feature/va/vaex_implementation`


**Build docker container**
`cd vaex_exercise/module/query`

`docker build -t query .`

**Test Data**
Test data is created in `vaex_exercise/data` directory

**To run `query_vaex.py` directly from docker container**

`cd vaex_exercise`

`docker run -it -v $PWD:$PWD -w $PWD --entrypoint /bin/bash --privileged=true query:latest -c 'python3 /scripts/query_vaex.py -a data/small_test/sample_alignment.txt -q data/small_test/sample_query.txt'`


**To run `query_pandas.py` directly from docker container**

`docker run -it -v $PWD:$PWD -w $PWD --entrypoint /bin/bash --privileged=true query:latest -c 'python3 /scripts/query_pandas.py -a data/small_test/sample_alignment.txt -q data/small_test/sample_query.txt'`

**To run nextflow (only `query_pandas.py` integrated. See Notes below)**

`nextflow run main.nf --alignment data/test_1/sample_alignment_1.txt --query data/test_1/sample_query_1.txt`

## Output

**query_pandas and query_vaex tool output**
Output is stored in `query_results/query_pandas_results_<date_timestamp>.txt` and `query_results/query_vaex_results_<date_timestamp>.txt`

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

Testing performed on local computer with 8 CPU and 16GB. Memory

| Dataset | Alignment Rows | Query Rows | Pandas Realtime | Vaex Realtime |
| --- | --- | --- | --- | --- |
| Test 1 | 3000 | 10 | < 30s | 5.071s |
| Test 2 | 300000 | 10 | 1m 32s | 6.129s |
| Test 3 | 30000000 | 10 | Out of memory | 
| Test 4 | 30000000 | 100 | Out of memory | 
| Test 5 | 30000000 | 1000 | Out of memory | > 2h


## Note

  I wanted to wrap the tool into nextflow to really monitor resource utilization and compare vaex and pandas implementation. With pandas implementation, I was able to configure successfully. However with vaex implementation, I was not able to successfully configure vaex tool docker in nextflow. Docker daemon seems to not exit properly and will need to look at it further. But thats why you will see nextflow code around.