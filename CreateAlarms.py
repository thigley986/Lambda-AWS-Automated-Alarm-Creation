#Describe EC2 instances, EBS volumes, and RDS instances

import boto3
import collections

ec = boto3.client('ec2')
rd = boto3.client('rds')
cw = boto3.client('cloudwatch')

def lambda_handler(event, context):
    reservations = ec.describe_instances().get('Reservations', [])
    instances = sum(
        [
            [i for i in r['Instances']]
            for r in reservations
        ], [])
    
    for instance in instances:
        for tag in instance['Tags']:
            if tag['Key'] == 'Name':
                name_tag = tag['Value']
                print "Found instance %s with name %s" % (instance['InstanceId'], name_tag)
        
        #Create Metric "CPU Utilization Greater than 95% for 15+ Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s %s High CPU Utilization Warning" % (name_tag, instance['InstanceId']),
            AlarmDescription='CPU Utilization Greater than 95% for 15+ Minutes',
            ActionsEnabled=True,
            AlarmActions=[
                'arn:aws:sns:us-east-1:659177528321:NotifyMe',
            ],
            MetricName='CPUUtilization',
            Namespace='AWS/EC2',
            Statistic='Average',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance['InstanceId']
                },
            ],
            Period=300,
            EvaluationPeriods=1,
            Threshold=95.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )
        
    for instance in instances:
        for dev in instance['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            vol_id = dev['Ebs']['VolumeId']
            print "Found EBS volume %s on instance %s" % (
                vol_id, instance['InstanceId'])
        
    database_instances = rd.describe_db_instances().get('DBInstances', [])
    for database in database_instances:
            print "Found RDS database %s" % (
                 database['DBInstanceIdentifier'])
        
    metricalarms = cw.describe_alarms().get('MetricAlarms', [])
    for alarm in metricalarms:
            print "Found CloudWatch alarm %s" % (
                 alarm['AlarmName'])
