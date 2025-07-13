#!/usr/bin/env python3
import aws_cdk as cdk
from lib.dynamo_stack import DynamoDBStack
from lib.lambda_stack import LambdaStack

app = cdk.App()

# Create the DynamoDB stack
dynamodb_stack = DynamoDBStack(app, "DynamoDBStack")

# Create the Lambda stack and pass the DynamoDB table as a parameter
lambda_stack = LambdaStack(app, "LambdaStack", dynamodb_table=dynamodb_stack.table)

app.synth()
