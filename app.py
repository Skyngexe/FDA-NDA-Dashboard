import dash
import pandas as pd
from dash import dcc, html
from dash.dependencies import Input, Output
import plotly.express as px
from pymongo.mongo_client import MongoClient
from dotenv import load_dotenv
import os
from datetime import datetime, timezone
import threading
import plotly.graph_objs as go

# Load environment variables
load_dotenv(dotenv_path="os.env")
mongo_url = os.getenv('MONGO_URI')
client = MongoClient(mongo_url)
db = client.fda
fda_nda = db.novel_drugs_approvals

# Initialize the Dash app
app = dash.Dash()

# Global variables
last_updated_time = datetime.now(timezone.utc)
monthly_approvals_count = 0
most_recent_drug_info = None

# Function to monitor database changes
def monitor_changes():
    global last_updated_time, monthly_approvals_count, most_recent_drug_info
    with fda_nda.watch() as stream:
        while True:
            change = stream.next()  # Wait for a change
            last_updated_time = datetime.now(timezone.utc)
            data = list(fda_nda.find())
            df = pd.DataFrame(data)
            df['Approval Date'] = pd.to_datetime(df['Approval Date'], format='%m/%d/%Y')

            current_month = datetime.now().month
            current_year = datetime.now().year

            # Update monthly approvals count
            monthly_approvals_count = df[
                (df['Approval Date'].dt.month == current_month) &
                (df['Approval Date'].dt.year == current_year)
            ].shape[0]

            # Get the most recent drug
            most_recent_drug_info = df.loc[df['Approval Date'].idxmax()] if not df.empty else None

# Start the change monitoring thread
change_thread = threading.Thread(target=monitor_changes, daemon=True)
change_thread.start()

# Data preprocessing
data = list(fda_nda.find())
df = pd.DataFrame(data)
df['Approval Date'] = pd.to_datetime(df['Approval Date'], format='%m/%d/%Y')
df['Year'] = df['Approval Date'].dt.year

current_month = datetime.now().month
current_year = datetime.now().year
monthly_approvals_count = df[
    (df['Approval Date'].dt.month == current_month) &
    (df['Approval Date'].dt.year == current_year)
].shape[0]

most_recent_drug_info = df.loc[df['Approval Date'].idxmax()] if not df.empty else None

# Create the yearly approvals line chart
max_approval_count = df.groupby('Year').size().reset_index(name='Approval Count')

# Layout of the app
app.layout = html.Div(style={
    'backgroundColor': '#1F2833',
    'padding': '20px',
    'textAlign': 'center',
    'fontFamily': 'Arial, sans-serif'
}, children=[
    dcc.Interval(
        id='interval-component',
        interval=600 * 1000,
        n_intervals=0
    ),
    html.H1("NDA and BLA Approvals Dashboard", style={'color': '#00FFF4', 'marginBottom': '40px'}),

    # Cards for statistics
    html.Div(style={'display': 'flex', 'justifyContent': 'center', 'marginBottom': '40px'}, children=[
        html.Div(style={
            'backgroundColor': '#0B0C10',
            'padding': '20px',
            'margin': '10px',
            'borderRadius': '10px',
            'color': 'white',
            'width': '300px',
            'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)'
        }, children=[
            html.H3("Approved Drugs This Month", style={'fontSize': '24px'}),
            html.P(id='monthly-approvals-count', style={'fontSize': '40px', 'color': '#00FFF4'})
        ]),
        html.Div(style={
            'backgroundColor': '#0B0C10',
            'padding': '20px',
            'margin': '10px',
            'borderRadius': '10px',
            'color': 'white',
            'width': '300px',
            'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)'
        }, children=[
            html.H3("Most Recently Approved Drug", style={'fontSize': '24px'}),
            html.P(id='most-recent-drug-name', style={'fontSize': '20px', 'textAlign': 'center', 'marginTop': '10px', 'color':'#ECFF00'}),
            html.P(id='most-recent-drug-company', style={'fontSize': '18px', 'color': '#00FFF4'})
        ]),
        html.Div(style={
            'backgroundColor': '#0B0C10',
            'padding': '20px',
            'margin': '10px',
            'borderRadius': '10px',
            'color': 'white',
            'width': '300px',
            'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)'
        }, children=[
            html.H3("Last Updated", style={'fontSize': '24px'}),
            html.P(id='last-updated-time', style={'fontSize': '20px', 'textAlign': 'center', 'marginTop': '10px'},
                   children=[
                       html.Span(id='last-updated-time-value',
                                 children="[Dynamic Time]",
                                 style={'padding': '20px', 'color': '#00FFF4', 'margin-top': '30px',
                                        'display': 'block'}),
                       "HKT"
                   ])
        ])
    ]),

    # Yearly approvals line chart
    dcc.Graph(id='yearly-approvals',
              style={'marginBottom': '40px', 'width': '80%', 'display': 'inline-block', 'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)', 'borderRadius': '10px'}),

    # Bar chart for top companies by selected year
    html.Div(style={'position': 'relative', 'display': 'inline-block', 'width': '80%'}, children=[
        dcc.Graph(id='top-companies-bar-chart', style={'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)', 'borderRadius': '10px'}),
        dcc.Dropdown(
            id='year-dropdown',
            options=[{'label': str(year), 'value': year} for year in sorted(df['Year'].unique())],
            value=current_year,
            clearable=False,
            style={'color': '#000000', 'position': 'absolute', 'top': '20px', 'right': '10px', 'width': '150px', 'borderRadius': '10px'}
        )
    ]),

    dcc.Graph(id='drug_portfolio_size',
              style={'marginBottom': '40px', 'width': '80%', 'display': 'inline-block', 'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)', 'borderRadius': '10px'}),
])

@app.callback(
    Output('monthly-approvals-count', 'children'),
    Output('most-recent-drug-name', 'children'),
    Output('most-recent-drug-company', 'children'),
    Output('last-updated-time-value', 'children'),
    Input('interval-component', 'n_intervals')
)
def update_statistics(n_intervals):
    drug_name = most_recent_drug_info['Drug Name'].split('N')[0] if most_recent_drug_info is not None else "N/A"
    drug_company = f"Company: {most_recent_drug_info['Company']}" if most_recent_drug_info is not None else "N/A"

    return (
        str(monthly_approvals_count),
        drug_name,
        drug_company,
        last_updated_time.strftime("%Y-%m-%d %H:%M:%S")
    )

@app.callback(
    Output('top-companies-bar-chart', 'figure'),
    [Input('year-dropdown', 'value'), Input('interval-component', 'n_intervals')]
)
def update_bar_chart(selected_year, n_intervals):
    filtered_df = df[df['Year'] == selected_year]
    top_companies = filtered_df['Company'].value_counts().nlargest(10)
    fig_bar = go.Figure(data=[
        go.Bar(x=top_companies.index,
               y=top_companies.values,
               marker_color=top_companies.values,
               text=top_companies.values,
               textposition='auto'
               )
    ])

    fig_bar.update_layout(
        title=f'Top 10 Companies in {selected_year} by Number of Approvals',
        plot_bgcolor='#0B0C10',
        paper_bgcolor='#0B0C10',
        font_color='white',
        xaxis=dict(tickangle=-90, tickfont=dict(size=12))
    )
    fig_bar.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    fig_bar.update_traces(
        hovertemplate="<br>%{x} <br>Approval Count: %{y}<extra></extra>"
    )
    return fig_bar

@app.callback(
    Output('drug_portfolio_size', 'figure'),
    Input('interval-component','n_intervals')
)
def update_drug_portfolio_size(n_intervals):
    data = list(fda_nda.find())
    df = pd.DataFrame(data)
    drug_portfolio_size = df.groupby('Company')['_id'].count().reset_index(name='portfolio_size')
    drug_portfolio_size['count'] = drug_portfolio_size.groupby('portfolio_size')['Company'].transform('count')

    fig = px.scatter(drug_portfolio_size,
                     x="portfolio_size",
                     y="count",
                     size="portfolio_size",
                     color="portfolio_size",
                     hover_name="Company",
                     log_x=True,
                     size_max=60)

    fig.update_traces(
        hovertemplate="<br>Portfolio Size: %{x}<br>Number of Companies: %{y}<br>Example Company: %{customdata[0]}",
        customdata=drug_portfolio_size['Company'].values.reshape(-1, 1)
    )

    df['Approval Date'] = pd.to_datetime(df['Approval Date'], format='%m/%d/%Y')
    df['Year'] = df['Approval Date'].dt.year
    min_year = df['Year'].min()

    fig.update_layout(
        title=f'Drug Portfolio Size Since {min_year}',
        plot_bgcolor='#0B0C10',
        paper_bgcolor='#0B0C10',
        font_color='white'
    )
    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')

    return fig

@app.callback(
    Output('yearly-approvals', 'figure'),
    Input('interval-component', 'n_intervals')
)
def update_yearly_trend(n_intervals):
    data = list(fda_nda.find())
    df = pd.DataFrame(data)
    df['Approval Date'] = pd.to_datetime(df['Approval Date'], format='%m/%d/%Y')
    df['Year'] = df['Approval Date'].dt.year

    max_approval_count = df.groupby('Year').size().reset_index(name='Approval Count')
    fig = px.line(max_approval_count,
                  x='Year',
                  y='Approval Count',
                  title='Number of FDA Approved Drugs Each Year',
                  labels={'Year': 'Year', 'Approval Count': 'Number of Approvals'},
                  text=max_approval_count['Approval Count'].values,
                  markers=True
                  )

    fig.update_layout(
        xaxis=dict(
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.2)',
            tickmode='array',
            tickvals=max_approval_count['Year'],
            tickangle=-90,
            range=[min(max_approval_count['Year']) - 1, max(max_approval_count['Year']) + 1]
        ),
        yaxis=dict(
            range=[-10, max_approval_count['Approval Count'].max() + 20],
            showgrid=True,
            gridcolor='rgba(255, 255, 255, 0.2)'
        ),
        plot_bgcolor='#0B0C10',
        paper_bgcolor='#0B0C10',
        font_color='white'
    )
    fig.update_traces(
        fill='tozeroy',
        line=dict(color='#66FCF1'),
        textposition='top center',
        hovertemplate="<br>Year: %{x}<br>Approval Count: %{y}",
        hoverlabel=dict(
            bgcolor='rgba(255, 255, 255, 0.8)',
            font=dict(color='black')
        )
    )

    fig.update_layout(paper_bgcolor='rgba(0,0,0,0)')
    return fig

if __name__ == '__main__':
    app.run_server(debug=True)