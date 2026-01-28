"""Example stack with both hardcoded and CDK-generated names."""

from aws_cdk import Stack, RemovalPolicy
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_dynamodb as dynamodb
from aws_cdk import aws_sqs as sqs
from constructs import Construct


class ExampleStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # BAD: Hardcoded name - will be detected
        s3.Bucket(
            self,
            "HardcodedBucket",
            bucket_name="my-hardcoded-bucket-name",  # Warning!
            removal_policy=RemovalPolicy.DESTROY,
        )

        # GOOD: CDK-generated name - no warning
        s3.Bucket(
            self,
            "GeneratedBucket",
            removal_policy=RemovalPolicy.DESTROY,
        )

        # BAD: Hardcoded table name - will be detected
        dynamodb.Table(
            self,
            "HardcodedTable",
            table_name="users-table",  # Warning!
            partition_key=dynamodb.Attribute(
                name="id", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
        )

        # BAD: Hardcoded queue name - will be detected
        sqs.Queue(
            self,
            "HardcodedQueue",
            queue_name="my-queue",  # Warning!
        )
