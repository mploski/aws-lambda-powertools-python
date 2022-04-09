import json

from aws_lambda_powertools import Logger, Tracer

tracer = Tracer()
logger = Logger()


@tracer.capture_lambda_handler
@logger.inject_lambda_context(log_event=True)
def lambda_handler(event, context):
    print("Received event: " + json.dumps(event, indent=2))

    logger.info("test")
    return "fourth lambda"
