import aws_cdk as core
import aws_cdk.assertions as assertions

from cdk_lab_network.cdk_lab_network_stack import CdkLabNetworkStack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_lab_network/cdk_lab_network_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkLabNetworkStack(app, "cdk-lab-network")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
