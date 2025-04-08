import boto3
import click


def get_current_task_definition(client, cluster, service):
    response = client.describe_services(cluster=cluster, services=[service])
    current_task_arn = response["services"][0]["taskDefinition"]

    response = client.describe_task_definition(taskDefinition=current_task_arn)
    return response


@click.command()
@click.option("--cluster", help="Name of the ECS cluster", required=True)
@click.option("--service", help="Name of the ECS service", required=True)
@click.option("--profile", help="Name of the aws profile", required=False)
@click.option("--region", help="Name of the aws region", required=False)
def deploy(cluster, service, profile, region):

    if profile:

        session = boto3.Session(
            profile_name=profile,
            region_name=region
        )

        # s3 = session.resource('s3')
        client = session.client("ecs")
    else:
        client = boto3.client("ecs")

    response = get_current_task_definition(client, cluster, service)
    container_definition = response["taskDefinition"]["containerDefinitions"][0].copy(
    )

    response = client.register_task_definition(
        family=response["taskDefinition"]["family"],
        volumes=response["taskDefinition"]["volumes"],
        containerDefinitions=[container_definition],
    )
    new_task_arn = response["taskDefinition"]["taskDefinitionArn"]

    response = client.update_service(
        cluster=cluster, service=service, taskDefinition=new_task_arn,
    )


if __name__ == "__main__":
    deploy()
