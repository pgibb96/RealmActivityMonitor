from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
)
from constructs import Construct

class LambdaStack(Stack):
    def __init__(self, scope: Construct, id: str, dynamodb_table, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a Lambda function
        lambda_function = _lambda.Function(
            self, "RealmActivityLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="main.lambda_handler",  # Update with your Lambda handler
            code=_lambda.Code.from_asset("../RealmActivityMonitor"),  # Path to your Lambda code
            environment={
                "DYNAMODB_TABLE_NAME": dynamodb_table.table_name
            }
        )

        # Grant the Lambda function permissions to access the DynamoDB table
        dynamodb_table.grant_read_write_data(lambda_function)