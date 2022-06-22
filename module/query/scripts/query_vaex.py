#!/usr/bin/env python

import pandas as pd
import numpy as np
import vaex
import re
import time
import os
import logging
import argparse

# output directory structure
timestamp = time.strftime("%Y%m%d-%H%M%S")
outdir = f'query_results'
scratch = f'{outdir}/scratch'
if not os.path.exists(scratch):
    os.makedirs(scratch)

# output result file
outfile = f'{outdir}/query_vaex_results_{timestamp}.txt'


def get_output(tx_id, query_position):
    '''To get output info for each query

    Function takes the query information and generates required outputs

    Paramters
    ---------
    tx_id : string
        Row from the 0-column from Query file

    query_position : int
        Row from the 1-column from Query file

    Returns
    -------
    (chrom, ref_position) : tuple 
        Returns chrom and reference position mapping to query position
    
    '''

    try:
        records = sequence_alignment[sequence_alignment['0'] == tx_id]
        if len(records) >= 1:
            logging.debug(f'There are multiple alignments for {tx_id}')
            chrom = records.to_records()[0]['1']
            ref_start = records.to_records()[0]['2']
            cigar_string = records.to_records()[0]['3']
            ref_position = process_query_to_ref_position(cigar_string,
                                                         ref_start,
                                                         query_position)
        if len(records) == 0 :
            logging.debug(f'There is no transcript id in alignment {tx_id}')
            chrom = ''
            ref_start = 0
            cigar_string = ''
            ref_position = -1
    except IndexError as e:
        chrom = ''
        ref_position = -1
        logging.info(f'There are no transcripts in alignment for {tx_id}')
    return((chrom, ref_position))


def process_query_to_ref_position(cigar_string, ref_start_position,
                                  query_index):
    '''To index reference and query sequence and provide ref position for query
    index

    Function takes the alignment sequence information and creates an index of
    query and reference based on the sequence alignment information provided in
    CIGAR string. Query and reference array are stored in a dictionary with key
    being sequence id. From samtools documentation. There are only set of
    operators in CIGAR string.

    | Operator | Description | Sequence mapping |
    | :------: | :---------- | :---- |
    | M | alignment match | Present in QUERY & REFERENCE |
    | I | insertion to the reference | Present in QUERY |
    | D | deletion from the reference | Present in REFERENCE |
    | N | skipped region from the reference | Present in REFERENCE |
    | S | soft clipping | Present in QUERY |
    | H | hard clipping |Present in None |
    | P | padding | Present in None |
    | = | sequence match | Present in QUERY & REFERENCE |
    | X | sequence mismatch | Present in QUERY & REFERENCE |

    Parameters
    ----------
    cigar_string : str
        CIGAR string indicating the mapping information
    
    ref_start_position : int
        0-based start position of sequence on reference genome
    
    query_index : int
        0-based item from 1-column from Query file

    Returns
    -------
    ref_position : int
        Reference position mapping to the query index position

    '''
    ref_array = np.array([]).astype('int32')
    query_array = np.array([]).astype('int32')
    query_start_position = 0
    try:
        string_info = re.findall(r'(\d+)(\w)', cigar_string)
    except ValueError as e:
        logging.info(f"Not a valid CIGAR string {cigar_string}")
        logging.exception(e)

    for number, operator in string_info:
        # assess whether the CIGAR operators are valid
        if operator not in ['M', 'I', 'D', 'N', 'S', 'H', 'P', '=', 'X']:
            raise Exception(f"Not a valid CIGAR operator {operator}: \
                            {cigar_string}")

        if operator in ['M', '=', 'X']:
            # present in query and reference
            ref_position = range(
                                    ref_start_position,
                                    ref_start_position+int(number))
            query_position = range(
                                    query_start_position,
                                    query_start_position+int(number))
            ref_array = np.append(ref_array, list(ref_position))
            query_array = np.append(query_array, list(query_position))
            ref_start_position += int(number)
            query_start_position += int(number)
        if operator in ['D', 'N']:
            # present in reference only
            ref_position = range(
                                    ref_start_position,
                                    ref_start_position+int(number))
            query_position = [query_start_position]*int(number)
            ref_array = np.append(ref_array, list(ref_position))
            query_array = np.append(query_array, query_position)
            ref_start_position += int(number)
        if operator in ['I', 'S']:
            # present in query only
            ref_position = [ref_start_position]*int(number)
            query_position = range(
                                    query_start_position,
                                    query_start_position+int(number))
            ref_array = np.append(ref_array, ref_position)
            query_array = np.append(query_array, list(query_position))
            query_start_position += int(number)
        if operator in ['H', 'P']:
            # present in none
            ref_position = [ref_start_position]*int(number)
            query_position = [query_start_position]*int(number)
            ref_array = np.append(ref_array, ref_position)
            query_array = np.append(query_array, query_position)
    logging.info(f'{cigar_string}\t{string_info}\t{ref_array}\t{query_array}')
    
    try:
        len(ref_array) == len(query_array)
    except ValueError as e:
        logging.info(f"Reference array and query array are not equal")
        logging.exception(e)

    
    try:
        ref_position = int(ref_array[list(query_array).index(query_index)])
    except ValueError as e:
        ref_position = -1
        logging.debug(f'Not a valid query position {query_index}')
        logging.exception(e)

    return ref_position

# def test_get_output():



def test_process_query_to_ref_position():
    '''To run a test on indexing sequences to see if indexing is generating an
    expected output

    Function performs a test

    '''

    cigar_string, ref_start, query_index = ['8M7D6M2I2M11D7M', 3, 13]
    expected_output = 23

    output = process_query_to_ref_position(cigar_string , ref_start, 
                                           query_index)

    assert output == expected_output


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Tool generates reference\
                                                  sequence position for a\
                                                  given set of query sequence\
                                                  indexes""")
    parser.add_argument('-a', '--alignment', required=True,
                        type=argparse.FileType('r', encoding='UTF-8'),
                        help="Specify path of the sequence alignment")
    parser.add_argument('-q', '--query', required=True,
                        type=argparse.FileType('r', encoding='UTF-8'),
                        help='Specify path of the query sequences')

    args = parser.parse_args()

 
    logging.basicConfig(filename=f'{scratch}/log_{timestamp}.txt')
    logging.info('Starting Analysis')
    logging.info('Read alignment and query inputs')

    print('Reading files')
    query_sequence = vaex.read_csv(args.query, chunk_size=10000,
                                   convert=True, sep='\t', header=None)

    sequence_alignment = vaex.read_csv(args.alignment, chunk_size=1000000,
                                        convert=True, sep='\t', header=None)


    print('Apply on query vaex dataframe')
    res = query_sequence.apply( get_output, 
                                arguments=[query_sequence['0'],
                                           query_sequence['1']], 
                                vectorize=False)
    res = res.evaluate()
    print('Convert result to pandas')
    res_vx = vaex.from_pandas(pd.DataFrame(res))
    print('Join dataframe')
    query_sequence = query_sequence.join(res_vx, lprefix='left')
    print('Exporting Results')
    query_sequence.export_csv(
        outfile,
        sep='\t', index=False, header=False)
    logging.info('Analysis Completed')
    print('Analysis Completed')
