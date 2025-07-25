from aws_cdk import (
    Stack,
    aws_dynamodb as dynamodb,
)
from constructs import Construct


class DynamoDBStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create a DynamoDB table
        self.table = dynamodb.Table(
            self,
            "RealmActivityTable",
            partition_key=dynamodb.Attribute(
                name="PlayerName", type=dynamodb.AttributeType.STRING  # Partition key
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
        )
