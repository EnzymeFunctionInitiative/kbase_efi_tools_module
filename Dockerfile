FROM kbase/sdkpython:3.8.0

ENV PIP_PROGRESS_BAR=off
RUN apt-get -y update
RUN apt-get -y install libpng-dev libargtable2-dev zlib1g-dev libgd-dev libfreetype-dev libmariadb-dev-compat
RUN apt-get -y install cpanminus unzip git r-base dos2unix

RUN pip install --upgrade pip
RUN pip install weblogo pytest-subtests parameterized


###################################################################################################
# Install Perl modules
RUN mkdir /build
WORKDIR /build
COPY cpanfile /build/cpanfile
RUN cpanm -v --installdeps .

# Force install the Bio::HMM:Logo module (it uses Consensus::Colors which doesn't have a perl
# installer).
RUN mkdir /build/consensus-colors
RUN mkdir /usr/lib/x86_64-linux-gnu/perl-base/Consensus
RUN curl -sL https://github.com/Janelia-Farm-Xfam/Consensus-Colors/archive/refs/heads/master.zip > /build/consensus-colors.zip
RUN unzip /build/consensus-colors.zip
RUN cp /build/Consensus-Colors-master/lib/Consensus/Colors.pm /usr/lib/x86_64-linux-gnu/perl-base/Consensus/
RUN cpanm -v --force https://github.com/Janelia-Farm-Xfam/Bio-HMM-Logo.git


###################################################################################################
# INSTALL APPS
RUN mkdir -p /apps/bin
RUN echo 'export PATH=$PATH:/apps/bin' > /apps/env.sh

#############################
# Install BLAST
RUN curl -sL https://ftp.ncbi.nlm.nih.gov/blast/executables/blast+/2.13.0/ncbi-blast-2.13.0+-x64-linux.tar.gz > /build/ncbi-blast-2.13.0+-x64-linux.tar.gz
#COPY ncbi-blast-2.13.0+-x64-linux.tar.gz /build/ncbi-blast-2.13.0+-x64-linux.tar.gz
RUN tar zxvf /build/ncbi-blast-2.13.0+-x64-linux.tar.gz
RUN mv /build/ncbi-blast-2.13.0+/bin /apps/ncbi-blast-2.13.0+
RUN echo 'export PATH=$PATH:/apps/ncbi-blast-2.13.0+' > /apps/blast_modern.sh
RUN curl -sL https://ftp.ncbi.nlm.nih.gov/blast/executables/legacy.NOTSUPPORTED/2.2.26/blast-2.2.26-x64-linux.tar.gz > /build/blast-2.2.26-x64-linux.tar.gz
#COPY blast-2.2.26-x64-linux.tar.gz /build/blast-2.2.26-x64-linux.tar.gz
RUN tar zxvf /build/blast-2.2.26-x64-linux.tar.gz
RUN mv /build/blast-2.2.26/bin /apps/blast-2.2.26
RUN echo 'export PATH=$PATH:/apps/blast-2.2.26' > /apps/blast_legacy.sh

RUN rm -rf /build/*

#############################
# Install CD-HIT
RUN curl -sL https://github.com/weizhongli/cdhit/releases/download/V4.8.1/cd-hit-v4.8.1-2019-0228.tar.gz > /build/cd-hit-v4.8.1-2019-0228.tar.gz
WORKDIR /build
RUN tar zxvf cd-hit-v4.8.1-2019-0228.tar.gz
WORKDIR /build/cd-hit-v4.8.1-2019-0228
RUN make
WORKDIR /build
RUN mv cd-hit-v4.8.1-2019-0228 /apps/
RUN echo 'export PATH=$PATH:/apps/cd-hit-v4.8.1-2019-0228' >> /apps/env.sh

#############################
# Install
RUN curl -sL https://github.com/rcedgar/muscle/releases/download/5.1.0/muscle5.1.linux_intel64 > /apps/bin/muscle
#TODO: this is not a properly-licensed copy. It is only here for testing/MVP, and will be corrected before app moves to production
RUN curl -sL http://www.drive5.com/downloads/usearch11.0.667_i86linux32.gz > /build/usearch.gz
RUN gunzip /build/usearch.gz
RUN mv /build/usearch /apps/bin/usearch

#
RUN curl -sL http://www.clustal.org/omega/clustalo-1.2.4-Ubuntu-x86_64 > /apps/bin/clustalo

#
RUN curl -sL https://github.com/bbuchfink/diamond/releases/download/v0.9.30/diamond-linux64.tar.gz > /build/diamond-linux64.tar.gz
WORKDIR /build
RUN tar zxvf /build/diamond-linux64.tar.gz
RUN mv /build/diamond /apps/bin/diamond

###################################################################################################
# Install EFI apps
WORKDIR /apps

RUN mkdir /apps/shortbred
WORKDIR /apps/shortbred
RUN mkdir /apps/shortbred/sb_data
RUN mkdir /apps/shortbred/sb_code
RUN git clone https://github.com/EnzymeFunctionInitiative/ShortBRED.git
#TODO: for now, we just include the necessary data files inside the git repo, but eventually we may
# want to provide this as a separate download.
WORKDIR /apps/shortbred/ShortBRED
RUN unzip sb_data.zip
RUN mv sb_data/* /apps/shortbred/sb_data/
RUN unzip sb_code.zip
RUN mv sb_code/* /apps/shortbred/sb_code/
RUN rm -rf sb_data sb_code

RUN mkdir -p /data/efi/0.1
RUN mkdir -p /data/job

ARG RESETCONFIG=false

RUN apt-get install -y wget
RUN wget -qO- https://cloud.r-project.org/bin/linux/ubuntu/marutter_pubkey.asc | tee -a /etc/apt/trusted.gpg.d/cran_ubuntu_key.asc
RUN apt-get update
RUN apt-get install -y software-properties-common
RUN apt-get update
RUN add-apt-repository "deb https://cloud.r-project.org/bin/linux/ubuntu $(lsb_release -cs)-cran40/"
#RUN apt-get update
RUN add-apt-repository -y ppa:c2d4u.team/c2d4u4.0+
RUN apt-get update
RUN apt-get install -y r-cran-hmisc

ARG DATADIR=/data/efi/0.2.1
RUN mkdir -p $DATADIR

### This is for KBase integration.  It can be commented out to run the EFI family app in standalone mode.
WORKDIR /kb/module
COPY ./requirements.txt /kb/module/requirements.txt
ENV PIP_PROGRESS_BAR=off
#RUN pip install --upgrade pip
RUN pip install -r requirements.txt
RUN pip install -e git+https://github.com/kbase-sfa-2021/sfa.git#egg=base
COPY ./ /kb/module
RUN mkdir -p /kb/module/work
RUN chmod -R a+rw /kb/module
RUN make all


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
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EFIShared/db_conf.sh EFI_SEQ_DB=$DATADIR/seq_mapping.sqlite EFI_DB=$DATADIR/metadata.sqlite EFI_DB_DIR=$DATADIR/blastdb EFI_DIAMOND_DB_DIR=$DATADIR/diamonddb EFI_FASTA_PATH=$DATADIR/uniprot.fasta
#RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EFIShared/db_conf.sh EFI_SEQ_DB=/kb/module$DATADIR/seq_mapping.sqlite EFI_DB=/kb/module$DATADIR/metadata.sqlite EFI_DB_DIR=/kb/module$DATADIR/blastdb EFI_DIAMOND_DB_DIR=/kb/module$DATADIR/diamonddb EFI_FASTA_PATH=/kb/module$DATADIR/uniprot.fasta

# This is for unit testing
ARG TESTPATH=/kb/module/data/unit_test/0.1
RUN cp /apps/EFIShared/db_conf.sh.example /apps/EFIShared/testing_db_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EFIShared/testing_db_conf.sh EFI_SEQ_DB=$TESTPATH/seq_mapping.sqlite EFI_DB=$TESTPATH/metadata.sqlite EFI_DB_DIR=$TESTPATH/blastdb EFI_DIAMOND_DB_DIR=$TESTPATH/diamonddb EFI_FASTA_PATH=$TESTPATH/uniprot.fasta
RUN cp /apps/EST/env_conf.sh.example /apps/EST/testing_env_conf.sh
RUN perl /apps/EFIShared/edit_env_conf.pl /apps/EST/testing_env_conf.sh EFI_EST=/apps/EST EFI_CONFIG=/apps/efi.config EFI_NP=4


### For EFI stand-alone
#COPY ./scripts/est_entrypoint.sh /apps/entrypoint.sh
#COPY ./test/est_test.py /apps/est_test.py
#ENTRYPOINT [ "/bin/bash", "/apps/entrypoint.sh" ]

WORKDIR /kb/module
ENTRYPOINT [ "./scripts/entrypoint.sh" ]

CMD [ ]

