"""cfn-lint custom rule to detect hardcoded physical resource names.

Usage:
    cdk synth
    cfn-lint cdk.out/*.template.json -a cfn_lint_rules/

Or in CI/CD:
    uv run cdk synth
    uv run cfn-lint cdk.out/*.template.json -a cfn_lint_rules/
"""

from cfnlint.rules import CloudFormationLintRule, RuleMatch


class HardcodedResourceNames(CloudFormationLintRule):
    """Check for hardcoded physical resource names."""

    id = "W9001"
    shortdesc = "Hardcoded physical resource name detected"
    description = (
        "Resources with hardcoded physical names prevent multiple deployments "
        "in the same account. Use CDK-generated names for developer isolation."
    )
    source_url = "https://docs.aws.amazon.com/cdk/v2/guide/best-practices.html"
    tags = ["resources", "naming", "best-practices"]

    # Map of CloudFormation resource types to their name properties
    RESOURCE_NAME_PROPERTIES = {
        "AWS::S3::Bucket": ["BucketName"],
        "AWS::DynamoDB::Table": ["TableName"],
        "AWS::DynamoDB::GlobalTable": ["TableName"],
        "AWS::SQS::Queue": ["QueueName"],
        "AWS::SNS::Topic": ["TopicName"],
        "AWS::Lambda::Function": ["FunctionName"],
        "AWS::Lambda::LayerVersion": ["LayerName"],
        "AWS::IAM::Role": ["RoleName"],
        "AWS::IAM::Policy": ["PolicyName"],
        "AWS::IAM::ManagedPolicy": ["ManagedPolicyName"],
        "AWS::IAM::User": ["UserName"],
        "AWS::IAM::Group": ["GroupName"],
        "AWS::SecretsManager::Secret": ["Name"],
        "AWS::SSM::Parameter": ["Name"],
        "AWS::Kinesis::Stream": ["Name"],
        "AWS::KinesisFirehose::DeliveryStream": ["DeliveryStreamName"],
        "AWS::ECR::Repository": ["RepositoryName"],
        "AWS::ECS::Cluster": ["ClusterName"],
        "AWS::ECS::Service": ["ServiceName"],
        "AWS::EKS::Cluster": ["Name"],
        "AWS::StepFunctions::StateMachine": ["StateMachineName"],
        "AWS::Events::Rule": ["Name"],
        "AWS::Events::EventBus": ["Name"],
        "AWS::ApiGateway::RestApi": ["Name"],
        "AWS::ApiGatewayV2::Api": ["Name"],
        "AWS::Cognito::UserPool": ["UserPoolName"],
        "AWS::RDS::DBInstance": ["DBInstanceIdentifier"],
        "AWS::RDS::DBCluster": ["DBClusterIdentifier"],
        "AWS::ElastiCache::CacheCluster": ["ClusterName"],
        "AWS::Elasticsearch::Domain": ["DomainName"],
        "AWS::OpenSearchService::Domain": ["DomainName"],
        "AWS::CloudWatch::Alarm": ["AlarmName"],
        "AWS::Logs::LogGroup": ["LogGroupName"],
        "AWS::KMS::Key": ["KeyId"],  # Usually an alias, but check anyway
        "AWS::KMS::Alias": ["AliasName"],
    }

    def match(self, cfn):
        matches = []

        resources = cfn.get_resources()
        for resource_name, resource_obj in resources.items():
            resource_type = resource_obj.get("Type", "")
            properties = resource_obj.get("Properties", {})

            if resource_type not in self.RESOURCE_NAME_PROPERTIES:
                continue

            name_props = self.RESOURCE_NAME_PROPERTIES[resource_type]
            for name_prop in name_props:
                value = properties.get(name_prop)

                # Check if it's a hardcoded string (not a Ref, Fn::Sub, etc.)
                if self._is_hardcoded_string(value):
                    path = ["Resources", resource_name, "Properties", name_prop]
                    matches.append(
                        RuleMatch(
                            path,
                            f"Hardcoded {name_prop}: '{value}' in {resource_type}. "
                            "Consider removing to allow CDK-generated names for "
                            "developer isolation in shared accounts.",
                        )
                    )

        return matches

    def _is_hardcoded_string(self, value):
        """Check if a value is a hardcoded string (not a CloudFormation intrinsic)."""
        if value is None:
            return False
        if isinstance(value, str):
            return True
        # If it's a dict, it's likely an intrinsic function like Ref, Fn::Sub, etc.
        if isinstance(value, dict):
            return False
        return False
