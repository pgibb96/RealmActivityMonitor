from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    Duration,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
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
                "DYNAMODB_TABLE_NAME": dynamodb_table.table_name,
            },
            timeout=Duration.seconds(15),
        )

        # Grant the Lambda function permissions to access the DynamoDB table
        dynamodb_table.grant_read_write_data(lambda_function)

        # Create a rule to trigger Lambda every 30 minutes
        rule = events.Rule(
            self, "RealmActivitySchedule",
            schedule=events.Schedule.rate(Duration.minutes(30))
        )
        rule.add_target(targets.LambdaFunction(lambda_function))

        lambda_function.role.add_to_policy(
            iam.PolicyStatement(
                actions=["ssm:GetParameter"],
                resources=[
                    f"arn:aws:ssm:{self.region}:{self.account}:parameter/discord/webhook"
                ]
            )
)