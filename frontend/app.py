import dash
from dash import dcc, html
import requests
import pandas as pd
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from bson import json_util
from datetime import datetime, timezone
import plotly.express as px

app = dash.Dash(__name__)
server = app.server


# Fetch full data once
def fetch_full_data():
    response = requests.get('https://fda-nda-dashboard.onrender.com/api/data')
    data = response.json()
    df = pd.DataFrame(data.get('data'))
    most_recent_drug = data.get('most_recent_drug')
    return df, most_recent_drug

# Check for updates
def check_for_updates():
    response = requests.get('https://fda-nda-dashboard.onrender.com/api/update')
    data = response.json()
    df = pd.DataFrame(data.get('data'))
    most_recent_drug = data.get('most_recent_drug')
    return df, most_recent_drug


# Initial data load
initial_data, most_recent_drug = fetch_full_data()
initial_data_json = json_util.dumps({'data': initial_data.to_dict(orient='records'), 'most_recent_drug': most_recent_drug})

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
    dcc.Store(id='stored-data', data = initial_data_json),
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
            html.H3(f"Approved Drugs This Month ({datetime.today().month} / {datetime.today().year})", style={'fontSize': '24px'}),
            html.P(id='monthly-approvals-count', style={'fontSize': '40px', 'color': '#00FFF4'}),
            html.P("Approved Drugs Last Month", style={'fontSize': '12px'}),
            html.P(id='past-month-approvals-count', style={'fontSize': '20px', 'color': '#FF5733'})
        ])

        ,
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
            html.P(id='most-recent-drug-name',
                   style={'fontSize': '20px', 'textAlign': 'center', 'marginTop': '10px', 'color': '#ECFF00'}),
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
                       "UTC"
                   ])
        ])
    ]),

    # Yearly approvals line chart
    dcc.Graph(id='yearly-approvals',
              style={'marginBottom': '40px', 'width': '80%', 'display': 'inline-block',
                     'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)', 'borderRadius': '10px'}),

    # Bar chart for top companies by selected year
    html.Div(style={'position': 'relative', 'display': 'inline-block', 'width': '80%'}, children=[
        dcc.Graph(id='top-companies-bar-chart',
                  style={'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)', 'borderRadius': '10px'}),
        dcc.Dropdown(
            id='year-dropdown',
            options=[],  # Will be populated dynamically
            value=None,
            clearable=False,
            style={'color': '#000000', 'position': 'absolute', 'top': '20px', 'right': '10px', 'width': '150px',
                   'borderRadius': '10px'}
        )
    ]),

    dcc.Graph(id='drug_portfolio_size',
              style={'marginBottom': '40px', 'width': '80%', 'display': 'inline-block',
                     'boxShadow': '0 4px 15px rgba(0, 0, 0, 0.5)', 'borderRadius': '10px'}),
])


@app.callback(
    Output('stored-data', 'data'),
    [Input('interval-component', 'n_intervals')],
    [State('stored-data', 'data')]
)
def fetch_and_store_data(n_intervals, stored_data):
    df, drug = check_for_updates()
    responses = {'data': df, 'most_recent_drug': drug}
    # Load existing data from the store
    if stored_data:
        existing_data = json_util.loads(stored_data)
    else:
        existing_data = {'data': [], 'most_recent_drug': None}

    # Append new data if it's not empty
    if not df.empty:
        existing_data['data'].extend(df)
    existing_data['most_recent_drug'] = drug

    return json_util.dumps(existing_data)


@app.callback(
    Output('monthly-approvals-count', 'children'),
    Output('past-month-approvals-count', 'children'),
    Output('most-recent-drug-name', 'children'),
    Output('most-recent-drug-company', 'children'),
    Output('last-updated-time-value', 'children'),
    Input('stored-data', 'data')
)
def update_statistics(data):
    data = json_util.loads(data)
    df = pd.DataFrame(data.get('data'))
    most_recent_drug_info = data.get('most_recent_drug')[0]

    df['Approval Date'] = pd.to_datetime(df['Approval Date'], format='%m/%d/%Y')
    df = df.dropna(subset=['Approval Date'])

    current_month = datetime.today().month
    current_year = datetime.now().year
    monthly_approvals_count = df[
        (df['Approval Date'].dt.month == current_month) &
        (df['Approval Date'].dt.year == current_year)
        ].shape[0]

    last_month_date = datetime.now() - pd.DateOffset(months=1)
    past_month = last_month_date.month
    past_year = last_month_date.year

    past_month_approvals_count = df[
        (df['Approval Date'].dt.month == past_month) &
        (df['Approval Date'].dt.year == past_year)
        ].shape[0]

    drug_name = most_recent_drug_info['Drug Name'].split('N')[0] if most_recent_drug_info else "N/A"
    drug_company = f"Company: {most_recent_drug_info['Company']}" if most_recent_drug_info else "N/A"
    last_updated_time = datetime.now(timezone.utc)

    return (
        str(monthly_approvals_count),
        str(past_month_approvals_count),
        drug_name,
        drug_company,
        last_updated_time.strftime("%Y-%m-%d %H:%M:%S")
    )

@app.callback(
    Output('top-companies-bar-chart', 'figure'),
    Output('year-dropdown', 'options'),
    Output('year-dropdown', 'value'),
    [Input('year-dropdown', 'value'), Input('stored-data', 'data')]
)
def update_bar_chart(selected_year, stored_data):
    data = json.loads(stored_data)
    df = pd.DataFrame(data.get('data'))
  
    df['Approval Date'] = pd.to_datetime(df['Approval Date'], format='%m%d%Y')
    df['Year'] = df['Approval Date'].dt.year
    years = sorted(df['Approval Date'].dt.year.unique())
    year_options = [{'label': str(year), 'value': year} for year in years]

    current_year = datetime.today().year # Get the latest year

    if selected_year is None:
        selected_year = current_year  # Default to the latest year if none is selected

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
    return fig_bar, year_options, selected_year
    
@app.callback(
    Output('drug_portfolio_size', 'figure'),
    Input('stored-data', 'data')
)
def update_drug_portfolio_size(data):
    data = json_util.loads(data)
    df = pd.DataFrame(data.get('data'))
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
    Input('stored-data', 'data')
)
def update_yearly_trend(data):
    data = json_util.loads(data)
    df = pd.DataFrame(data.get('data'))
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
    app.run_server()
