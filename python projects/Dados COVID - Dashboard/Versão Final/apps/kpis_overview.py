import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app
from country_options import options

data = pd.read_csv("data/owid-covid-data.csv")
data['date'] = pd.to_datetime(data['date'])


def get_metric_by_country(country_name: str, metric: str):
    filtered_data = data[data['location'] == country_name]

    return filtered_data.groupby(['date'])[[metric, f'{metric}_smoothed']].sum().reset_index()


def get_metric_by_region(metric):
    cases_by_region = data.groupby(['continent'])[metric].sum()
    return cases_by_region.sort_values(ascending=True).reset_index()


def get_region_stats_over_time():
    return data.groupby('continent').resample('W', on='date').sum().reset_index().sort_values(by='date')


COUNTRIES = data['location'].unique()

county_options = [{'label': str(country), 'value': str(country)}
                  for country in COUNTRIES]


# Update new cases KPI on filter
@app.callback(Output('new_cases_kpi', 'children'),
              [Input('country-dropdown', 'value')])
def _update_total_by_metric(selected_value):
    metric_by_country = get_metric_by_country(country_name=selected_value, metric="new_cases")
    agg_metric = metric_by_country.sum().values[0]
    return f"{agg_metric:,}".replace('.0', '')


# Update new deaths KPI
@app.callback(Output('new_deaths_kpi', 'children'),
              [Input('country-dropdown', 'value')])
def _update_total_by_metric(selected_value):
    metric_by_country = get_metric_by_country(country_name=selected_value, metric="new_deaths")
    agg_metric = metric_by_country.sum().values[0]
    return f"{agg_metric:,}".replace('.0', '')


# Update new vaccinations KPI
@app.callback(Output('new_vaccinations_kpi', 'children'),
              [Input('country-dropdown', 'value')])
def _update_total_by_metric(selected_value):
    metric_by_country = get_metric_by_country(country_name=selected_value, metric="new_cases")
    agg_metric = metric_by_country.sum().values[0]
    return f"{agg_metric:,}".replace('.0', '')


# Update new cases chart on filter selection
@app.callback(Output('new_cases_count', 'figure'),
              [Input('country-dropdown', 'value')])
def update_new_cases_figure(selected_value):
    return _make_count_plot(metric="new_cases", country=selected_value)


# Update new deaths chart on filter selection
@app.callback(Output('new_deaths_count', 'figure'),
              [Input('country-dropdown', 'value')])
def update_new_deaths_figure(selected_value):
    return _make_count_plot(metric="new_deaths", country=selected_value)


# Update new vaccinations chart on filter selection
@app.callback(Output('new_vaccinations_count', 'figure'),
              [Input('country-dropdown', 'value')])
def update_new_vaccinations_figure(selected_value):
    return _make_count_plot(metric="new_vaccinations", country=selected_value)


def _make_count_plot(metric: str, **kwargs):
    country = kwargs.get("country")
    cases = get_metric_by_country(country_name=country, metric=metric)

    if metric == 'new_cases':
        title = f'<b>Casos confirmados no(a) {country}</b>'
    elif metric == 'new_deaths':
        title = f'<b>Mortes confirmadas no(a) {country}</b>'
    else:
        title = f'<b>Total de vacinas administradas no(a) {country}</b>'

    fig = px.bar(
        cases,
        x='date',
        y=metric,
        title=title,
        opacity=0.4
    )

    fig.add_trace(
        go.Scatter(
            x=cases['date'],
            mode='lines',
            y=cases[f'{metric}_smoothed'],
            line=dict(color='royalblue', width=3),
            name='Média móvel (7 dias)'
        ),
        row=1,
        col=1
    )

    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title=None,
        xaxis_title=None
    )

    return fig


def _make_region_barplot():
    # Overall cases by continent
    regions_stats = get_metric_by_region(metric='new_cases')

    _colors = ['#AB63FA', '#19D3F3', '#00CC96', '#EF553B', '#FFA15A', '#636EFA']

    fig = px.bar(regions_stats,
                 x='new_cases',
                 y='continent',
                 text='new_cases',
                 title='Casos confirmados por região.',
                 opacity=0.7)

    fig.update_traces(texttemplate='%{text:.2s}', textposition='inside', marker_color=_colors)
    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis={
            'showgrid': False
        },
        yaxis={
            'showgrid': False
        },
        yaxis_title=None,
        xaxis_title=None
    )

    return fig


def make_stacked_bar_region():
    # Regions stats over time
    grouped_stats = get_region_stats_over_time()

    fig = px.bar(
        grouped_stats,
        color='continent',
        x='date',
        y='new_cases',
        text='new_cases',
        title='Distribuição dos casos por região',
        opacity=0.7
    )

    fig.update_layout(
        barmode='stack',
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        xaxis={
            'showgrid': False
        },
        yaxis={
            'showgrid': False
        },
        yaxis_title=None,
        xaxis_title=None
    )

    return fig


def _make_ranking_plot(metric: str):
    filtered_covid_data = data[~data['location'].isin(
        ['World', 'Asia', 'Europe', 'North America', 'South America', 'European Union'])].copy()

    top15 = filtered_covid_data.groupby(['location'])[metric].sum().sort_values(ascending=False)[:15].reset_index()

    median_metric = top15[metric].median()
    max_x = median_metric / top15[metric].max()

    if metric == "new_cases":
        title = "Top 15 países em <b>casos confirmados</b>."
        annotation = "<b>Média de casos</b>"
        top15["color"] = top15[metric].apply(lambda n: "darkorange" if n > median_metric else "grey")
    elif metric == "new_deaths":
        title = "Top 15 países em <b>mortes confirmadas</b>."
        annotation = "<b>Média de mortes</b>"
        top15["color"] = top15[metric].apply(lambda n: "darkorange" if n > median_metric else "grey")
    else:
        title = "Top 15 países em <b>vacinas administradas</b>."
        annotation = "<b>Média de vacinação</b>"
        top15["color"] = top15[metric].apply(lambda n: "royalblue" if n > median_metric else "grey")

    top15_sorted = top15.sort_values(metric)
    fig = px.bar(top15_sorted,
                 x=metric,
                 y='location',
                 color='color',
                 color_discrete_sequence=top15_sorted['color'].unique(),
                 text=metric,
                 title=title,
                 opacity=0.7)
    fig.update_traces(texttemplate='%{text:.2s}', textposition='inside')

    fig.add_shape(type="line",
                  xref="paper",
                  yref="paper",
                  x0=max_x,
                  y0=0,
                  x1=max_x,
                  y1=1,
                  line=dict(
                      color="lightgrey",
                      width=2,
                      dash="dash"
                  ),
                  )

    fig.add_annotation(x=median_metric,
                       y=5,
                       text=annotation,
                       showarrow=False,
                       xshift=60)

    fig.update_layout(
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        showlegend=False,
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title=None,
        xaxis_title=None
    )

    return fig


layout = html.Div(
    children=[
        html.Div([
            html.Div([html.P("")], className="one columns"),
            html.Div([
                html.H1(
                    children="Análise de dados COVID-19",
                    className="bold_text"
                ),
                html.H6(
                    children="Painel com indicadores gerais sobre a pandemia Covid-19 com dados coletados de cerca de"
                             " 225 países ao redor do mundo e como os mesmos estão combatendo à pandemia.",
                )
            ],
                className="eight columns"
            ),
        ], id="header"),

        html.Div([
            # TEMP
            html.Div([html.P("")], className="one column"),
            html.Div([
                html.H3(
                    "Visão geral",
                    className="bold_text section_title"
                ),
                html.H6(
                    "Essa seção apresenta uma visão geral dos principais indicadores de acompanhamento da pandemia"
                    " Covid-19 por país."
                ),
            ],
                className="eight columns"
            ),

            html.Div([
                html.P(
                    "Selecione o país:",
                    className="control_label bold_text"
                ),

                dcc.Dropdown(
                    id='country-dropdown',
                    options=options,
                    multi=False,
                    value="Brazil",
                    searchable=True,
                    className="dcc_control"
                ),
            ], className="two columns section_title"),
        ]),

        html.Div(
            [
                html.Div([html.P("")], className="one column"),
                html.Div(
                    [
                        html.H2(
                            className="bold_text",
                            id="new_cases_kpi"
                        ),
                        html.H6("Casos confirmados")
                    ],
                    id="kpi_confirmed_cases",
                    className="two columns"
                ),
                # Graph
                dcc.Graph(
                    figure=_make_count_plot(metric='new_cases'),
                    id="new_cases_count",
                    className="eight columns"
                ),
            ],
            className="section_title",
        ),

        html.Div(
            [
                html.Div([html.P("")], className="one column"),
                html.Div(
                    [
                        html.H2(
                            id="new_deaths_kpi",
                            className="bold_text"
                        ),
                        html.H6("Mortes confirmadas")
                    ],
                    id="kpi2",
                    className="two columns"
                ),
                # Graph
                dcc.Graph(
                    figure=_make_count_plot(metric='new_deaths'),
                    id="new_deaths_count",
                    className="eight columns"
                ),
            ],
            className="section_title"
        ),

        html.Div(
            [html.Div([html.P("")], className="one column"),
             html.Div(
                 [
                     html.H2(
                         className="bold_text",
                         id="new_vaccinations_kpi"
                     ),
                     html.H6("Total de vacinas aplicadas")
                 ],
                 id="kpi4",
                 className="two columns"
             ),
             # Graph
             dcc.Graph(
                 figure=_make_count_plot(metric='new_vaccinations'),
                 id="new_vaccinations_count",
                 className="eight columns"
             ),
             ],
            className="section_title"
        ),

        # Region situation
        html.Div([
            html.Div([html.P("")], className="one column"),
            html.Div(
                [
                    html.H3(
                        "Situação por região",
                        className="bold_text section_title"
                    ),

                    html.H6("Situação da pandemia por região continental para o indicador de casos confirmados."),
                ], className="eight columns"),
        ]),

        html.Div([
            html.Div([html.P("")], className="one column"),
            html.Div(
                [
                    dcc.Graph(
                        figure=_make_region_barplot()
                    ),
                ],
                id="kpi3",
                className="four columns"
            ),
            html.Div([
                # Graph
                dcc.Graph(
                    figure=make_stacked_bar_region(),
                ),
            ],
                className="six columns"
            )]),

        html.Div(
            [
                html.Div([html.P("")], className="one column"),
                html.Div([
                    html.Div([
                        html.H3(
                            "Ranking",
                            className="bold_text section_title"
                        ),

                        html.H6("Ranking dos países (TOP 15) nos principais indicadores sobre a pandemia."),
                    ], className="six columns"),
                ]),
            ]
        ),

        html.Div([
            html.Div([html.P("")], className="one column"),
            dcc.Graph(
                figure=_make_ranking_plot(metric="new_cases"),
                className="three columns"
            ),

            html.Div([html.P("")], className="one column"),
            dcc.Graph(
                figure=_make_ranking_plot(metric="new_deaths"),
                className="three columns"
            ),

            html.Div([html.P("")], className="one column"),
            dcc.Graph(
                figure=_make_ranking_plot(metric="new_vaccinations"),
                className="three columns"
            ),
        ])

    ],
    id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)
