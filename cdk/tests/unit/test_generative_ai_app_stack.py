import aws_cdk as core
import aws_cdk.assertions as assertions

from generative_ai_app.generative_ai_app_stack import GenerativeAiAppStack

# example tests. To run these tests, uncomment this file along with the example
# resource in generative_ai_app/generative_ai_app_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = GenerativeAiAppStack(app, "generative-ai-app")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
