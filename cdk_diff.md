# cdk diff for new uber stack

Below is full diff output for a new uber stack creation, as of 10/5/2019

```bash
$ cdk diff
...
IAM Statement Changes
┌───┬─────────────────────────────────┬────────┬─────────────────────────────────┬─────────────────────────────────┬──────────────────────────────────┐
│   │ Resource                        │ Effect │ Action                          │ Principal                       │ Condition                        │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${LogRetentionaae0aa3c5b4d4f87b │ Allow  │ sts:AssumeRole                  │ Service:lambda.amazonaws.com    │                                  │
│   │ 02d85b201efdd8a/ServiceRole.Arn │        │                                 │                                 │                                  │
│   │ }                               │        │                                 │                                 │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${external-api.Arn}             │ Allow  │ lambda:InvokeFunction           │ Service:apigateway.amazonaws.co │ "ArnLike": {                     │
│   │                                 │        │                                 │ m                               │   "AWS:SourceArn": "arn:${AWS::P │
│   │                                 │        │                                 │                                 │ artition}:execute-api:${AWS::Reg │
│   │                                 │        │                                 │                                 │ ion}:${AWS::AccountId}:${externa │
│   │                                 │        │                                 │                                 │ lapi8DE75EF8}/${external_api/Dep │
│   │                                 │        │                                 │                                 │ loymentStage.prod}/*/{proxy+}"   │
│   │                                 │        │                                 │                                 │ }                                │
│ + │ ${external-api.Arn}             │ Allow  │ lambda:InvokeFunction           │ Service:apigateway.amazonaws.co │ "ArnLike": {                     │
│   │                                 │        │                                 │ m                               │   "AWS:SourceArn": "arn:${AWS::P │
│   │                                 │        │                                 │                                 │ artition}:execute-api:${AWS::Reg │
│   │                                 │        │                                 │                                 │ ion}:${AWS::AccountId}:${externa │
│   │                                 │        │                                 │                                 │ lapi8DE75EF8}/test-invoke-stage/ │
│   │                                 │        │                                 │                                 │ */{proxy+}"                      │
│   │                                 │        │                                 │                                 │ }                                │
│ + │ ${external-api.Arn}             │ Allow  │ lambda:InvokeFunction           │ Service:apigateway.amazonaws.co │ "ArnLike": {                     │
│   │                                 │        │                                 │ m                               │   "AWS:SourceArn": "arn:${AWS::P │
│   │                                 │        │                                 │                                 │ artition}:execute-api:${AWS::Reg │
│   │                                 │        │                                 │                                 │ ion}:${AWS::AccountId}:${externa │
│   │                                 │        │                                 │                                 │ lapi8DE75EF8}/${external_api/Dep │
│   │                                 │        │                                 │                                 │ loymentStage.prod}/*/"           │
│   │                                 │        │                                 │                                 │ }                                │
│ + │ ${external-api.Arn}             │ Allow  │ lambda:InvokeFunction           │ Service:apigateway.amazonaws.co │ "ArnLike": {                     │
│   │                                 │        │                                 │ m                               │   "AWS:SourceArn": "arn:${AWS::P │
│   │                                 │        │                                 │                                 │ artition}:execute-api:${AWS::Reg │
│   │                                 │        │                                 │                                 │ ion}:${AWS::AccountId}:${externa │
│   │                                 │        │                                 │                                 │ lapi8DE75EF8}/test-invoke-stage/ │
│   │                                 │        │                                 │                                 │ */"                              │
│   │                                 │        │                                 │                                 │ }                                │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${external_api/CloudWatchRole.A │ Allow  │ sts:AssumeRole                  │ Service:apigateway.amazonaws.co │                                  │
│   │ rn}                             │        │                                 │ m                               │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${external-api/ServiceRole.Arn} │ Allow  │ sts:AssumeRole                  │ Service:lambda.amazonaws.com    │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${job-dlq.Arn}                  │ Allow  │ sqs:GetQueueAttributes          │ AWS:${orchestrator/ServiceRole} │                                  │
│   │                                 │        │ sqs:GetQueueUrl                 │                                 │                                  │
│   │                                 │        │ sqs:SendMessage                 │                                 │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${job-queue.Arn}                │ Allow  │ sqs:GetQueueAttributes          │ AWS:${worker/ServiceRole}       │                                  │
│   │                                 │        │ sqs:GetQueueUrl                 │                                 │                                  │
│   │                                 │        │ sqs:SendMessage                 │                                 │                                  │
│ + │ ${job-queue.Arn}                │ Allow  │ sqs:ChangeMessageVisibility     │ AWS:${orchestrator/ServiceRole} │                                  │
│   │                                 │        │ sqs:DeleteMessage               │                                 │                                  │
│   │                                 │        │ sqs:GetQueueAttributes          │                                 │                                  │
│   │                                 │        │ sqs:GetQueueUrl                 │                                 │                                  │
│   │                                 │        │ sqs:ReceiveMessage              │                                 │                                  │
│ + │ ${job-queue.Arn}                │ Allow  │ sqs:GetQueueAttributes          │ AWS:${task_master/ServiceRole}  │                                  │
│   │                                 │        │ sqs:GetQueueUrl                 │                                 │                                  │
│   │                                 │        │ sqs:SendMessage                 │                                 │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${orchestrator.Arn}             │ Allow  │ lambda:InvokeFunction           │ Service:events.amazonaws.com    │ "ArnLike": {                     │
│   │                                 │        │                                 │                                 │   "AWS:SourceArn": "${orchestrat │
│   │                                 │        │                                 │                                 │ or_rule.Arn}"                    │
│   │                                 │        │                                 │                                 │ }                                │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${orchestrator/ServiceRole.Arn} │ Allow  │ sts:AssumeRole                  │ Service:lambda.amazonaws.com    │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${slack-notify.Arn}             │ Allow  │ lambda:InvokeFunction           │ Service:sns.amazonaws.com       │ "ArnLike": {                     │
│   │                                 │        │                                 │                                 │   "AWS:SourceArn": "${throttle-e │
│   │                                 │        │                                 │                                 │ vents-topic}"                    │
│   │                                 │        │                                 │                                 │ }                                │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${slack-notify/ServiceRole.Arn} │ Allow  │ sts:AssumeRole                  │ Service:lambda.amazonaws.com    │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${task_master.Arn}              │ Allow  │ lambda:InvokeFunction           │ Service:events.amazonaws.com    │ "ArnLike": {                     │
│   │                                 │        │                                 │                                 │   "AWS:SourceArn": "${orchestrat │
│   │                                 │        │                                 │                                 │ or_rule.Arn}"                    │
│   │                                 │        │                                 │                                 │ }                                │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${task_master/ServiceRole.Arn}  │ Allow  │ sts:AssumeRole                  │ Service:lambda.amazonaws.com    │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${throttle-events-topic}        │ Allow  │ sns:Publish                     │ AWS:${worker/ServiceRole}       │                                  │
│ + │ ${throttle-events-topic}        │ Allow  │ sns:Publish                     │ AWS:${orchestrator/ServiceRole} │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${worker.Arn}                   │ Allow  │ lambda:InvokeFunction           │ AWS:${orchestrator/ServiceRole} │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ ${worker/ServiceRole.Arn}       │ Allow  │ sts:AssumeRole                  │ Service:lambda.amazonaws.com    │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ *                               │ Allow  │ xray:PutTelemetryRecords        │ AWS:${external-api/ServiceRole} │                                  │
│   │                                 │        │ xray:PutTraceSegments           │                                 │                                  │
│ + │ *                               │ Allow  │ logs:DeleteRetentionPolicy      │ AWS:${LogRetentionaae0aa3c5b4d4 │                                  │
│   │                                 │        │ logs:PutRetentionPolicy         │ f87b02d85b201efdd8a/ServiceRole │                                  │
│   │                                 │        │                                 │ }                               │                                  │
│ + │ *                               │ Allow  │ xray:PutTelemetryRecords        │ AWS:${worker/ServiceRole}       │                                  │
│   │                                 │        │ xray:PutTraceSegments           │                                 │                                  │
│ + │ *                               │ Allow  │ xray:PutTelemetryRecords        │ AWS:${orchestrator/ServiceRole} │                                  │
│   │                                 │        │ xray:PutTraceSegments           │                                 │                                  │
│ + │ *                               │ Allow  │ xray:PutTelemetryRecords        │ AWS:${task_master/ServiceRole}  │                                  │
│   │                                 │        │ xray:PutTraceSegments           │                                 │                                  │
│ + │ *                               │ Allow  │ xray:PutTelemetryRecords        │ AWS:${slack-notify/ServiceRole} │                                  │
│   │                                 │        │ xray:PutTraceSegments           │                                 │                                  │
├───┼─────────────────────────────────┼────────┼─────────────────────────────────┼─────────────────────────────────┼──────────────────────────────────┤
│ + │ arn:aws:ssm:::parameter/api_poc │ Allow  │ ssm:*                           │ AWS:${slack-notify/ServiceRole} │                                  │
│   │ /notify/slack/*                 │        │                                 │                                 │                                  │
└───┴─────────────────────────────────┴────────┴─────────────────────────────────┴─────────────────────────────────┴──────────────────────────────────┘
IAM Policy Changes
┌───┬────────────────────────────────────────────────────────────────────────┬────────────────────────────────────────────────────────────────────────┐
│   │ Resource                                                               │ Managed Policy ARN                                                     │
├───┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ + │ ${LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole}            │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecu │
│   │                                                                        │ tionRole                                                               │
├───┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ + │ ${external_api/CloudWatchRole}                                         │ arn:${AWS::Partition}:iam::aws:policy/service-role/AmazonAPIGatewayPus │
│   │                                                                        │ hToCloudWatchLogs                                                      │
├───┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ + │ ${external-api/ServiceRole}                                            │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecu │
│   │                                                                        │ tionRole                                                               │
│ + │ ${external-api/ServiceRole}                                            │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaVPCAccessE │
│   │                                                                        │ xecutionRole                                                           │
├───┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ + │ ${orchestrator/ServiceRole}                                            │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecu │
│   │                                                                        │ tionRole                                                               │
│ + │ ${orchestrator/ServiceRole}                                            │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaVPCAccessE │
│   │                                                                        │ xecutionRole                                                           │
├───┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ + │ ${slack-notify/ServiceRole}                                            │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecu │
│   │                                                                        │ tionRole                                                               │
├───┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ + │ ${task_master/ServiceRole}                                             │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecu │
│   │                                                                        │ tionRole                                                               │
│ + │ ${task_master/ServiceRole}                                             │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaVPCAccessE │
│   │                                                                        │ xecutionRole                                                           │
├───┼────────────────────────────────────────────────────────────────────────┼────────────────────────────────────────────────────────────────────────┤
│ + │ ${worker/ServiceRole}                                                  │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaBasicExecu │
│   │                                                                        │ tionRole                                                               │
│ + │ ${worker/ServiceRole}                                                  │ arn:${AWS::Partition}:iam::aws:policy/service-role/AWSLambdaVPCAccessE │
│   │                                                                        │ xecutionRole                                                           │
└───┴────────────────────────────────────────────────────────────────────────┴────────────────────────────────────────────────────────────────────────┘
Security Group Changes
┌───┬─────────────────────────────────────┬─────┬──────────┬─────────────────────────────────────┐
│   │ Group                               │ Dir │ Protocol │ Peer                                │
├───┼─────────────────────────────────────┼─────┼──────────┼─────────────────────────────────────┤
│ + │ ${api_poc-vpc.DefaultSecurityGroup} │ In  │ TCP 6379 │ ${api_poc-vpc.DefaultSecurityGroup} │
└───┴─────────────────────────────────────┴─────┴──────────┴─────────────────────────────────────┘
(NOTE: There may be security-related changes not in this list. See https://github.com/aws/aws-cdk/issues/1299)

Parameters
[+] Parameter python3-lib-layer/Code/S3Bucket python3liblayerCodeS3Bucket96166927: {"Type":"String","Description":"S3 bucket for asset \"api-uberstack-dev/python3-lib-layer/Code\""}
[+] Parameter python3-lib-layer/Code/S3VersionKey python3liblayerCodeS3VersionKeyFDFB998E: {"Type":"String","Description":"S3 key for asset version \"api-uberstack-dev/python3-lib-layer/Code\""}
[+] Parameter python3-lib-layer/Code/ArtifactHash python3liblayerCodeArtifactHashC89836F6: {"Type":"String","Description":"Artifact hash for asset \"api-uberstack-dev/python3-lib-layer/Code\""}
[+] Parameter external-api/Code/S3Bucket externalapiCodeS3BucketB39A7759: {"Type":"String","Description":"S3 bucket for asset \"api-uberstack-dev/external-api/Code\""}
[+] Parameter external-api/Code/S3VersionKey externalapiCodeS3VersionKey2B2EDD6A: {"Type":"String","Description":"S3 key for asset version \"api-uberstack-dev/external-api/Code\""}
[+] Parameter external-api/Code/ArtifactHash externalapiCodeArtifactHash9B69A1A3: {"Type":"String","Description":"Artifact hash for asset \"api-uberstack-dev/external-api/Code\""}
[+] Parameter LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/Code/S3Bucket LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8aCodeS3BucketB81211B5: {"Type":"String","Description":"S3 bucket for asset \"api-uberstack-dev/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/Code\""}
[+] Parameter LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/Code/S3VersionKey LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8aCodeS3VersionKey10C1B354: {"Type":"String","Description":"S3 key for asset version \"api-uberstack-dev/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/Code\""}
[+] Parameter LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/Code/ArtifactHash LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8aCodeArtifactHash327647CC: {"Type":"String","Description":"Artifact hash for asset \"api-uberstack-dev/LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/Code\""}
[+] Parameter worker/Code/S3Bucket workerCodeS3Bucket96113DA1: {"Type":"String","Description":"S3 bucket for asset \"api-uberstack-dev/worker/Code\""}
[+] Parameter worker/Code/S3VersionKey workerCodeS3VersionKey8C190413: {"Type":"String","Description":"S3 key for asset version \"api-uberstack-dev/worker/Code\""}
[+] Parameter worker/Code/ArtifactHash workerCodeArtifactHashAC3566D0: {"Type":"String","Description":"Artifact hash for asset \"api-uberstack-dev/worker/Code\""}
[+] Parameter orchestrator/Code/S3Bucket orchestratorCodeS3Bucket1C84E80F: {"Type":"String","Description":"S3 bucket for asset \"api-uberstack-dev/orchestrator/Code\""}
[+] Parameter orchestrator/Code/S3VersionKey orchestratorCodeS3VersionKey03EB569A: {"Type":"String","Description":"S3 key for asset version \"api-uberstack-dev/orchestrator/Code\""}
[+] Parameter orchestrator/Code/ArtifactHash orchestratorCodeArtifactHash0F891747: {"Type":"String","Description":"Artifact hash for asset \"api-uberstack-dev/orchestrator/Code\""}
[+] Parameter task_master/Code/S3Bucket taskmasterCodeS3BucketF56E7DD0: {"Type":"String","Description":"S3 bucket for asset \"api-uberstack-dev/task_master/Code\""}
[+] Parameter task_master/Code/S3VersionKey taskmasterCodeS3VersionKey68A431FA: {"Type":"String","Description":"S3 key for asset version \"api-uberstack-dev/task_master/Code\""}
[+] Parameter task_master/Code/ArtifactHash taskmasterCodeArtifactHashDC69DDA5: {"Type":"String","Description":"Artifact hash for asset \"api-uberstack-dev/task_master/Code\""}
[+] Parameter slack-notify/Code/S3Bucket slacknotifyCodeS3Bucket0F8917EE: {"Type":"String","Description":"S3 bucket for asset \"api-uberstack-dev/slack-notify/Code\""}
[+] Parameter slack-notify/Code/S3VersionKey slacknotifyCodeS3VersionKeyA47D02F1: {"Type":"String","Description":"S3 key for asset version \"api-uberstack-dev/slack-notify/Code\""}
[+] Parameter slack-notify/Code/ArtifactHash slacknotifyCodeArtifactHash854D7640: {"Type":"String","Description":"Artifact hash for asset \"api-uberstack-dev/slack-notify/Code\""}

Conditions
[+] Condition CDKMetadataAvailable: {"Fn::Or":[{"Fn::Or":[{"Fn::Equals":[{"Ref":"AWS::Region"},"ap-east-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"ap-northeast-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"ap-northeast-2"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"ap-south-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"ap-southeast-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"ap-southeast-2"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"ca-central-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"cn-north-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"cn-northwest-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"eu-central-1"]}]},{"Fn::Or":[{"Fn::Equals":[{"Ref":"AWS::Region"},"eu-north-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"eu-west-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"eu-west-2"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"eu-west-3"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"me-south-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"sa-east-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"us-east-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"us-east-2"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"us-west-1"]},{"Fn::Equals":[{"Ref":"AWS::Region"},"us-west-2"]}]}]}

Resources
[+] AWS::EC2::VPC api_poc-vpc apipocvpcDC0F60F9
[+] AWS::EC2::Subnet api_poc-vpc/PublicSubnet1/Subnet apipocvpcPublicSubnet1SubnetA49F1C19
[+] AWS::EC2::RouteTable api_poc-vpc/PublicSubnet1/RouteTable apipocvpcPublicSubnet1RouteTable6E40DADA
[+] AWS::EC2::SubnetRouteTableAssociation api_poc-vpc/PublicSubnet1/RouteTableAssociation apipocvpcPublicSubnet1RouteTableAssociation32A0EB19
[+] AWS::EC2::Route api_poc-vpc/PublicSubnet1/DefaultRoute apipocvpcPublicSubnet1DefaultRoute6DB168B7
[+] AWS::EC2::EIP api_poc-vpc/PublicSubnet1/EIP apipocvpcPublicSubnet1EIP872BE500
[+] AWS::EC2::NatGateway api_poc-vpc/PublicSubnet1/NATGateway apipocvpcPublicSubnet1NATGateway8A431129
[+] AWS::EC2::Subnet api_poc-vpc/PrivateSubnet1/Subnet apipocvpcPrivateSubnet1Subnet92850674
[+] AWS::EC2::RouteTable api_poc-vpc/PrivateSubnet1/RouteTable apipocvpcPrivateSubnet1RouteTable8F10814E
[+] AWS::EC2::SubnetRouteTableAssociation api_poc-vpc/PrivateSubnet1/RouteTableAssociation apipocvpcPrivateSubnet1RouteTableAssociationB9407362
[+] AWS::EC2::Route api_poc-vpc/PrivateSubnet1/DefaultRoute apipocvpcPrivateSubnet1DefaultRoute095390F5
[+] AWS::EC2::InternetGateway api_poc-vpc/IGW apipocvpcIGW8BDEDF59
[+] AWS::EC2::VPCGatewayAttachment api_poc-vpc/VPCGW apipocvpcVPCGW387514EE
[+] AWS::EC2::SecurityGroupIngress default_sg/from apiuberstackdevdefaultsg65F5F0FA:6379-6379 defaultsgfromapiuberstackdevdefaultsg65F5F0FA63796379ECAEC424
[+] AWS::Lambda::LayerVersion python3-lib-layer python3liblayerCC17FDB8
[+] AWS::ElastiCache::SubnetGroup cache_subnet_group cachesubnetgroup
[+] AWS::ElastiCache::CacheCluster cache cache
[+] AWS::IAM::Role external-api/ServiceRole externalapiServiceRole2C83F4B0
[+] AWS::IAM::Policy external-api/ServiceRole/DefaultPolicy externalapiServiceRoleDefaultPolicyDC28D8D1
[+] AWS::Lambda::Function external-api externalapi1DAE34E8
[+] Custom::LogRetention external-api/LogRetention externalapiLogRetention6BBF0435
[+] AWS::IAM::Role LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8aServiceRole9741ECFB
[+] AWS::IAM::Policy LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a/ServiceRole/DefaultPolicy LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8aServiceRoleDefaultPolicyADDA7DEB
[+] AWS::Lambda::Function LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8a LogRetentionaae0aa3c5b4d4f87b02d85b201efdd8aFD4BFC8A
[+] AWS::ApiGateway::RestApi external_api externalapi8DE75EF8
[+] AWS::ApiGateway::Deployment external_api/Deployment externalapiDeploymentA39CBBE156847787e2936c1ed7af0bb5dac3993b
[+] AWS::ApiGateway::Stage external_api/DeploymentStage.prod externalapiDeploymentStageprod8BC609AA
[+] AWS::IAM::Role external_api/CloudWatchRole externalapiCloudWatchRoleADC1A2AF
[+] AWS::ApiGateway::Account external_api/Account externalapiAccount52922276
[+] AWS::ApiGateway::Resource external_api/Default/{proxy+} externalapiproxy58A17B72
[+] AWS::Lambda::Permission external_api/Default/{proxy+}/ANY/ApiPermission.apiuberstackdevexternalapiAE3729ED.ANY..{proxy+} externalapiproxyANYApiPermissionapiuberstackdevexternalapiAE3729EDANYproxyFDA70F1E
[+] AWS::Lambda::Permission external_api/Default/{proxy+}/ANY/ApiPermission.Test.apiuberstackdevexternalapiAE3729ED.ANY..{proxy+} externalapiproxyANYApiPermissionTestapiuberstackdevexternalapiAE3729EDANYproxy8BCB01B2
[+] AWS::ApiGateway::Method external_api/Default/{proxy+}/ANY externalapiproxyANY7D653B4B
[+] AWS::Lambda::Permission external_api/Default/ANY/ApiPermission.apiuberstackdevexternalapiAE3729ED.ANY.. externalapiANYApiPermissionapiuberstackdevexternalapiAE3729EDANYBB3DEE2E
[+] AWS::Lambda::Permission external_api/Default/ANY/ApiPermission.Test.apiuberstackdevexternalapiAE3729ED.ANY.. externalapiANYApiPermissionTestapiuberstackdevexternalapiAE3729EDANY9EEE3703
[+] AWS::ApiGateway::Method external_api/Default/ANY externalapiANY468C920E
[+] AWS::SQS::Queue job-dlq jobdlq334817DA
[+] AWS::SQS::Queue job-queue jobqueue43A2E469
[+] AWS::SNS::Topic throttle-events-topic throttleeventstopicDA8117AB
[+] AWS::SNS::Subscription throttle-events-topic/morty.frasier@gmail.com throttleeventstopicmortyfrasiergmailcomF1F48A6E
[+] AWS::IAM::Role worker/ServiceRole workerServiceRole2130CC7F
[+] AWS::IAM::Policy worker/ServiceRole/DefaultPolicy workerServiceRoleDefaultPolicyBA498553
[+] AWS::Lambda::Function worker worker28EA3E30
[+] Custom::LogRetention worker/LogRetention workerLogRetentionA17D54F2
[+] AWS::IAM::Role orchestrator/ServiceRole orchestratorServiceRole5E8D7E02
[+] AWS::IAM::Policy orchestrator/ServiceRole/DefaultPolicy orchestratorServiceRoleDefaultPolicy389C0032
[+] AWS::Lambda::Function orchestrator orchestratorDDCE86FA
[+] Custom::LogRetention orchestrator/LogRetention orchestratorLogRetentionC7AC05F5
[+] AWS::Lambda::Permission orchestrator/AllowEventRuleapiuberstackdevorchestratorrule11A65CE6 orchestratorAllowEventRuleapiuberstackdevorchestratorrule11A65CE605FB9888
[+] AWS::IAM::Role task_master/ServiceRole taskmasterServiceRole8CD2B6DE
[+] AWS::IAM::Policy task_master/ServiceRole/DefaultPolicy taskmasterServiceRoleDefaultPolicy96ADB244
[+] AWS::Lambda::Function task_master taskmasterC345736A
[+] Custom::LogRetention task_master/LogRetention taskmasterLogRetention2F2CDFC0
[+] AWS::Lambda::Permission task_master/AllowEventRuleapiuberstackdevorchestratorrule11A65CE6 taskmasterAllowEventRuleapiuberstackdevorchestratorrule11A65CE6A717D57B
[+] AWS::IAM::Role slack-notify/ServiceRole slacknotifyServiceRole33FFA2FF
[+] AWS::IAM::Policy slack-notify/ServiceRole/DefaultPolicy slacknotifyServiceRoleDefaultPolicy3BBC8B45
[+] AWS::Lambda::Function slack-notify slacknotify74B26EF7
[+] Custom::LogRetention slack-notify/LogRetention slacknotifyLogRetention9B02D939
[+] AWS::Lambda::Permission slack-notify/AllowInvoke:apiuberstackdevthrottleeventstopic9ABA3CC2 slacknotifyAllowInvokeapiuberstackdevthrottleeventstopic9ABA3CC239E150A4
[+] AWS::SNS::Subscription slack-notify/throttle-events-topic slacknotifythrottleeventstopic0987B488
[+] AWS::Events::Rule orchestrator_rule orchestratorruleC0505227

Outputs
[+] Output external_api/Endpoint externalapiEndpoint01EBBEBF: {"Value":{"Fn::Join":["",["https://",{"Ref":"externalapi8DE75EF8"},".execute-api.",{"Ref":"AWS::Region"},".",{"Ref":"AWS::URLSuffix"},"/",{"Ref":"externalapiDeploymentStageprod8BC609AA"},"/"]]}}
[+] Output Redis_Address RedisAddress: {"Value":{"Fn::Join":["",[{"Fn::GetAtt":["cache","RedisEndpoint.Address"]},":",{"Fn::GetAtt":["cache","RedisEndpoint.Port"]}]]}}
```
