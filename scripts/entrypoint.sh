#!/bin/bash

. /kb/deployment/user-env.sh

python ./scripts/prepare_deploy_cfg.py ./deploy.cfg ./work/config.properties

if [ -f ./work/token ] ; then
  export KB_AUTH_TOKEN=$(<./work/token)
fi

if [ $# -eq 0 ] ; then
  sh ./scripts/start_server.sh
elif [ "${1}" = "test" ] ; then
  echo "Run Tests"
  make test
elif [ "${1}" = "async" ] ; then
  sh ./scripts/run_async.sh
elif [ "${1}" = "init" ] ; then
  echo "Initialize module"
  # TODO: this should point to latest, but we don't have a latest DB yet
  efi_url=https://efi.igb.illinois.edu/downloads/databases/20230301_swissprot
  # This should point to a persistent directory that is mounted to the docker path
  if [ "${2}" = "" ]; then
      data_dir="/data/efi/0.2.1"
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
  touch /data/__READY__
elif [ "${1}" = "bash" ] ; then
  bash
elif [ "${1}" = "report" ] ; then
  export KB_SDK_COMPILE_REPORT_FILE=./work/compile_report.json
  make compile
else
  echo Unknown
fi
