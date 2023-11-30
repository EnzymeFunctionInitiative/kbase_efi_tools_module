# kbase_efi_tools_module



# Standalone - Run through Docker

    docker build -t <TAG_NAME> --build-arg DATA_DIR=/data/efi/db --build-arg STANDALONE=1 .

## Test

    mkdir /tmp/output
    docker run -it --mount type=bind,source=/tmp/output,target=/data/output <TAG_NAME> test /data/output

## Run through Singularity

    mkdir /tmp/output
    # Run the unit tests
    # Replace the tag with the appropriate version (e.g. the latest, look on https://hub.docker.com/repository/docker/nilsoberg/kbase-efi/general)
    singularity run --bind /tmp/output:/data/output docker://nilsoberg/kbase-efi:standalone-0.5.1 test /data/output


