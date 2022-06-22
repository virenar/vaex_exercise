#!/usr/bin/env python

import pandas as pd
import numpy as np
import re
import multiprocessing as mp
import time
import os
import logging
import argparse

# dict to store reference and query sequence index
manager = mp.Manager()
alignment_index_dict = manager.dict()

# output directory structure
timestamp = time.strftime("%Y%m%d-%H%M%S")
outdir = f'query_results'
scratch = f'{outdir}/scratch'
if not os.path.exists(scratch):
    os.makedirs(scratch)

# output result file
tmp_query_results = f'{scratch}/tmp_query_results_{timestamp}.txt'
outfile = f'{outdir}/query_pandas_results_{timestamp}.txt'


def indexing_sequences(alignment):
    '''To index reference and query sequence

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
    alignment : array
        Array containing alignment info. Four elements in the array are
        sequence id, chromosome name, 0-based start position of sequence on
        reference genome, and CIGAR string indicating the mapping information.

    Returns
    -------
    None

    '''
    seq_id, chrom, ref_start_position, cigar_string = alignment
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
                            {alignment}")

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
    # logging.info(f'{cigar_string}\n{string_info}\n{ref_array}\n{query_array}')

    try:
        len(ref_array) == len(query_array)
    except ValueError as e:
        logging.info(f"Reference array and query array are not equal")
        logging.exception(e)

    try:
        alignment_index_dict[seq_id] = [chrom, ref_array,
                                        query_array]
    except ValueError as e:
        logging.info(f"Not a valid transcript id {seq_id}")
        logging.exception(e)


def query(transcript):
    '''To obtain reference genome coordinate for a given query sequence index

    Function takes the transcript info and performs query to obtain reference
    genome position.

    Parameters
    ---------
    transcript : array
        Array containing transcript info. Two elements in the array are
        sequence id and 0-based coordinate of the query sequence.

    '''
    index, seq_id, query_position = transcript
    try:
        chrom, ref_array, query_array = alignment_index_dict[seq_id]
    except KeyError as e:
        chrom, ref_array, query_array = ['', '', '']
        logging.debug(f'Not a valid sequence id {seq_id}')
        logging.exception(e)

    try:
        ref_position = int(ref_array[list(query_array).index(query_position)])
    except ValueError as e:
        ref_position = ''
        logging.debug(f'Not a valid query position {query_position}')
        logging.exception(e)
    with open(tmp_query_results, 'a') as f:
        f.write(f'{index}\t{seq_id}\t{query_position}\t{chrom}\t\
                {ref_position}\n')


def perform_query(sequence_alignment, sequence_query):
    '''To perform indexing of sequences and query of the transcripts

    Function performs query

    Parameters
    ----------
    sequence_alignment : dataframe

    sequence_query : dataframe

    '''
    logging.info('Starting multiprocessing pool')
    p = mp.Pool(processes=mp.cpu_count())

    logging.info('Multiprocessing query and reference index')
    p.map(indexing_sequences, sequence_alignment.values.tolist())

    logging.info('Multiprocessing queries')
    p.map(query, sequence_query.values.tolist())
    p.close()

    logging.info('Generating output')
    output = format_output(tmp_query_results)
    return output


def format_output(filepath):
    '''To format output dataframe to same order as input


    Parameters
    ----------
    filepath : str
        Scratch filepath where the query results are stored in unsorted manner
    Returns
    -------
    output : dataframe
        Pandas dataframe containing the output in same order as input query

    '''
    output = pd.read_csv(filepath, sep='\t', header=None)
    output.set_index(0, inplace=True)
    output.sort_index(inplace=True)
    output.reset_index(drop=True, inplace=True)
    output.columns = list(range(0, 4))
    output.to_csv(outfile, index=False, header=False, sep='\t')
    return output


def test_indexing_sequences():
    '''To run a test on indexing sequences to see if indexing is generating an
    expected output

    Function performs a test

    '''
    test_input = ['TR1', 'CHR1', 3, '8M7D6M2I2M11D7M']
    expected_output = {
                        'TR1': [
                                'CHR1',
                                np.array([
                                            3,  4,  5,  6,  7,  8,  9, 10, 11,
                                            12, 13, 14, 15, 16, 17, 18, 19,
                                            20, 21, 22, 23, 24, 24, 24, 25, 26,
                                            27, 28, 29, 30, 31, 32, 33, 34,
                                            35, 36, 37, 38, 39, 40, 41, 42,
                                            43], dtype='int32'),
                                np.array([
                                            0,  1,  2,  3,  4,  5,  6,  7,  8,
                                            8,  8,  8,  8,  8,  8,  8,  9, 10,
                                            11, 12, 13, 14, 15, 16, 17, 18,
                                            18, 18, 18, 18, 18, 18, 18, 18,
                                            18, 18, 18, 19, 20, 21, 22, 23,
                                            24], dtype='int32')
                                ]
    }

    indexing_sequences(test_input)
    assert alignment_index_dict['TR1'][0] == expected_output['TR1'][0]
    np.testing.assert_array_equal(
                                    alignment_index_dict['TR1'][1],
                                    expected_output['TR1'][1])
    np.testing.assert_array_equal(
                                    alignment_index_dict['TR1'][2],
                                    expected_output['TR1'][2])


def test_query():
    '''To run a test on sample data to see if query is generating an expected
    output

    Function performs a test

    '''
    sequence_alignment = pd.read_csv('data/small_test/sample_alignment.txt',
                                     sep='\t', header=None)
    query_sequence = pd.read_csv('data/small_test/sample_query.txt',
                                 sep='\t', header=None)
    expected_output = pd.read_csv('data/small_test/sample_output.txt',
                                  sep='\t', header=None)

    query_sequence.reset_index(inplace=True)
    output = perform_query(sequence_alignment, query_sequence)
    assert output.equals(expected_output)


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
    sequence_alignment = pd.read_csv(args.alignment, sep='\t', header=None)
    query_sequence = pd.read_csv(args.query, sep='\t', header=None)
    query_sequence.reset_index(inplace=True)

    perform_query(sequence_alignment, query_sequence)
    logging.info('Analysis Completed')