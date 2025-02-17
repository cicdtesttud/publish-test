#!/bin/bash

tmp_dir=$(mktemp -ud /tmp/libtsl-dev-XXXXXX)

curl -L "https://github.com/db-tu-dresden/TSL/releases/latest/download/tsl.tar.gz" -o ${TMP_DIR}/tsl.tar.gz