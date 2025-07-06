import streamlit as st
import os
from dotenv import load_dotenv
import boto3
from datetime import datetime, timedelta
import calendar
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Load environment variables from .env file
load_dotenv(override=True)

# Page configuration
st.set_page_config(
    page_title="AWS Cost Dashboard",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #ff6b6b;
    }
    .stMetric > div > div > div > div {
        font-size: 2rem;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_resource
def get_aws_client():
    """
    Create AWS Cost Explorer client using environment variables from .env file
    """
    aws_region = os.getenv("AWS_DEFAULT_REGION", "us-east-1")
    
    try:
        # Create client using credentials from .env environment variables
        client = boto3.client('ce', region_name=aws_region)
        
        # Test credentials with a simple call
        client.list_cost_category_definitions(MaxResults=1)
        
        return client, None
        
    except Exception as e:
        error_msg = f"❌ Error setting up AWS client: {e}"
        return None, error_msg

@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_cost_data():
    """Fetch all cost data from AWS"""
    client, error = get_aws_client()
    if error:
        return None, error
    
    try:
        # Date calculations
        today = datetime.today().date()
        current_month_start = today.replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        last_month_start = last_month_end.replace(day=1)
        
        # Last 30 days
        end_date = today
        start_date = end_date - timedelta(days=30)
        
        # 1. Get daily costs for last 30 days
        daily_response = client.get_cost_and_usage(
            TimePeriod={'Start': start_date.strftime('%Y-%m-%d'), 'End': end_date.strftime('%Y-%m-%d')},
            Granularity='DAILY',
            Metrics=['UnblendedCost']
        )
        
        # 2. Get previous month total
        prev_month_response = client.get_cost_and_usage(
            TimePeriod={
                'Start': last_month_start.strftime('%Y-%m-%d'), 
                'End': current_month_start.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        # 3. Get current month so far
        current_month_response = client.get_cost_and_usage(
            TimePeriod={
                'Start': current_month_start.strftime('%Y-%m-%d'), 
                'End': today.strftime('%Y-%m-%d')
            },
            Granularity='MONTHLY',
            Metrics=['UnblendedCost']
        )
        
        # 4. Get cost breakdown by service (last 30 days)
        service_response = client.get_cost_and_usage(
            TimePeriod={'Start': start_date.strftime('%Y-%m-%d'), 'End': end_date.strftime('%Y-%m-%d')},
            Granularity='MONTHLY',
            Metrics=['UnblendedCost'],
            GroupBy=[
                {
                    'Type': 'DIMENSION',
                    'Key': 'SERVICE'
                }
            ]
        )
        
        # Process data
        daily_data = []
        total_30_days = 0
        for result in daily_response['ResultsByTime']:
            date = result['TimePeriod']['Start']
            amount = float(result['Total']['UnblendedCost']['Amount'])
            total_30_days += amount
            daily_data.append({'date': date, 'cost': amount})
        
        prev_month_cost = float(prev_month_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
        current_month_cost = float(current_month_response['ResultsByTime'][0]['Total']['UnblendedCost']['Amount'])
        
        # Process service breakdown data
        service_data = []
        if service_response['ResultsByTime']:
            for group in service_response['ResultsByTime'][0]['Groups']:
                service_name = group['Keys'][0]
                service_cost = float(group['Metrics']['UnblendedCost']['Amount'])
                if service_cost > 0:  # Only include services with actual costs
                    service_data.append({
                        'service': service_name,
                        'cost': service_cost
                    })
        
        # Sort services by cost (highest first)
        service_data = sorted(service_data, key=lambda x: x['cost'], reverse=True)
        
        # Calculate projections
        days_in_month = calendar.monthrange(today.year, today.month)[1]
        days_elapsed = today.day
        daily_avg = current_month_cost / days_elapsed if days_elapsed > 0 else 0
        estimated_month_cost = daily_avg * days_in_month
        
        return {
            'daily_data': daily_data,
            'service_data': service_data,
            'total_30_days': total_30_days,
            'prev_month_cost': prev_month_cost,
            'current_month_cost': current_month_cost,
            'estimated_month_cost': estimated_month_cost,
            'days_elapsed': days_elapsed,
            'days_in_month': days_in_month,
            'daily_avg': daily_avg,
            'last_month_start': last_month_start,
            'current_month_start': current_month_start,
            'start_date': start_date,
            'end_date': end_date
        }, None
        
    except Exception as e:
        return None, f"Error fetching cost data: {e}"

def main():
    # Header
    st.title("💰 AWS Cost Dashboard")
    st.markdown("**Real-time AWS cost analysis and projections**")
    
    # Fetch data
    with st.spinner("Fetching AWS cost data..."):
        data, error = fetch_cost_data()
    
    if error:
        st.error(error)
        st.info("**Troubleshooting steps:**")
        st.write("""
        1. Check your .env file has the correct credentials
        2. Verify AWS_ACCESS_KEY_ID starts with 'AKIA'
        3. Make sure there are no extra spaces or quotes in .env
        4. Confirm Cost Explorer is enabled in your AWS account
        5. Check your IAM user has Cost Explorer permissions
        """)
        return
    
    # Success message
    st.success("✓ Connected to AWS Cost Explorer")
    
    # Key Metrics Row
    st.subheader("📊 Key Metrics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Last 30 Days Total",
            value=f"${data['total_30_days']:.2f}",
            delta=f"${data['total_30_days']/30:.2f}/day avg"
        )
    
    with col2:
        st.metric(
            label=f"Previous Month ({data['last_month_start'].strftime('%b %Y')})",
            value=f"${data['prev_month_cost']:.2f}"
        )
    
    with col3:
        change = ((data['estimated_month_cost'] - data['prev_month_cost']) / data['prev_month_cost'] * 100) if data['prev_month_cost'] > 0 else 0
        st.metric(
            label=f"Current Month Estimate ({data['current_month_start'].strftime('%b %Y')})",
            value=f"${data['estimated_month_cost']:.2f}",
            delta=f"{change:+.1f}% vs last month"
        )
    
    with col4:
        st.metric(
            label="Month To Date",
            value=f"${data['current_month_cost']:.2f}",
            delta=f"{data['days_elapsed']}/{data['days_in_month']} days"
        )
    
    st.divider()
    
    # Charts Row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Daily Cost Trend (Last 30 Days)")
        
        # Create daily cost chart
        df_daily = pd.DataFrame(data['daily_data'])
        df_daily['date'] = pd.to_datetime(df_daily['date'])
        
        fig_daily = px.line(
            df_daily, 
            x='date', 
            y='cost',
            title=f"Daily AWS Costs ({data['start_date']} to {data['end_date']})",
            labels={'cost': 'Cost ($)', 'date': 'Date'}
        )
        fig_daily.update_traces(line_color='#ff6b6b', line_width=3)
        fig_daily.update_layout(
            xaxis_title="Date",
            yaxis_title="Cost ($)",
            hovermode='x unified'
        )
        st.plotly_chart(fig_daily, use_container_width=True)
    
    with col2:
        st.subheader("📊 Monthly Comparison")
        
        # Create monthly comparison chart
        months = [
            data['last_month_start'].strftime('%b %Y'),
            data['current_month_start'].strftime('%b %Y') + ' (Est.)'
        ]
        costs = [data['prev_month_cost'], data['estimated_month_cost']]
        colors = ['#36a2eb', '#ff6b6b']
        
        fig_monthly = go.Figure(data=[
            go.Bar(
                x=months,
                y=costs,
                marker_color=colors,
                text=[f'${cost:.2f}' for cost in costs],
                textposition='auto',
            )
        ])
        fig_monthly.update_layout(
            title="Monthly Cost Comparison",
            xaxis_title="Month",
            yaxis_title="Cost ($)",
            showlegend=False
        )
        st.plotly_chart(fig_monthly, use_container_width=True)
    
    # Service Breakdown Chart (full width)
    st.subheader("🔧 Cost by AWS Service (Last 30 Days)")
    
    if data['service_data']:
        # Create two columns for service breakdown
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Pie chart for service breakdown
            df_services = pd.DataFrame(data['service_data'])
            
            # Limit to top 10 services for readability
            top_services = df_services.head(10)
            
            fig_pie = px.pie(
                top_services,
                values='cost',
                names='service',
                title=f"Service Distribution (Top {len(top_services)} Services)",
                color_discrete_sequence=px.colors.qualitative.Set3
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            fig_pie.update_layout(showlegend=True, legend=dict(orientation="v"))
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Service cost table
            st.markdown("**💰 Service Costs**")
            df_services_display = pd.DataFrame(data['service_data'])
            df_services_display['cost'] = df_services_display['cost'].apply(lambda x: f"${x:.2f}")
            df_services_display['percentage'] = [f"{(cost/data['total_30_days']*100):.1f}%" for cost in [s['cost'] for s in data['service_data']]]
            df_services_display.columns = ['Service', 'Cost', '%']
            
            st.dataframe(
                df_services_display,
                use_container_width=True,
                hide_index=True,
                height=400
            )
    else:
        st.info("No service breakdown data available for the selected period.")
    
    st.divider()
    
    # Detailed Data Table
    st.subheader("📋 Detailed Daily Costs")
    
    # Format data for table
    df_table = pd.DataFrame(data['daily_data'])
    df_table['date'] = pd.to_datetime(df_table['date']).dt.strftime('%Y-%m-%d')
    df_table['cost'] = df_table['cost'].apply(lambda x: f"${x:.2f}")
    df_table.columns = ['Date', 'Cost']
    
    # Add export buttons above the table
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        # Export daily costs to CSV
        daily_csv = pd.DataFrame(data['daily_data'])
        daily_csv['date'] = pd.to_datetime(daily_csv['date']).dt.strftime('%Y-%m-%d')
        daily_csv.columns = ['Date', 'Cost']
        
        st.download_button(
            label="📥 Download Daily Costs CSV",
            data=daily_csv.to_csv(index=False),
            file_name=f"aws_daily_costs_{data['start_date']}_{data['end_date']}.csv",
            mime="text/csv"
        )
    
    with col2:
        # Export service breakdown to CSV
        if data['service_data']:
            service_csv = pd.DataFrame(data['service_data'])
            service_csv['percentage'] = [f"{(cost/data['total_30_days']*100):.1f}%" for cost in service_csv['cost']]
            service_csv.columns = ['Service', 'Cost', 'Percentage']
            
            st.download_button(
                label="📥 Download Service Breakdown CSV",
                data=service_csv.to_csv(index=False),
                file_name=f"aws_service_costs_{data['start_date']}_{data['end_date']}.csv",
                mime="text/csv"
            )
    
    with col3:
        # Export summary report to CSV
        summary_data = {
            'Metric': [
                'Last 30 Days Total',
                f'Previous Month ({data["last_month_start"].strftime("%b %Y")})',
                f'Current Month To Date ({data["current_month_start"].strftime("%b %Y")})',
                f'Current Month Estimate ({data["current_month_start"].strftime("%b %Y")})',
                'Daily Average (Last 30 Days)',
                'Daily Average (Current Month)',
                'Days Elapsed This Month',
                'Days in Current Month'
            ],
            'Value': [
                f"${data['total_30_days']:.2f}",
                f"${data['prev_month_cost']:.2f}",
                f"${data['current_month_cost']:.2f}",
                f"${data['estimated_month_cost']:.2f}",
                f"${data['total_30_days']/30:.2f}",
                f"${data['daily_avg']:.2f}",
                data['days_elapsed'],
                data['days_in_month']
            ]
        }
        summary_csv = pd.DataFrame(summary_data)
        
        st.download_button(
            label="📥 Download Summary Report CSV",
            data=summary_csv.to_csv(index=False),
            file_name=f"aws_cost_summary_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )
    
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True
    )
    
    # Sidebar with additional info
    with st.sidebar:
        st.header("ℹ️ Information")
        
        # Format current time in a more readable way
        now = datetime.now()
        formatted_time = now.strftime('%B %d, %Y at %I:%M %p')
        
        st.info(f"""
        **Data Source:** AWS Cost Explorer
        
        **Last Updated:** {formatted_time}
        
        **Region:** {os.getenv('AWS_DEFAULT_REGION', 'us-east-1')}
        """)
        
        if st.button("🔄 Refresh Data"):
            st.cache_data.clear()
            st.rerun()
        
        st.markdown("---")
        st.markdown("**💡 Tips:**")
        st.markdown("""
        - Data refreshes every 5 minutes automatically
        - Current month estimate based on daily average
        - Click 'Refresh Data' for immediate update
        - Use download buttons to export data as CSV files
        """)

        st.markdown("---")
        st.markdown("**📥 Available Exports:**")
        st.markdown("""
        - **Daily Costs**: Individual daily cost data
        - **Service Breakdown**: Cost by AWS service
        - **Summary Report**: Key metrics and projections
        """)

if __name__ == "__main__":
    main()
