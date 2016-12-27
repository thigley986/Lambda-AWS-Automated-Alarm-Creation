from __future__ import print_function
import boto3
import logging

# SNS Topic Definition for EC2, EBS
ec2_sns = '<SNS_TOPIC_ARN>'
ebs_sns = '<SNS_TOPIC_ARN>'

# AWS Account and Region Definition for Reboot Actions
akid = '<ACCOUNT_ID>'
region = '<REGION_NAME>'
name_tag = '<TAG_NAME>'

# Create AWS clients
ec2session = boto3.client('ec2')
cw = boto3.client('cloudwatch')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

# Retrives instance id from cloudwatch event
def get_instance_id(event):
    try:
        return event['detail']['instance-id']
    except KeyError as err:
        LOGGER.error(err)
        return False

def lambda_handler(event, context):

    session = boto3.session.Session()
    ec2session = session.client('ec2')
    instanceid = get_instance_id(event)

    # Create Metric "CPU Utilization Greater than 95% for 15+ Minutes"
    cw.put_metric_alarm(
    AlarmName="%s %s High CPU Utilization Warning" % (name_tag, instanceid),
    AlarmDescription='CPU Utilization Greater than 95% for 15+ Minutes',
    ActionsEnabled=True,
    AlarmActions=[
        ec2_sns
    ],
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': 'InstanceId',
            'Value': instanceid
        },
    ],
    Period=300,
    EvaluationPeriods=3,
    Threshold=95.0,
    ComparisonOperator='GreaterThanOrEqualToThreshold'
)

# Create Metric "CPU Utilization Greater than 95% for 60+ Minutes"
    cw.put_metric_alarm(
    AlarmName="%s %s High CPU Utilization Critical" % (name_tag, instanceid),
    AlarmDescription='CPU Utilization Greater than 95% for 60+ Minutes',
    ActionsEnabled=True,
    AlarmActions=[
        ec2_sns
    ],
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': 'InstanceId',
            'Value': instanceid
        },
    ],
    Period=300,
    EvaluationPeriods=12,
    Threshold=95.0,
    ComparisonOperator='GreaterThanOrEqualToThreshold'
)

# Create Metric "Status Check Failed (System) for 5 Minutes"
    cw.put_metric_alarm(
    AlarmName="%s %s System Check Failed" % (name_tag, instanceid),
    AlarmDescription='Status Check Failed (System) for 5 Minutes',
    ActionsEnabled=True,
    AlarmActions=[
        ec2_sns,
        "arn:aws:automate:%s:ec2:recover" % region
    ],
    MetricName='StatusCheckFailed_System',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': 'InstanceId',
            'Value': instanceid
        },
    ],
    Period=60,
    EvaluationPeriods=5,
    Threshold=1.0,
    ComparisonOperator='GreaterThanOrEqualToThreshold'
)

# Create Metric "Status Check Failed (Instance) for 20 Minutes"
    cw.put_metric_alarm(
    AlarmName="%s %s Instance Check Failed" % (name_tag, instanceid),
    AlarmDescription='Status Check Failed (Instance) for 20 Minutes',
    ActionsEnabled=True,
    AlarmActions=[
        ec2_sns
    ],
    MetricName='StatusCheckFailed_Instance',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': 'InstanceId',
            'Value': instanceid
        },
    ],
    Period=60,
    EvaluationPeriods=20,
    Threshold=1.0,
    ComparisonOperator='GreaterThanOrEqualToThreshold'
)

    # Enumerate EBS devices attached to EC2 instances
    #vol_id = ec2session.describe_volumes()
    #vol_id = ec2session.get_all_volumes(filters={'attachment.instance-id': instanceid})

    ec2d = boto3.resource('ec2', region_name= region)
    instance = ec2d.Instance(instanceid)
    vol_id = instance.volumes.all()

    for v in vol_id:

        print("Found EBS volume %s on instance %s" % (v.id, instanceid))

    # Create Metric "Volume Idle Time <= 30 sec (of 5 minutes) for 30 Minutes"

    cw.put_metric_alarm(
    AlarmName="%s %s High Volume Activity Warning" % (v.id, instanceid),
    AlarmDescription='Volume Idle Time <= 30 sec (of 5 minutes) for 30 Minutes',
    ActionsEnabled=True,
    AlarmActions=[
        ebs_sns
    ],
    MetricName='VolumeIdleTime',
    Namespace='AWS/EBS',
    Statistic='Average',
    Dimensions=[
        {
            'Name': 'VolumeId',
            'Value': v.id
        },
    ],
    Period=300,
    EvaluationPeriods=6,
    Threshold=30.0,
    ComparisonOperator='LessThanOrEqualToThreshold'
)

# Create Metric "Volume Idle Time <= 30 sec (of 5 minutes) for 60 Minutes"
    cw.put_metric_alarm(
    AlarmName="%s %s High Volume Activity Critical" % (v.id, instanceid),
    AlarmDescription='Volume Idle Time <= 30 sec (of 5 minutes) for 60 Minutes',
    ActionsEnabled=True,
    AlarmActions=[
        ebs_sns
    ],
    MetricName='VolumeIdleTime',
    Namespace='AWS/EBS',
    Statistic='Average',
    Dimensions=[
        {
            'Name': 'VolumeId',
            'Value': v.id
        },
    ],
    Period=300,
    EvaluationPeriods=12,
    Threshold=30.0,
    ComparisonOperator='LessThanOrEqualToThreshold'
)
