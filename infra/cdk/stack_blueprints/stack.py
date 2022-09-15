"""Main python file_key for adding resources to the application stack."""
from typing import Dict, Any
import aws_cdk
import aws_cdk.aws_kms as kms
import aws_cdk.aws_sns as sns
import aws_cdk.aws_iam as iam
import aws_cdk.aws_lambda as _lambda
from constructs import Construct

from .iam_construct import IAMConstruct
from .kms_construct import KMSConstruct
from .sns_construct import SNSConstruct
from .s3_construct import S3Construct
from .lambda_layer_construct import LambdaLayerConstruct


class MainProjectStack(aws_cdk.Stack):
    """Build the app stacks and its resources."""
    def __init__(self, env_var: str, scope: Construct, 
                 app_id: str, config: dict, **kwargs: Dict[str, Any]) -> None:
        """Creates the cloudformation templates for the projects."""
        super().__init__(scope, app_id, **kwargs)
        self.env_var = env_var
        self.config = config
        MainProjectStack.create_stack(self, self.env_var, config=config)

    @staticmethod
    def create_stack(stack: aws_cdk.Stack, env: str, config: dict) -> None:
        """Create and add the resources to the application stack"""

        # KMS infra setup ------------------------------------------------------
        kms_pol_doc = IAMConstruct.get_kms_policy_document()

        kms_key = KMSConstruct.create_kms_key(
            stack=stack,
            config=config,
            policy_doc=kms_pol_doc
        )
        print(kms_key, env)

        # SNS Infra Setup -----------------------------------------------------
        sns_topic = MainProjectStack.setup_sns_topic(
            config,
            kms_key,
            stack
        )
        print(sns_topic)

        # IAM Role Setup --------------------------------------------------------
        stack_role = MainProjectStack.create_stack_role(
            config=config,
            stack=stack,
            kms_key=kms_key,
            sns_topic=sns_topic
        )
        print(stack_role)

        # Lambda Layers --------------------------------------------------------
        layer = MainProjectStack.create_layers_for_lambdas(
            stack=stack,
            config=config
        )
        print(layer)

    @staticmethod
    def setup_sns_topic(
            config: dict,
            kms_key: kms.Key,
            stack: aws_cdk.Stack) -> sns.Topic:
        """Set up the SNS Topic and returns the SNS Topic Object."""
        sns_topic = SNSConstruct.create_sns_topic(
            stack=stack,
            config=config,
            kms_key=kms_key
        )
        SNSConstruct.subscribe_email(config=config, topic=sns_topic)
        return sns_topic

    @staticmethod
    def create_stack_role(
        config: dict,
        stack: aws_cdk.Stack,
        kms_key: kms.Key,
        sns_topic: sns.Topic
    ) -> iam.Role:
        """Create the IAM role."""

        stack_policy = IAMConstruct.create_managed_policy(
            stack=stack,
            config=config,
            policy_name="mainStack",
            statements=[
                KMSConstruct.get_kms_key_encrypt_decrypt_policy(
                    [kms_key.key_arn]
                ),
                S3Construct.get_s3_object_policy([config['global']['bucket_arn']]),
                SNSConstruct.get_sns_publish_policy(sns_topic.topic_arn)
            ]
        )
        stack_role = IAMConstruct.create_role(
            stack=stack,
            config=config,
            role_name="mainStack",
            assumed_by=["s3", "lambda"]
        )
        stack_role.add_managed_policy(policy=stack_policy)
        return stack_role

    @staticmethod
    def create_layers_for_lambdas(
            stack: aws_cdk.Stack,
            config: dict) -> Dict[str, _lambda.LayerVersion]:
        """Method to create layers."""
        layers = {}
        # requirement layer for general ----------------------------------------------------
        layers["pmanalysis_layer1"] = LambdaLayerConstruct.create_lambda_layer(
            stack=stack,
            config=config,
            layer_name="pmanalysis_layer1",
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_8
            ]
        )
        layers["pmanalysis_layer2"] = LambdaLayerConstruct.create_lambda_layer(
            stack=stack,
            config=config,
            layer_name="pmanalysis_layer2",
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_8
            ]
        )
        layers["pmanalysis_layer3"] = LambdaLayerConstruct.create_lambda_layer(
            stack=stack,
            config=config,
            layer_name="pmanalysis_layer3",
            compatible_runtimes=[
                _lambda.Runtime.PYTHON_3_8
            ]
        )
        return layers