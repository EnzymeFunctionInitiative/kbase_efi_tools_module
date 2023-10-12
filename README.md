# kbase_efi_tools_module



# Standalone - Run through Docker

    docker build -t est_standalone --build-arg DATA_DIR=/data/efi/db --build-arg STANDALONE=1 .

## Test

    mkdir /tmp/output
    docker run -it --mount type=bind,source=/tmp/output,target=/data/output est_standalone test /data/output


