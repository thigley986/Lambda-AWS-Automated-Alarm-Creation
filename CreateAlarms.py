#Create EC2 instance, EBS, and RDS alarms for all resources in a region

import boto3
import collections

#SNS Topic Definition for EC2, EBS, and RDS
ec2_sns = '<SNS_TOPIC_ARN>'
ebs_sns = '<SNS_TOPIC_ARN>'
rds_sns = '<SNS_TOPIC_ARN>'

#AWS Account and Region Definition for Reboot Actions
akid = '<ACCOUNT_ID>'
region = '<REGION_NAME>'

#Create AWS clients
ec = boto3.client('ec2')
rd = boto3.client('rds')
cw = boto3.client('cloudwatch')

def lambda_handler(event, context):
    
    #Enumerate EC2 instances
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
                ec2_sns,
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
            EvaluationPeriods=3,
            Threshold=95.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )
        
        #Create Metric "CPU Utilization Greater than 95% for 60+ Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s %s High CPU Utilization Critical" % (name_tag, instance['InstanceId']),
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
                    'Name': 'InstanceId',
                    'Value': instance['InstanceId']
                },
            ],
            Period=300,
            EvaluationPeriods=12,
            Threshold=95.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )
        
        #Create CPU Credit Alarms only on T2 instances
        if "t2" in instance['InstanceType']:
            #Create Metric "CPU Credit Balance <= 25 for 30 Minutes"
            response = cw.put_metric_alarm(
                AlarmName="%s %s Credit Balance Warning" % (name_tag, instance['InstanceId']),
                AlarmDescription='CPU Credit Balance <= 25 for 30 Minutes',
                ActionsEnabled=True,
                AlarmActions=[
                    ec2_sns,
                ],
                MetricName='CPUCreditBalance',
                Namespace='AWS/EC2',
                Statistic='Average',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance['InstanceId']
                    },
                ],
                Period=300,
                EvaluationPeriods=6,
                Threshold=25.0,
                ComparisonOperator='LessThanOrEqualToThreshold'
            )
            
            #Create Metric "CPU Credit Balance <= 5 for 10 Minutes"
            response = cw.put_metric_alarm(
                AlarmName="%s %s Credit Balance Critical" % (name_tag, instance['InstanceId']),
                AlarmDescription='CPU Credit Balance <= 5 for 10 Minutes',
                ActionsEnabled=True,
                AlarmActions=[
                    ec2_sns,
                ],
                MetricName='CPUCreditBalance',
                Namespace='AWS/EC2',
                Statistic='Average',
                Dimensions=[
                    {
                        'Name': 'InstanceId',
                        'Value': instance['InstanceId']
                    },
                ],
                Period=300,
                EvaluationPeriods=2,
                Threshold=5.0,
                ComparisonOperator='LessThanOrEqualToThreshold'
            )
        
        #Create Metric "Status Check Failed (System) for 5 Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s %s System Check Failed" % (name_tag, instance['InstanceId']),
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
                    'Name': 'InstanceId',
                    'Value': instance['InstanceId']
                },
            ],
            Period=60,
            EvaluationPeriods=5,
            Threshold=1.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )
        
        #Create Metric "Status Check Failed (Instance) for 20 Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s %s Instance Check Failed" % (name_tag, instance['InstanceId']),
            AlarmDescription='Status Check Failed (Instance) for 20 Minutes',
            ActionsEnabled=True,
            AlarmActions=[
                ec2_sns,
                "arn:aws:swf:%s:%s:action/actions/AWS_EC2.InstanceId.Reboot/1.0" % (region, akid)
            ],
            MetricName='StatusCheckFailed_Instance',
            Namespace='AWS/EC2',
            Statistic='Average',
            Dimensions=[
                {
                    'Name': 'InstanceId',
                    'Value': instance['InstanceId']
                },
            ],
            Period=60,
            EvaluationPeriods=20,
            Threshold=1.0,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )
    
    #Enumerate EBS devices attached to EC2 instances    
    for instance in instances:
        for dev in instance['BlockDeviceMappings']:
            if dev.get('Ebs', None) is None:
                continue
            vol_id = dev['Ebs']['VolumeId']
            print "Found EBS volume %s on instance %s" % (
                vol_id, instance['InstanceId'])
            
        #Create Metric "Volume Idle Time <= 30 sec (of 5 minutes) for 30 Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s %s High Volume Activity Warning" % (vol_id, instance['InstanceId']),
            AlarmDescription='Volume Idle Time <= 30 sec (of 5 minutes) for 30 Minutes',
            ActionsEnabled=True,
            AlarmActions=[
                ebs_sns,
            ],
            MetricName='VolumeIdleTime',
            Namespace='AWS/EBS',
            Statistic='Average',
            Dimensions=[
                {
                    'Name': 'VolumeId',
                    'Value': vol_id
                },
            ],
            Period=300,
            EvaluationPeriods=6,
            Threshold=30.0,
            ComparisonOperator='LessThanOrEqualToThreshold'
        )
        
        #Create Metric "Volume Idle Time <= 30 sec (of 5 minutes) for 60 Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s %s High Volume Activity Critical" % (vol_id, instance['InstanceId']),
            AlarmDescription='Volume Idle Time <= 30 sec (of 5 minutes) for 60 Minutes',
            ActionsEnabled=True,
            AlarmActions=[
                ebs_sns,
            ],
            MetricName='VolumeIdleTime',
            Namespace='AWS/EBS',
            Statistic='Average',
            Dimensions=[
                {
                    'Name': 'VolumeId',
                    'Value': vol_id
                },
            ],
            Period=300,
            EvaluationPeriods=12,
            Threshold=30.0,
            ComparisonOperator='LessThanOrEqualToThreshold'
        )
    
    #Enumerate RDS database instances    
    database_instances = rd.describe_db_instances().get('DBInstances', [])
    for database in database_instances:
        print "Found RDS database %s" % (
            database['DBInstanceIdentifier'])
        
        #Create CPU Credit Alarms only on T2 DB Instance Classes
        if "t2" in database['DBInstanceClass']:
            
            #Create Metric "CPU Credit Balance <= 25 for 30 Minutes"
            response = cw.put_metric_alarm(
                AlarmName="%s RDS Credit Balance Warning" % (database['DBInstanceIdentifier']),
                AlarmDescription='CPU Credit Balance <= 25 for 30 Minutes',
                ActionsEnabled=True,
                AlarmActions=[
                    rds_sns,
                ],
                MetricName='CPUCreditBalance',
                Namespace='AWS/RDS',
                Statistic='Average',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': database['DBInstanceIdentifier']
                    },
                ],
                Period=300,
                EvaluationPeriods=6,
                Threshold=25.0,
                ComparisonOperator='LessThanOrEqualToThreshold'
            )
            
            #Create Metric "CPU Credit Balance <= 10 for 10 Minutes"
            response = cw.put_metric_alarm(
                AlarmName="%s RDS Credit Balance Critical" % (database['DBInstanceIdentifier']),
                AlarmDescription='CPU Credit Balance <= 10 for 10 Minutes',
                ActionsEnabled=True,
                AlarmActions=[
                    rds_sns,
                ],
                MetricName='CPUCreditBalance',
                Namespace='AWS/RDS',
                Statistic='Average',
                Dimensions=[
                    {
                        'Name': 'DBInstanceIdentifier',
                        'Value': database['DBInstanceIdentifier']
                    },
                ],
                Period=300,
                EvaluationPeriods=2,
                Threshold=10.0,
                ComparisonOperator='LessThanOrEqualToThreshold'
            )
        
        #Create Metric "Read Latency >= 3ms for 15 Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s RDS Read Latency Warning" % (database['DBInstanceIdentifier']),
            AlarmDescription='Read Latency >= 3ms for 15 Minutes',
            ActionsEnabled=True,
            AlarmActions=[
                rds_sns,
            ],
            MetricName='ReadLatency',
            Namespace='AWS/RDS',
            Statistic='Average',
            Dimensions=[
                {
                    'Name': 'DBInstanceIdentifier',
                    'Value': database['DBInstanceIdentifier']
                },
            ],
            Period=300,
            EvaluationPeriods=3,
            Threshold=.003,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )
        
        #Create Metric "Read Latency >= 5ms for 15 Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s RDS Read Latency Critical" % (database['DBInstanceIdentifier']),
            AlarmDescription='Read Latency >= 5ms for 15 Minutes',
            ActionsEnabled=True,
            AlarmActions=[
                rds_sns,
            ],
            MetricName='ReadLatency',
            Namespace='AWS/RDS',
            Statistic='Average',
            Dimensions=[
                {
                    'Name': 'DBInstanceIdentifier',
                    'Value': database['DBInstanceIdentifier']
                },
            ],
            Period=300,
            EvaluationPeriods=3,
            Threshold=.005,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )        
        #Create Metric "Write Latency >= 8ms for 15 Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s RDS Write Latency Warning" % (database['DBInstanceIdentifier']),
            AlarmDescription='Write Latency >= 8ms for 15 Minutes',
            ActionsEnabled=True,
            AlarmActions=[
                rds_sns,
            ],
            MetricName='WriteLatency',
            Namespace='AWS/RDS',
            Statistic='Average',
            Dimensions=[
                {
                    'Name': 'DBInstanceIdentifier',
                    'Value': database['DBInstanceIdentifier']
                },
            ],
            Period=300,
            EvaluationPeriods=3,
            Threshold=.008,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )
        
        #Create Metric "Write Latency >= 12ms for 15 Minutes"
        response = cw.put_metric_alarm(
            AlarmName="%s RDS Write Latency Critical" % (database['DBInstanceIdentifier']),
            AlarmDescription='Write Latency >= 12ms for 15 Minutes',
            ActionsEnabled=True,
            AlarmActions=[
                rds_sns,
            ],
            MetricName='WriteLatency',
            Namespace='AWS/RDS',
            Statistic='Average',
            Dimensions=[
                {
                    'Name': 'DBInstanceIdentifier',
                    'Value': database['DBInstanceIdentifier']
                },
            ],
            Period=300,
            EvaluationPeriods=3,
            Threshold=.012,
            ComparisonOperator='GreaterThanOrEqualToThreshold'
        )
