import os
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_ecr as ecr,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_logs as logs,
    aws_ecs_patterns as ecs_patterns,
)
from aws_cdk.aws_ecr_assets import (DockerImageAsset, Platform)
from aws_cdk.aws_iam import (Effect, PolicyStatement)
import cdk_ecr_deployment as ecrdeploy
from constructs import Construct


class GenAppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Get AWS Account ID and Region
        account_id = self.account
        region = self.region

        resource_name = "gen-app"

        # ECS, Fargate
        # Create ECR Repository
        ecr_repository = ecr.Repository(
            self,
            "EcrRepo",
            repository_name=f"{resource_name}-assets-{account_id}-{region}",
            removal_policy=RemovalPolicy.DESTROY,
            empty_on_delete=True)

        # Create Docker Image Asset
        docker_image_asset = DockerImageAsset(
            self,
            "DockerImageAsset",
            directory=os.path.join(
                os.path.dirname(__file__), '..', '..', 'app'),
            platform=Platform.LINUX_AMD64)

        # Deploy Docker Image to ECR Repository
        ecrdeploy.ECRDeployment(
            self,
            "DeployDockerImage",
            src=ecrdeploy.DockerImageName(
                docker_image_asset.image_uri),
            dest=ecrdeploy.DockerImageName(f"{account_id}.dkr.ecr.{region}.amazonaws.com/{ecr_repository.repository_name}:latest"))

        # Create VPC and Subnet
        vpc = ec2.Vpc(
            self,
            "Vpc",
            vpc_name=f"{resource_name}-vpc",
            max_azs=2,
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/20"),
            subnet_configuration=[
                {
                    "cidrMask": 24,
                    "name": f"{resource_name}-public",
                    "subnetType": ec2.SubnetType.PUBLIC,
                },
                {
                    "cidrMask": 24,
                    "name": f"{resource_name}-private",
                    "subnetType": ec2.SubnetType.PRIVATE_WITH_EGRESS,
                }
            ]
        )

        # Create ECS Cluster
        ecs_cluster = ecs.Cluster(
            self,
            "EcsCluster",
            cluster_name=f"{resource_name}-cluster",
            vpc=vpc)

        # Create CloudWatch Log Group
        ecs_log_group = logs.LogGroup(
            self,
            "EcsLogGroup",
            log_group_name=f"/aws/ecs/{resource_name}",
            removal_policy=RemovalPolicy.DESTROY)

        # Create ALB and ECS Fargate Service
        ecs_service = ecs_patterns.ApplicationLoadBalancedFargateService(
            self,
            "EcsFargateService",
            load_balancer_name=f"{resource_name}-lb",
            public_load_balancer=True,
            cluster=ecs_cluster,
            cpu=1024,
            desired_count=1,
            memory_limit_mib=2048,
            assign_public_ip=False,
            task_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS),
            task_image_options={
                "family": f"{resource_name}-taskdef",
                "container_name": f"{resource_name}-container",
                "image": ecs.ContainerImage.from_ecr_repository(ecr_repository, "latest"),
                "container_port": 8501,
                "log_driver": ecs.LogDriver.aws_logs(stream_prefix=f"{resource_name}-container-logs", log_group=ecs_log_group),
            }
        )

        ecs_service.task_definition.add_to_task_role_policy(
            statement=PolicyStatement(
                effect=Effect.ALLOW,
                actions=["bedrock:*"],
                resources=["*"],
            )
        )
