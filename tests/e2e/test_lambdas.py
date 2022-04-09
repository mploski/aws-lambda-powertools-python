import subprocess
import tempfile
import uuid
from pathlib import Path

import boto3
import pytest
from aws_cdk import App, CfnOutput, Stack
from aws_cdk.aws_lambda import Code, Function, LayerVersion, Runtime

HANDLER_DIR = "handlers"

session = boto3.Session()
cf_client = session.client("cloudformation")
lambda_client = session.client("lambda")

# Helpers


def get_lambda_arn(outputs):
    lambda_arn = None
    for output in outputs:
        if output["OutputKey"] == "lambdaArn":
            lambda_arn = output["OutputValue"]
    return lambda_arn


def load_handler_file(tmp_filename, handler_filename):

    with open(tmp_filename, mode="wb+") as tmp:
        with open(handler_filename, mode="rb") as handler:
            for line in handler:
                tmp.write(line)
    return tmp


def trigger_lambda(lambda_arn):
    response = lambda_client.invoke(
        FunctionName=lambda_arn, InvocationType="RequestResponse"
    )
    return response


# Create CDK cloud assembly code
def cdk_infrastructure(handler_file, stack_name):
    integration_test_app = App()
    stack = Stack(integration_test_app, stack_name)
    powertools_layer = LayerVersion.from_layer_version_arn(
        stack,
        "aws-lambda-powertools",
        "arn:aws:lambda:us-east-1:017000801446:layer:AWSLambdaPowertoolsPython:15",
    )

    code = Code.from_asset(str(Path(handler_file).parent))

    function_python = Function(
        stack,
        "MyFunction",
        runtime=Runtime.PYTHON_3_9,
        code=code,
        handler=f"{Path(handler_file).stem}.lambda_handler",
        layers=[powertools_layer],
    )
    CfnOutput(stack, "lambdaArn", value=function_python.function_arn)
    integration_test_app.synth()
    return integration_test_app


# Deploy synthesized code using CDK CLI
def deploy_app(path, stack_name):
    result = subprocess.run(
        [
            "cdk",
            "deploy",
            "--app",
            str(path),
            "--require-approval",
            "never",
            "--hotswap",
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    print(result.returncode, result.stdout, result.stderr)

    outputs = cf_client.describe_stacks(StackName=stack_name)["Stacks"][0]["Outputs"]
    return outputs


# PYTEST SPECIFIC
@pytest.fixture(scope="session")
def deploy_infrastructure():
    # in order to use hotswap we create tmp file that we specify as cdk lambda asset
    # and we dynamically change its content
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_filename = f"{tmp_dir}/tmp.py"
        stack_name = f"test-lambda-{uuid.uuid4()}"

        def deploy(handler_filename):
            load_handler_file(
                tmp_filename=tmp_filename, handler_filename=handler_filename
            )
            app = cdk_infrastructure(handler_file=tmp_filename, stack_name=stack_name)

            outputs = deploy_app(path=app.outdir, stack_name=stack_name)
            lambda_arn = get_lambda_arn(outputs=outputs)
            return lambda_arn, app

        yield deploy
        # Ensure stack deletion is triggered at the end of the test session
        cf_client.delete_stack(StackName=stack_name)


# tests
def test_first_lambda(deploy_infrastructure):
    lambda_arn, _ = deploy_infrastructure(handler_filename=f"{HANDLER_DIR}/handler.py")
    result = trigger_lambda(lambda_arn=lambda_arn)
    assert result["Payload"].read() == b'"first lambda"'


def test_second_lambda(deploy_infrastructure):
    lambda_arn, _ = deploy_infrastructure(handler_filename=f"{HANDLER_DIR}/handler2.py")
    result = trigger_lambda(lambda_arn=lambda_arn)
    assert result["Payload"].read() == b'"second lambda"'


def test_third_lambda(deploy_infrastructure):
    lambda_arn, _ = deploy_infrastructure(handler_filename=f"{HANDLER_DIR}/handler3.py")
    result = trigger_lambda(lambda_arn=lambda_arn)
    assert result["Payload"].read() == b'"third lambda"'


def test_fourth_lambda(deploy_infrastructure):
    lambda_arn, _ = deploy_infrastructure(handler_filename=f"{HANDLER_DIR}/handler4.py")
    result = trigger_lambda(lambda_arn=lambda_arn)
    assert result["Payload"].read() == b'"fourth lambda"'
