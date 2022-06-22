
## Install

Docker 4.8.2



## Assumptions

- 5' to 3' sequence reads
- Each transcript is unique and do not multimap or have duplicate entries.
- Each alignment and query files are for a given sample/individual. So these are always in pairs.
- Number of transcripts index to query will be in hundreds and thousands
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

To run `query.py` directly from docker container

`docker run -it -v $PWD:$PWD -w $PWD --entrypoint /bin/bash --privileged=true query:latest -c 'python3 /scripts/query.py -a data/small_test/sample_alignment.txt -q data/small_test/sample_query.txt'`


## Output

Output of the file is stored in `output` followed by date and timestamp


## Testing

To run unit test
`docker run -it -v $PWD:$PWD -w $PWD --entrypoint /bin/bash query:latest -c 'pytest /scripts/query.py -vv'`

Expected output
```
======================================= test session starts =======================================
platform linux -- Python 3.8.13, pytest-5.2.1, py-1.11.0, pluggy-0.13.1 -- /usr/local/bin/python
cachedir: .pytest_cache
rootdir: /scripts
plugins: anyio-3.6.1
collected 2 items                                                                                 

../../../scripts/query.py::test_indexing_sequences PASSED                                   [ 50%]
../../../scripts/query.py::test_query PASSED                                                [100%]

======================================== 2 passed in 0.63s ========================================
```

## Note

  I wanted to wrap the tool into nextflow to really monitor resource utilization and compare vaex and pandas implementation. With pandas implementation, I was able to configure successfully. However with vaex implementation, I was not able to successfully configure. Docker daemon seems to not exit properly and will need to look at it further. But thats why you will see nextflow code around.