nextflow.enable.dsl=2

alignment_ch = Channel.fromPath ( params.alignment )
query_ch =     Channel.fromPath ( params.query )


process QUERY_PANDAS {
    tag "${alignment}"
    container 'query:latest'
    cpus 6
    memory 15.GB
    publishDir "${params.publish_dir}/query_output_${params.timestamp}/${task.process.replaceAll(":","_")}"

    input:
        path(alignment)
        path(query)
    output:
        path 'query_results*'

    script:
    """
    python3 /scripts/query_pandas.py -a ${alignment} -q ${query}
    """
}

process QUERY_VAEX {
    tag "${alignment}"
    container 'query:latest'
    cpus 6
    memory 15.GB
    publishDir "${params.publish_dir}/query_output_${params.timestamp}/${task.process.replaceAll(":","_")}"

    input:
        path(alignment)
        path(query)
    output:
        path 'query_results*'

    script:
    """
    python3 /scripts/query_vaex.py -a ${alignment} -q ${query}
    """
}


workflow {
    QUERY_PANDAS ( alignment_ch, query_ch )
    // QUERY_VAEX ( alignment_ch, query_ch )
}