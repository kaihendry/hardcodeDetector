#!/usr/bin/env python3
"""Scan deployed CloudFormation stacks for hardcoded physical resource names.

Usage:
    # Scan all stacks in the default region
    python scripts/scan_deployed_stacks.py

    # Scan specific stacks
    python scripts/scan_deployed_stacks.py MyStack-prod MyStack-dev

    # Scan in a specific region
    AWS_REGION=eu-west-2 python scripts/scan_deployed_stacks.py
"""

import sys
import json
import boto3

# Resource types and their name properties to check
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
    "AWS::SecretsManager::Secret": ["Name"],
    "AWS::SSM::Parameter": ["Name"],
    "AWS::Kinesis::Stream": ["Name"],
    "AWS::ECR::Repository": ["RepositoryName"],
    "AWS::ECS::Cluster": ["ClusterName"],
    "AWS::ECS::Service": ["ServiceName"],
    "AWS::StepFunctions::StateMachine": ["StateMachineName"],
    "AWS::Events::Rule": ["Name"],
    "AWS::ApiGateway::RestApi": ["Name"],
    "AWS::RDS::DBInstance": ["DBInstanceIdentifier"],
    "AWS::RDS::DBCluster": ["DBClusterIdentifier"],
    "AWS::Logs::LogGroup": ["LogGroupName"],
}


def is_hardcoded(value):
    """Check if a value is hardcoded (plain string, not a CloudFormation reference)."""
    if value is None:
        return False
    if isinstance(value, str):
        return True
    # Dicts are intrinsic functions like Ref, Fn::Sub, etc.
    if isinstance(value, dict):
        return False
    return False


def scan_template(template_body, stack_name):
    """Scan a CloudFormation template for hardcoded names."""
    findings = []
    template = json.loads(template_body)
    resources = template.get("Resources", {})

    for logical_id, resource in resources.items():
        resource_type = resource.get("Type", "")
        properties = resource.get("Properties", {})

        if resource_type not in RESOURCE_NAME_PROPERTIES:
            continue

        for name_prop in RESOURCE_NAME_PROPERTIES[resource_type]:
            value = properties.get(name_prop)
            if is_hardcoded(value):
                findings.append({
                    "stack": stack_name,
                    "logical_id": logical_id,
                    "resource_type": resource_type,
                    "property": name_prop,
                    "value": value,
                })

    return findings


def main():
    cfn = boto3.client("cloudformation")

    # Get stack names from args or list all stacks
    if len(sys.argv) > 1:
        stack_names = sys.argv[1:]
    else:
        print("Listing all stacks...", file=sys.stderr)
        paginator = cfn.get_paginator("list_stacks")
        stack_names = []
        for page in paginator.paginate(
            StackStatusFilter=[
                "CREATE_COMPLETE",
                "UPDATE_COMPLETE",
                "UPDATE_ROLLBACK_COMPLETE",
            ]
        ):
            for stack in page["StackSummaries"]:
                stack_names.append(stack["StackName"])
        print(f"Found {len(stack_names)} stacks", file=sys.stderr)

    all_findings = []

    for stack_name in stack_names:
        print(f"Scanning {stack_name}...", file=sys.stderr)
        try:
            response = cfn.get_template(StackName=stack_name)
            template_body = response["TemplateBody"]
            if isinstance(template_body, dict):
                template_body = json.dumps(template_body)
            findings = scan_template(template_body, stack_name)
            all_findings.extend(findings)
        except Exception as e:
            print(f"  Error: {e}", file=sys.stderr)

    # Output results
    if all_findings:
        print(f"\nFound {len(all_findings)} hardcoded resource names:\n")
        for f in all_findings:
            print(f"  [{f['stack']}] {f['logical_id']} ({f['resource_type']})")
            print(f"    {f['property']}: '{f['value']}'")
            print()
        sys.exit(1)
    else:
        print("\nNo hardcoded resource names found.")
        sys.exit(0)


if __name__ == "__main__":
    main()
