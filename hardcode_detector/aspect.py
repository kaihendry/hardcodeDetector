"""CDK Aspect to detect hardcoded physical resource names."""

import jsii
from aws_cdk import IAspect, Annotations, Token
from constructs import IConstruct
from aws_cdk import CfnResource


@jsii.implements(IAspect)
class HardcodedNameDetector:
    """Warns when resources have hardcoded physical names."""

    # Map of CloudFormation property names (PascalCase) to Python attribute names (snake_case)
    NAME_PROPERTIES = {
        "TableName": "table_name",
        "BucketName": "bucket_name",
        "FunctionName": "function_name",
        "QueueName": "queue_name",
        "TopicName": "topic_name",
        "RoleName": "role_name",
        "PolicyName": "policy_name",
        "ClusterName": "cluster_name",
        "SecretName": "secret_name",
        "StreamName": "stream_name",
        "RepositoryName": "repository_name",
        "KeyName": "key_name",
        "LayerName": "layer_name",
        "ApiName": "api_name",
        "StageName": "stage_name",
        "DomainName": "domain_name",
        "HostedZoneName": "hosted_zone_name",
        "DBInstanceIdentifier": "db_instance_identifier",
        "DBClusterIdentifier": "db_cluster_identifier",
    }

    def visit(self, node: IConstruct) -> None:
        """Visit each construct and check for hardcoded names."""
        if isinstance(node, CfnResource):
            for cfn_prop, python_attr in self.NAME_PROPERTIES.items():
                value = getattr(node, python_attr, None)
                # Check if it's a plain string (hardcoded) vs a token/reference
                if value is not None and isinstance(value, str) and not Token.is_unresolved(value):
                    Annotations.of(node).add_warning(
                        f"Hardcoded {cfn_prop}: '{value}' - "
                        "consider using CDK-generated names for developer isolation"
                    )
