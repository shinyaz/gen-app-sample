#!/usr/bin/env python3
import os
import aws_cdk as cdk
from gen_app.gen_app_stack import GenAppStack

app = cdk.App()
GenAppStack(app, "GenAppStack",)

app.synth()
