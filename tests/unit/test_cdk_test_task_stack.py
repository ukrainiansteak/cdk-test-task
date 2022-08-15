import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_test_task.cdk_test_task_stack import CdkTestTaskStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_test_task/cdk_test_task_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkTestTaskStack(app, "cdk-test-task")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
