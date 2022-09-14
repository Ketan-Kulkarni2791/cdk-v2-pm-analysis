"""Main python file_key for adding resources to the application stack."""
from typing import Dict, Any
import aws_cdk
import aws_cdk.aws_kms as kms
import aws_cdk.aws_sns as sns
from constructs import Construct

from .iam_construct import IAMConstruct
from .kms_construct import KMSConstruct
from .sns_construct import SNSConstruct


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