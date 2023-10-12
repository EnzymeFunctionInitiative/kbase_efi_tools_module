#!/bin/bash

 if [ "${1}" = "est" ] ; then
    out_dir=$2
    json=$3
    database_dir=$4
    source /apps/env.sh
    source /apps/blast_legacy.sh
    source /apps/EST/env_conf.sh
    source /apps/EFIShared/env_conf.sh
    source /apps/EFIShared/db_conf.sh
    script_file=`perl /apps/EST/create_job.pl --job-dir $out_dir --params $json --env-scripts /apps/env.sh,/apps/EST/env_conf.sh,/apps/EFIShared/env_conf.sh,/apps/EFIShared/db_conf.sh`
    echo "Executing $script_file"
    bash $script_file
elif [ "${1}" = "test" ] ; then
    echo "Running test"
    if [ "${2}" = "" ]; then
        echo "Require output dir as second parameter"
        exit 1
    fi
    export JOB_DIR=$2
    /bin/bash /apps/test/run_standalone.sh
elif [ "${1}" = "bash" ] ; then
    bash
elif [ "${1}" = "init" ] ; then
    # TODO: this should point to latest, but we don't have a latest DB yet
    efi_url=https://efi.igb.illinois.edu/downloads/databases/20230301_swissprot
    # This should point to a persistent directory that is mounted to the docker path
    if [ "${2}" = "" ]; then
        data_dir="/data/efi/1.0"
    else
        data_dir=$2
    fi
    mkdir -p $data_dir
    curl -ksL $efi_url/blastdb.zip > $data_dir/blastdb.zip
    curl -ksL $efi_url/diamonddb.zip > $data_dir/diamonddb.zip
    curl -ksL $efi_url/uniprot.fasta.zip > $data_dir/uniprot.fasta.zip
    curl -ksL $efi_url/seq_mapping.sqlite.zip > $data_dir/seq_mapping.sqlite.zip
    curl -ksL $efi_url/metadata.sqlite.zip > $data_dir/metadata.sqlite.zip
    unzip -o $data_dir/blastdb.zip -d $data_dir/blastdb
    unzip -o $data_dir/diamonddb.zip -d $data_dir/diamonddb
    unzip -o $data_dir/uniprot.fasta.zip -d $data_dir
    unzip -o $data_dir/seq_mapping.sqlite.zip -d $data_dir
    unzip -o $data_dir/metadata.sqlite.zip -d $data_dir
    rm $data_dir/*.zip
fi

