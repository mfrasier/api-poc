#!/usr/bin/env bash

LAYER_NAME=python3-lib-layer
SITE_PACKAGES=.env/lib/python3.7/site-packages
LIB_DIR=layers/python

echo "creating zip file for lambda dependency layer $LAYER_NAME"

rm -rf $LIB_DIR 2>/dev/null
mkdir -p $LIB_DIR

rm layers/$LAYER_NAME.zip 2>/dev/null
cp -r $SITE_PACKAGES/* $LIB_DIR
pushd layers
zip -r $LAYER_NAME.zip python -x 'python/boto*' 'python/aws_cdk*' 'python/jsii*' 'python/docutils*' 'python/pip*'
popd