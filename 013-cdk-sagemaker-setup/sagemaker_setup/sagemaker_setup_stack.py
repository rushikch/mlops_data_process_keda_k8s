from constructs import Construct
from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_ec2 as ec2,
    aws_sagemaker as sagemaker
)


class SagemakerSetupStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, app_prefix: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # VPC and Networking setup 
        self.__setup_networking(app_prefix)

        # IAM Permissions setup for SageMaker
        self.__setup_iam_roles(app_prefix)

        # Create SageMaker Domain and User Profile
        self.__setup_sagemaker_domain_and_user(app_prefix)

    def __setup_networking(self, app_prefix: str) -> None:
        """
        Setup VPC and Networking components for SageMaker environment.
        """

        # Create VPC
        self.vpc = ec2.Vpc(
            self,
            "VPC",
            vpc_name=f"{app_prefix}-vpc",
            ip_addresses=ec2.IpAddresses.cidr("10.10.0.0/16"),
            enable_dns_hostnames=True,
            enable_dns_support=True,
            # Create VPC without subnets
            subnet_configuration=[]
        )
        
        # Get availability zones (first 2)
        azs = self.availability_zones[:2]
        
        # Create Internet Gateway
        self.igw = ec2.CfnInternetGateway(
            self,
            "InternetGateway",
            tags=[{"key": "Name", "value": f"{app_prefix}-igw"}]
        )
        
        # Attach Internet Gateway to VPC
        ec2.CfnVPCGatewayAttachment(
            self,
            "IGWAttachment",
            vpc_id=self.vpc.vpc_id,
            internet_gateway_id=self.igw.ref  # Fixed: Use .ref instead of .attr_internet_gateway_id
        )

        # Create Public Subnets
        self.public_subnets = []
        for i, az in enumerate(azs):
            subnet = ec2.CfnSubnet(
                self,
                f"PublicSubnet{i+1}",
                availability_zone=az,
                cidr_block=f"10.10.{i}.0/24",
                vpc_id=self.vpc.vpc_id,
                map_public_ip_on_launch=True,
                tags=[{"key": "Name", "value": f"{app_prefix}-public-subnet-{i+1}"}]
            )
            self.public_subnets.append(subnet)
        
        # Create Private Subnets
        self.private_subnets = []
        for i, az in enumerate(azs):
            subnet = ec2.CfnSubnet(
                self,
                f"PrivateSubnet{i+1}",
                availability_zone=az,
                cidr_block=f"10.10.{i+10}.0/24",  # 10.10.10.0/24, 10.10.11.0/24
                vpc_id=self.vpc.vpc_id,
                map_public_ip_on_launch=False,
                tags=[{"key": "Name", "value": f"{app_prefix}-private-subnet-{i+1}"}]
            )
            self.private_subnets.append(subnet)
        
        # Create EIP for NAT Gateway first
        # self.nat_eip = ec2.CfnEIP(
        #     self,
        #     "NATGatewayEIP",
        #     domain="vpc",
        #     tags=[{"key": "Name", "value": f"{app_prefix}-nat-eip"}]
        # )
        
        # Create NAT Gateway (in first public subnet)
        # self.nat_gateway = ec2.CfnNatGateway(
        #     self,
        #     "NATGateway",
        #     subnet_id=self.public_subnets[0].ref,  # Fixed: Use .ref instead of .attr_subnet_id
        #     allocation_id=self.nat_eip.attr_allocation_id,
        #     tags=[{"key": "Name", "value": f"{app_prefix}-nat-gateway"}]
        # )
        
        # Create Route Tables
        # Public Route Table
        self.public_route_table = ec2.CfnRouteTable(
            self,
            "PublicRouteTable",
            vpc_id=self.vpc.vpc_id,
            tags=[{"key": "Name", "value": f"{app_prefix}-public-rt"}]
        )
        
        # Add route to Internet Gateway
        ec2.CfnRoute(
            self,
            "PublicRoute",
            route_table_id=self.public_route_table.ref,  # Fixed: Use .ref instead of .attr_route_table_id
            destination_cidr_block="0.0.0.0/0",
            gateway_id=self.igw.ref  # Fixed: Use .ref instead of .attr_internet_gateway_id
        )
        
        # Associate public subnets with public route table
        for i, subnet in enumerate(self.public_subnets):
            ec2.CfnSubnetRouteTableAssociation(
                self,
                f"PublicSubnetRTAssoc{i+1}",
                subnet_id=subnet.ref,  # Fixed: Use .ref instead of .attr_subnet_id
                route_table_id=self.public_route_table.ref  # Fixed: Use .ref instead of .attr_route_table_id
            )
        
        # Private Route Table
        self.private_route_table = ec2.CfnRouteTable(
            self,
            "PrivateRouteTable",
            vpc_id=self.vpc.vpc_id,
            tags=[{"key": "Name", "value": f"{app_prefix}-private-rt"}]
        )
        
        # Add route to NAT Gateway
        # ec2.CfnRoute(
        #     self,
        #     "PrivateRoute",
        #     route_table_id=self.private_route_table.ref,  # Fixed: Use .ref instead of .attr_route_table_id
        #     destination_cidr_block="0.0.0.0/0",
        #     nat_gateway_id=self.nat_gateway.ref  # Fixed: Use .ref instead of .attr_nat_gateway_id
        # )
        
        # Associate private subnets with private route table
        for i, subnet in enumerate(self.private_subnets):
            ec2.CfnSubnetRouteTableAssociation(
                self,
                f"PrivateSubnetRTAssoc{i+1}",
                subnet_id=subnet.ref,  # Fixed: Use .ref instead of .attr_subnet_id
                route_table_id=self.private_route_table.ref  # Fixed: Use .ref instead of .attr_route_table_id
            )
        
    def __setup_iam_roles(self, app_prefix: str) -> None:
    
        """
        Setup IAM Roles and Policies for SageMaker environment.
        """

        # Create IAM Role for SageMaker Domain
        self.sagemaker_domain_role = iam.Role(
            self,
            "SageMakerDomainRole",
            role_name=f"{app_prefix}-sagemaker-domain-role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
            ]
        )

        # Create IAM Role for SageMaker Studio User Profile
        self.sagemaker_studio_user_role = iam.Role(
            self,
            "SageMakerStudioUserRole",
            role_name=f"{app_prefix}-sagemaker-studio-user-role",
            assumed_by=iam.ServicePrincipal("sagemaker.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSageMakerFullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("CloudWatchLogsFullAccess")
            ]
        )
    
    def __setup_sagemaker_domain_and_user(self, app_prefix: str) -> None:
        """
        Setup SageMaker Domain and User Profile.
        """

        # Create Security Group for SageMaker Domain
        self.sagemaker_sg = ec2.SecurityGroup(
            self,
            "SageMakerSecurityGroup",
            vpc=self.vpc,
            security_group_name=f"{app_prefix}-sagemaker-sg",
            description="Security group for SageMaker Domain",
            allow_all_outbound=True
        )

        # Allow inbound traffic (customize as needed) 
        # Allowing all traffic for demonstration; restrict in production
        self.sagemaker_sg.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.all_traffic(),
            description="Allow all inbound traffic"
        )
        
        # Create SageMaker Domain
        self.sagemaker_domain = sagemaker.CfnDomain(
            self,
            "SageMakerDomain",
            domain_name=f"{app_prefix}-sagemaker-domain",
            auth_mode="IAM",
            default_user_settings=sagemaker.CfnDomain.UserSettingsProperty(
                execution_role=self.sagemaker_studio_user_role.role_arn,
                security_groups=[]
            ),
            subnet_ids=[subnet.ref for subnet in self.private_subnets],
            vpc_id=self.vpc.vpc_id,
            tags=[{"key": "Name", "value": f"{app_prefix}-sagemaker-domain"}]
        )

        # Create SageMaker User Profile
        self.sagemaker_user_profile = sagemaker.CfnUserProfile(
            self,
            "SageMakerUserProfile",
            domain_id=self.sagemaker_domain.attr_domain_id,
            user_profile_name="default-user",
            user_settings=sagemaker.CfnUserProfile.UserSettingsProperty(
                execution_role=self.sagemaker_studio_user_role.role_arn
            )
        )