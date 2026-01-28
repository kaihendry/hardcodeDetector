#!/usr/bin/env python3
"""CDK app demonstrating the HardcodedNameDetector aspect."""

import aws_cdk as cdk
from aws_cdk import Aspects

from hardcode_detector.aspect import HardcodedNameDetector
from hardcode_detector.stack import ExampleStack

app = cdk.App()

stack = ExampleStack(
    app,
    "HardcodeDetectorStack",
    env=cdk.Environment(region="eu-west-2"),
)

# Apply the aspect to detect hardcoded names
Aspects.of(app).add(HardcodedNameDetector())

app.synth()
