FROM nilsoberg/kbase-efi:3.8.0-efi-0.5.1

ARG DATA_DIR=/data/efi/0.2.1
RUN mkdir -p $DATA_DIR
ARG TEST_DATA_DIR=/kb/module/data/unit_test/0.1
RUN mkdir -p $TEST_DATA_DIR

### This is for KBase integration.
WORKDIR /kb/module
COPY ./ /kb/module
RUN make all

ARG RESETCONFIG=true

# Configure EFI apps
WORKDIR /apps
#COPY EST /apps/EST
#COPY GNT /apps/GNT
#COPY EFIShared /apps/EFIShared
#COPY EFITools /apps/EFITools
RUN git clone https://github.com/EnzymeFunctionInitiative/EFITools.git
RUN git clone --branch devel https://github.com/EnzymeFunctionInitiative/EST.git
RUN git clone --branch devel https://github.com/EnzymeFunctionInitiative/GNT.git
RUN git clone --branch master https://github.com/EnzymeFunctionInitiative/EFIShared.git

RUN perl /apps/EFIShared/make_efi_config.pl --output /apps/efi.config --db-interface sqlite3
RUN cp /apps/EST/env_conf.sh.example /apps/EST/env_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EST/env_conf.sh EFI_EST=/apps/EST EFI_CONFIG=/apps/efi.config
RUN cp /apps/GNT/env_conf.sh.example /apps/GNT/env_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/GNT/env_conf.sh EFI_GNN=/apps/GNT
RUN cp /apps/EFIShared/env_conf.sh.example /apps/EFIShared/env_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EFIShared/env_conf.sh EFI_SHARED=/apps/EFIShared/lib EFI_GROUP_HOME=/apps/efi
RUN cp /apps/shortbred/ShortBRED/env_conf.sh.example /apps/shortbred/ShortBRED/env_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/shortbred/ShortBRED/env_conf.sh SHORTBRED_APP_HOME=/apps/shortbred/sb_code SHORTBRED_DATA_HOME=/apps/shortbred/sb_data EFI_SHORTBRED_HOME=/apps/shortbred/ShortBRED
RUN cp /apps/EFIShared/db_conf.sh.example /apps/EFIShared/db_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EFIShared/db_conf.sh EFI_SEQ_DB=$DATA_DIR/seq_mapping.sqlite EFI_DB=$DATA_DIR/metadata.sqlite EFI_DB_DIR=$DATA_DIR/blastdb EFI_DIAMOND_DB_DIR=$DATA_DIR/diamonddb EFI_FASTA_PATH=$DATA_DIR/uniprot.fasta
#RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EFIShared/db_conf.sh EFI_SEQ_DB=/kb/module$DATA_DIR/seq_mapping.sqlite EFI_DB=/kb/module$DATA_DIR/metadata.sqlite EFI_DB_DIR=/kb/module$DATA_DIR/blastdb EFI_DIAMOND_DB_DIR=/kb/module$DATA_DIR/diamonddb EFI_FASTA_PATH=/kb/module$DATA_DIR/uniprot.fasta

# This is for unit testing
RUN cp /apps/EFIShared/db_conf.sh.example /apps/EFIShared/testing_db_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EFIShared/testing_db_conf.sh EFI_SEQ_DB=$TEST_DATA_DIR/seq_mapping.sqlite EFI_DB=$TEST_DATA_DIR/metadata.sqlite EFI_DB_DIR=$TEST_DATA_DIR/blastdb EFI_DIAMOND_DB_DIR=$TEST_DATA_DIR/diamonddb EFI_FASTA_PATH=$TEST_DATA_DIR/uniprot.fasta
RUN cp /apps/EST/env_conf.sh.example /apps/EST/testing_env_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EST/testing_env_conf.sh EFI_EST=/apps/EST EFI_CONFIG=/apps/efi.config EFI_NP=4

WORKDIR /kb/module

### For KBase
COPY ./scripts/entrypoint.sh /apps/entrypoint.sh

### For EFI stand-alone
# Copy over the entry point script
ARG STANDALONE
RUN if [ "$STANDALONE" = "1" ]; then \
        cp ./scripts/est_entrypoint.sh /apps/entrypoint.sh && \
        mkdir /apps/test && \
        cp -a ./test_standalone/* /apps/test/ ; \
    fi
RUN chmod +x /apps/entrypoint.sh

ENTRYPOINT [ "/apps/entrypoint.sh" ]

CMD [ ]

