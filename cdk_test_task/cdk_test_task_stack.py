from aws_cdk import (
    Stack,
    aws_apigateway as api_gw,
    aws_dynamodb as dynamodb,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_notifications as s3n,
    aws_rekognition as rekognition,
    RemovalPolicy,
)
from aws_cdk.aws_iam import Role, ServicePrincipal, ManagedPolicy
from aws_cdk.aws_lambda import Function, Code
from constructs import Construct

import config


class CdkTestTaskStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        lambda_role = Role(
            self,
            f"{config.SERVICE_NAME}-Lambda-Role",
            assumed_by=ServicePrincipal("lambda.amazonaws.com")
        )
        lambda_role.add_managed_policy(
            ManagedPolicy.from_aws_managed_policy_name(config.ADMIN_POLICY_NAME)
        )

        # api gw
        api = api_gw.RestApi(
            self,
            "test-task-api"
        )

        api_resource_general = api.root.add_resource(path_part="blobs")
        api_resource_object = api_resource_general.add_resource("{blob_id}")

        # rekognition
        rekognition_project = rekognition.CfnProject(
            self,
            f"{config.SERVICE_NAME}-blobs-project",
            project_name=f"{config.SERVICE_NAME}-blobs-project"
        )

        # dynamodb
        dynamo = dynamodb.Table(
            self,
            f"{config.SERVICE_NAME}-dynamodb",
            table_name=f"{config.SERVICE_NAME}-blobs",
            partition_key=dynamodb.Attribute(
                name="blob_id", type=dynamodb.AttributeType.STRING
            ),
            removal_policy=RemovalPolicy.DESTROY,
            stream=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES,
        )
        TABLE_NAME = dynamo.table_name
        dynamo_table_stream_arn = dynamo.table_stream_arn

        # bucket
        bucket = s3.Bucket(
            self,
            f"{config.SERVICE_NAME}-bucket",
            bucket_name=f"{config.SERVICE_NAME}-blobs-bucket"
        )
        BUCKET_NAME = bucket.bucket_name

        # lambdas
        create_blob = Function(
            self,
            "create_blob",
            function_name=f"{config.SERVICE_NAME}-cdk-create-blob",
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=Code.from_asset('src/createBlob'),
            environment={
                'TABLE_NAME': TABLE_NAME,
                'BUCKET_NAME': BUCKET_NAME
            }
        )

        process_blob = Function(
            self,
            "process_blob",
            function_name=f"{config.SERVICE_NAME}-cdk-process-blob",
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=Code.from_asset('src/processBlob'),
            environment={
                'TABLE_NAME': TABLE_NAME,
                'BUCKET_NAME': BUCKET_NAME
            }
        )

        get_blob = Function(
            self,
            "get_blob",
            function_name=f"{config.SERVICE_NAME}-cdk-get-blob",
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=Code.from_asset('src/getBlob'),
            environment={
                'TABLE_NAME': TABLE_NAME,
            }
        )

        make_callback = Function(
            self,
            "make_callback",
            function_name=f"{config.SERVICE_NAME}-cdk-make-callback",
            role=lambda_role,
            runtime=_lambda.Runtime.PYTHON_3_8,
            handler="index.handler",
            code=Code.from_asset('src/makeCallback'),
            environment={
                'TABLE_NAME': TABLE_NAME,
            }
        )

        # events
        bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(process_blob)
        )

        api_resource_object.add_method(
            "GET",
            api_gw.LambdaIntegration(
               get_blob
            )
        )

        api_resource_general.add_method(
            "POST",
            api_gw.LambdaIntegration(
                create_blob
            )
        )

        cfn_event_source_mapping = _lambda.CfnEventSourceMapping(
            self,
            "DynamotoCallbackEventSourceMapping",
            function_name=make_callback.function_name,
            batch_size=1,
            event_source_arn=dynamo_table_stream_arn,
            filter_criteria=_lambda.CfnEventSourceMapping.FilterCriteriaProperty(
                     filters=[_lambda.CfnEventSourceMapping.FilterProperty(
                         pattern="{\"eventName\": [\"MODIFY\"]}"
                     )]
            ),
            starting_position="LATEST"
        )
