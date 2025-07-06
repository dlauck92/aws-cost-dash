import os
from dotenv import load_dotenv
import boto3
from datetime import datetime, timedelta
import calendar

# Load environment variables from .env file
load_dotenv(override=True)

# AWS region configuration
aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")

def get_aws_client():
    """
    Create AWS Cost Explorer client using environment variables from .env file
    """
    try:
        # Create client using credentials from .env environment variables
        client = boto3.client('ce', region_name=aws_region)
        
        # Test credentials with a simple call
        client.list_cost_category_definitions(MaxResults=1)
        
        print("✓ Using credentials from .env file")
        return client
        
    except Exception as e:
        print(f"❌ Error setting up AWS client: {e}")
        print("\n🔍 Troubleshooting steps:")
        print("1. Check your .env file has the correct credentials")
        print("2. Verify AWS_ACCESS_KEY_ID starts with 'AKIA'")
        print("3. Make sure there are no extra spaces or quotes in .env")
        print("4. Confirm Cost Explorer is enabled in your AWS account")
        print("5. Check your IAM user has Cost Explorer permissions")
        exit(1)

# Create the AWS client
client = get_aws_client()

# Date calculations
today = datetime.today().date()
current_month_start = today.replace(day=1)
last_month_end = current_month_start - timedelta(days=1)
last_month_start = last_month_end.replace(day=1)

# Last 30 days
end_date = today
start_date = end_date - timedelta(days=30)

print("🔍 AWS Cost Analysis\n")

# 1. Last 30 days daily costs
print(f"📅 Daily Costs (Last 30 Days: {start_date} to {end_date}):")
print("-" * 50)

response = client.get_cost_and_usage(
    TimePeriod={'Start': start_date.strftime('%Y-%m-%d'), 'End': end_date.strftime('%Y-%m-%d')},
    Granularity='DAILY',
    Metrics=['UnblendedCost']
)

total_30_days = 0
for result in response['ResultsByTime']:
    date = result['TimePeriod']['Start']
    amount = float(result['Total']['UnblendedCost']['Amount'])
    total_30_days += amount
    print(f"{date}: ${amount:.2f}")

print(f"\n💰 Total (Last 30 Days): ${total_30_days:.2f}")
print(f"📊 Average per day: ${total_30_days/30:.2f}")

# 2. Previous month total
print(f"\n📆 Previous Month ({last_month_start.strftime('%B %Y')}):")
print("-" * 50)

prev_month_response = client.get_cost_and_usage(
    TimePeriod={
        'Start': last_month_start.strftime('%Y-%m-%d'), 
        'End': current_month_start.strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY',
    Metrics=['UnblendedCost']
)

prev_month_cost = float(prev_month_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
print(f"💰 Total: ${prev_month_cost:.2f}")

# 3. Current month so far and projection
print(f"\n📈 Current Month ({current_month_start.strftime('%B %Y')}):")
print("-" * 50)

current_month_response = client.get_cost_and_usage(
    TimePeriod={
        'Start': current_month_start.strftime('%Y-%m-%d'), 
        'End': today.strftime('%Y-%m-%d')
    },
    Granularity='MONTHLY',
    Metrics=['UnblendedCost']
)

current_month_cost = float(current_month_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])

# Calculate days in current month
days_in_month = calendar.monthrange(today.year, today.month)[1]
days_elapsed = today.day
daily_avg = current_month_cost / days_elapsed if days_elapsed > 0 else 0
estimated_month_cost = daily_avg * days_in_month

print(f"💰 Current month to date: ${current_month_cost:.2f}")
print(f"📊 Days elapsed: {days_elapsed} of {days_in_month}")
print(f"📈 Estimated monthly total: ${estimated_month_cost:.2f}")

# Comparison
print(f"\n📊 Month-over-Month Comparison:")
print("-" * 50)
if prev_month_cost > 0:
    change = ((estimated_month_cost - prev_month_cost) / prev_month_cost) * 100
    trend = "📈" if change > 0 else "📉" if change < 0 else "➡️"
    print(f"{trend} Estimated change: {change:+.1f}% vs last month")
else:
    print("📊 No previous month data for comparison")
