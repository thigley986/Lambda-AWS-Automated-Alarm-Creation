from __future__ import print_function
import boto3
import logging

# SNS Topic Definition for EC2, EBS
ec2_sns = 'arn:aws:sns:eu-west-1:503375299761:testinspector'
ebs_sns = 'arn:aws:sns:eu-west-1:503375299761:testinspector'

# AWS Account and Region Definition for Reboot Actions
akid = '503375299761'
region = 'eu-west-1'

# Create AWS clients
ec = boto3.client('ec2')
cw = boto3.client('cloudwatch')

LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

def get_instance_id(event):
    """Parses InstanceID from the event dict and gets the FQDN from EC2 API"""
    try:
        return event['detail']['instance-id']
    except KeyError as err:
        LOGGER.error(err)
        return False

def lambda_handler(event, context):
    instanceid = get_instance_id(event)
    name_tag = 'lambdagenerated'

    # Create Metric "CPU Utilization Greater than 95% for 15+ Minutes"

    cw.put_metric_alarm(
    AlarmName="%s %s High CPU Utilization Warning" % (name_tag, instanceid),
    AlarmDescription='CPU Utilization Greater than 95% for 15+ Minutes',
    ActionsEnabled=True,
    AlarmActions=[
        ec2_sns,
    ],
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': instanceid,
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
        ec2_sns,
    ],
    MetricName='CPUUtilization',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': instanceid,
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
        "arn:aws:automate:%s:ec2:recover" % region,
    ],
    MetricName='StatusCheckFailed_System',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': instanceid,
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
        ec2_sns,
        "arn:aws:swf:%s:%s:action/actions/AWS_EC2.instance['instanceid'].Reboot/1.0" % (region, akid)
    ],
    MetricName='StatusCheckFailed_Instance',
    Namespace='AWS/EC2',
    Statistic='Average',
    Dimensions=[
        {
            'Name': instanceid,
            'Value': instanceid
        },
    ],
    Period=60,
    EvaluationPeriods=20,
    Threshold=1.0,
    ComparisonOperator='GreaterThanOrEqualToThreshold'
)

