# AWS Cost Dashboard

This is a comprehensive AWS cost analysis tool that provides both a Python CLI interface and an interactive web dashboard using Streamlit. It connects to AWS Cost Explorer API to display daily spending, monthly comparisons, service breakdowns, and cost projections.

## 📸 Dashboard Preview

![AWS Cost Dashboard](images/dashboard-screenshot.png)

*Interactive web dashboard showing daily costs, monthly comparisons, and service breakdowns*

## Features

### 📊 **Interactive Web Dashboard** (Streamlit)
- **Real-time cost metrics** with key performance indicators
- **Interactive charts** showing daily cost trends and monthly comparisons
- **Service breakdown** with pie chart and detailed cost analysis
- **Monthly projections** based on current spending patterns
- **CSV export functionality** for all data sets
- **Auto-refresh** every 5 minutes with manual refresh option
- **Responsive design** that works on desktop and mobile

### 💻 **Command Line Interface**
- Daily cost analysis for the last 30 days
- Previous month vs current month comparison
- Current month cost projections
- Service-by-service cost breakdown

### 🔒 **Security**
- Uses environment variables for AWS credentials
- Secure credential management with `.env` files
- No hardcoded secrets in the codebase

## Setup

### Prerequisites
1. Ensure Cost Explorer is enabled in your AWS account
2. Create an IAM user with Cost Explorer permissions (or use your existing credentials)

### Environment Variables Setup
1. Create a `.env` file in the project root
2. Add your credentials to `.env`:
```
AWS_ACCESS_KEY_ID=your_access_key_here
AWS_SECRET_ACCESS_KEY=your_secret_key_here
AWS_DEFAULT_REGION=us-east-1
```

### Install Dependencies
```bash
pip install -r requirements.txt
```

## Usage

### 🌐 **Streamlit Web Dashboard** (Recommended)
```bash
streamlit run streamlit_app.py
```
This will open your browser to `http://localhost:8501` with the interactive dashboard.

### 💻 **Command Line Interface**
```bash
python main.py
```

## 📥 **Data Export**

The Streamlit dashboard provides three CSV export options:

1. **Daily Costs CSV** - Individual daily cost data for the last 30 days
2. **Service Breakdown CSV** - Cost analysis by AWS service with percentages
3. **Summary Report CSV** - Key metrics and projections in a comprehensive report

## Dashboard Features

### 📈 **Key Metrics**
- Last 30 days total spending
- Previous month actual costs
- Current month estimated costs
- Month-to-date progress tracking

### 📊 **Visualizations**
- **Daily Cost Trend Chart** - Line chart showing spending patterns
- **Monthly Comparison Chart** - Bar chart comparing month-over-month costs
- **Service Breakdown Chart** - Pie chart showing cost distribution by AWS service

### 🔄 **Data Management**
- Automatic data caching (5-minute intervals)
- Manual refresh capability
- Real-time timestamp showing last update
- Error handling with helpful troubleshooting steps

## File Structure

```
aws-cost-dash/
├── main.py              # Command line interface
├── streamlit_app.py     # Interactive web dashboard
├── requirements.txt     # Python dependencies
├── .env                 # AWS credentials (create this)
├── .gitignore          # Version control exclusions
├── images/             # Screenshots and assets
│   └── dashboard-screenshot.png
└── README.md           # This file
```

## AWS Permissions Required

Your IAM user needs the following permissions:
- `ce:GetCostAndUsage`
- `ce:ListCostCategoryDefinitions`
- `ce:GetDimensionValues`

Or attach the AWS managed policy: `Billing`

## Troubleshooting

### Common Issues:
1. **Invalid credentials** - Check your `.env` file format (no quotes needed)
2. **Cost Explorer not enabled** - Enable it in your AWS Billing console
3. **Permission denied** - Ensure your IAM user has Cost Explorer permissions
4. **No data showing** - Verify you have actual AWS usage/costs in your account

### Getting Help:
- Check the troubleshooting steps in the dashboard
- Verify your AWS credentials are correct
- Ensure Cost Explorer is enabled in your AWS account
- Make sure you have actual AWS usage to analyze

## Technologies Used

- **Python 3.7+**
- **Streamlit** - Web dashboard framework
- **boto3** - AWS SDK for Python
- **pandas** - Data manipulation and analysis
- **plotly** - Interactive charts and visualizations
- **python-dotenv** - Environment variable management

## License

This project is open source and available under the MIT License.
