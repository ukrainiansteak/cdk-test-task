#!/usr/bin/env python3
import os

import aws_cdk as cdk

from cdk_test_task.cdk_test_task_stack import CdkTestTaskStack


app = cdk.App()
CdkTestTaskStack(app,
                 "CdkTestTaskStack",
                 env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'),
                                     region=os.getenv('CDK_DEFAULT_REGION')),
                 )

app.synth()
