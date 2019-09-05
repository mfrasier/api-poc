#!/usr/bin/env python3

from aws_cdk import core

from api_poc.api_poc_stack import ApiPocStack


app = core.App()
ApiPocStack(app, "api-poc")

app.synth()
