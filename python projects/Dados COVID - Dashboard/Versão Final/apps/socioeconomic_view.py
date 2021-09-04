import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.express as px
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app

data = pd.read_csv("data/owid-covid-data.csv")
data['date'] = pd.to_datetime(data['date'])

filtered_covid_data = data[~data['location'].isin(
    ['World', 'Asia', 'Europe', 'North America', 'South America', 'European Union'])].copy()

filtered_covid_data = filtered_covid_data[filtered_covid_data['population'] > 5e6]


def get_metric_by_country(country_name: str, metric: str):
    filtered_data = data[data['location'] == country_name]

    return filtered_data.groupby(['date'])[[metric, f'{metric}_smoothed']].sum().reset_index()


def get_metric_by_region(metric):
    cases_by_region = data.groupby(['continent'])[metric].sum()
    return cases_by_region.sort_values(ascending=True).reset_index()


def get_region_stats_over_time():
    return data.groupby('continent').resample('W', on='date').sum().reset_index().sort_values(by='date')


def _get_top_k_kpi(k: int = 3, metric: str = 'new_deaths', agg_metric: bool = False):
    if agg_metric:
        filtered_kpi = filtered_covid_data.groupby(
            ['location']
        )[metric].max().sort_values(ascending=False)[:k].reset_index()
    else:
        filtered_kpi = filtered_covid_data.groupby(
            ['location']
        )[metric].sum().sort_values(ascending=False)[:k].reset_index()

    return filtered_kpi


COUNTRIES = data['location'].unique()

county_options = [{'label': str(country), 'value': str(country)}
                  for country in COUNTRIES]


def _get_socioeconomic_metric(metric: str):
    top_idh_location = _get_top_k_kpi(metric=metric, k=1, agg_metric=True)
    agg_metric = top_idh_location['location'][0]
    return str(agg_metric)


# Update socioeconomic indicator chart on filter selection
@app.callback(Output('socioeconomic_kpi', 'figure'),
              [Input('kpi-dropdown', 'value')])
def update_ranking_plots(selected_value):
    return _make_ranking_plot(metric=selected_value, agg_metric=True)


# Update metric distribution from selected country vs. world
@app.callback(Output('new_deaths_dist', 'figure'),
              [Input('kpi-dropdown', 'value')])
def update_new_deaths_kpi(selected_value):
    return _make_count_plot(
        metric="new_deaths_smoothed_per_million",
        socio_metric=selected_value
    )


# Update metric distribution from selected country vs. world
@app.callback(Output('new_cases_dist', 'figure'),
              [Input('kpi-dropdown', 'value')])
def update_new_cases_kpi(selected_value):
    return _make_count_plot(
        metric="new_cases_smoothed_per_million",
        socio_metric=selected_value
    )


# Update metric distribution from selected country vs. world
@app.callback(Output('new_vaccinations_dist', 'figure'),
              [Input('kpi-dropdown', 'value')])
def update_new_vaccinations_kpi(selected_value):
    return _make_count_plot(
        metric="new_vaccinations_smoothed_per_million",
        socio_metric=selected_value
    )


def _make_count_plot(metric, **kwargs):
    socio_metric = kwargs.get("socio_metric", "gdp_per_capita")
    country = _get_top_k_kpi(k=1, metric=socio_metric, agg_metric=True)['location'][0]

    wrld = data[data['location'] == 'World']
    wrld_kpi = wrld.groupby(['date'])[metric].sum().reset_index()

    socio_metric_filtered = filtered_covid_data[filtered_covid_data['location'] == country]
    top_country = socio_metric_filtered.groupby(['date'])[metric].sum().reset_index()

    if metric == "new_deaths_smoothed_per_million":
        title = "<b>Mortes suavizadas por milhão de habitantes</b>"
    elif metric == "new_cases_smoothed_per_million":
        title = "<b>Novos casos suavizados por milhão de habitantes</b>"
    else:
        title = "<b>Número de vacinados suavizado por milhão de habitantes</b>"

    if socio_metric == "gdp_per_capita":
        s_metric = "PIB per capita"
    elif socio_metric == "human_development_index":
        s_metric = "IDH"
    else:
        s_metric = "Expectativa de vida"

    fig = go.Figure([
        go.Scatter(
            x=top_country['date'],
            mode='lines',
            y=top_country[metric],
            line=dict(color='royalblue', width=3),
            name=f'País líder em {s_metric}',
            opacity=0.7,
        ),

        go.Scatter(
            x=wrld_kpi['date'],
            mode='lines',
            y=wrld_kpi[metric],
            line=dict(color='orange', width=3),
            opacity=0.7,
            name='Mundo'
        )
    ])

    fig.update_layout(
        title=title,
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title=None,
        xaxis_title=None
    )

    return fig


def _make_ranking_plot(metric: str, agg_metric: bool = False):
    if agg_metric:
        top15 = _get_top_k_kpi(k=15, metric=metric, agg_metric=True)
    else:
        top15 = filtered_covid_data.groupby(['location'])[metric].sum().sort_values(ascending=False)[:15].reset_index()

    if metric == "gdp_per_capita":
        title = "<b>PIB per capita.</b>"
    elif metric == "human_development_index":
        title = "<b>Índice de Desenvolvimento Humano.</b>"
    elif metric == "life_expectancy":
        title = "<b>Expectativa de vida dos habitantes.</b>"
    elif metric == "new_tests_per_thousand":
        title = "<b>Número de testes por 1000 habitantes.</b>"
    else:
        title = "<b>Total de vacinas por 100 habitantes.</b>"

    top15_sorted = top15.sort_values(metric)
    fig = px.bar(
        top15_sorted,
        x=metric,
        y='location',
        text=metric,
        title=title,
        opacity=0.7
    )

    fig.update_traces(
        texttemplate='%{text:.2s}',
        textposition='inside',
        marker_color='grey'
    )

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
                    children="Indicadores Socioeconômicos",
                    className="bold_text"
                ),
                html.H6(
                    children="Análise de como indicadores socioeconômicos (PIB, IDH, Expectativa de vida) se "
                             "correlacionam com as métricas observadas no combate à pandemia.",
                )
            ],
                className="eight columns"
            ),
        ], id="header"),

        html.Div(
            [
                html.Div([html.P("")], className="one column"),
                html.Div(
                    [
                        html.H3(
                            # TEMP - hardcoded
                            '🇳🇴 ' + _get_socioeconomic_metric(metric="human_development_index"),
                            id="top_idh",
                            className="bold_text",
                        ),
                        html.H6("#1 em IDH")
                    ],
                    id="kpi_idh",
                    className="three columns pretty_container"
                ),

                html.Div([html.P("")], className="one column"),

                html.Div(
                    [
                        html.H3(
                            '🇭🇰 ' + _get_socioeconomic_metric(metric="life_expectancy"),
                            id="top_life_exp",
                            className="bold_text"
                        ),
                        html.H6("#1 em Expectativa de vida")
                    ],
                    id="kpi_life_exp",
                    className="three columns pretty_container"
                ),

                html.Div([html.P("")], className="one column"),

                html.Div(
                    [
                        html.H3(
                            '🇸🇬 ' + _get_socioeconomic_metric(metric="gdp_per_capita"),
                            id="top_gdp",
                            className="bold_text"
                        ),
                        html.H6("#1 em PIB per capita")
                    ],
                    id="kpi_gdp",
                    className="three columns pretty_container"
                ),
            ],
            className="section_title"
        ),

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
                    ], className="eight columns"),

                    html.Div([
                        html.P(
                            "Selecione o indicador:",
                            className="control_label bold_text"
                        ),

                        dcc.Dropdown(
                            id='kpi-dropdown',
                            options=[{'label': 'PIB per capita', 'value': 'gdp_per_capita'},
                                     {'label': 'IDH', 'value': 'human_development_index'},
                                     {'label': 'Expectativa de vida', 'value': 'life_expectancy'}],
                            multi=False,
                            value="gdp_per_capita",
                            searchable=True,
                            className="dcc_control"
                        ),
                    ], className="two columns section_title_kpis"),
                ]),
            ]
        ),

        html.Div([
            html.Div([html.P("")], className="one column"),
            dcc.Graph(
                figure=_make_ranking_plot(metric="gdp_per_capita", agg_metric=True),
                id="socioeconomic_kpi",
                className="three columns"
            ),

            html.Div([html.P("")], className="one column"),
            dcc.Graph(
                figure=_make_ranking_plot(metric="new_tests_per_thousand"),
                className="three columns"
            ),

            html.Div([html.P("")], className="one column"),
            dcc.Graph(
                figure=_make_ranking_plot(metric="total_vaccinations_per_hundred"),
                className="three columns"
            ),
        ]),

        html.Div([
            html.Div([html.P("")], className="one column"),
            html.Div(
                [
                    html.H3(
                        "Países líderes em indicadores socioeconômicos",
                        className="bold_text section_title"
                    ),

                    html.H6("Como países líderes em indicadores socioeconômicos (PIB, IDH e Expectativa de vida) se"
                            "comparam com o resto do mundo no combate à Covid-19?"),
                ], className="eight columns"),
        ]),

        html.Div(
            [html.Div([html.P("")], className="one column"),
             html.Div(
                 [
                     html.P("O número de mortes suavizada (smoothed) é calculada utilizando a média móvel de 7 dias.")
                 ],
                 className="two columns section_legend_text"
             ),
             # Graph
             dcc.Graph(
                 figure=_make_count_plot(metric='new_deaths_smoothed_per_million'),
                 id="new_deaths_dist",
                 className="eight columns"
             ),
             ],
            className="section_title"
        ),

        html.Div(
            [html.Div([html.P("")], className="one column"),
             html.Div(
                 [
                     html.P("Embora a curva de novos casos para países líderes em indicadors socioeconômicos seja "
                            "maior que a geral em alguns momentos, geralmente esses países se recuperam mais rápido, "
                            "em alguns casos estabilizando rapidamente os indicadores da pandemia.")
                 ],
                 className="two columns section_legend_text"
             ),
             # Graph
             dcc.Graph(
                 figure=_make_count_plot(metric='new_cases_smoothed_per_million'),
                 id="new_cases_dist",
                 className="eight columns"
             ),
             ],
            className="section_title"
        ),

        html.Div(
            [html.Div([html.P("")], className="one column"),
             html.Div(
                 [
                     html.P("Esses países também empregaram uma campanha de vacinação mais eficiente que o resto do "
                            "mundo, mesmo em alguns casos começando tardiamente. O gráfico ao lado indica que esses "
                            "países possuem indicadores muito superiores à média, possivelmente impactando nos "
                            "indicadores de novos casos e mortes.")
                 ],
                 className="two columns section_legend_text"
             ),
             # Graph
             dcc.Graph(
                 figure=_make_count_plot(metric='new_vaccinations_smoothed_per_million'),
                 id="new_vaccinations_dist",
                 className="eight columns"
             ),
             ],
            className="section_title"
        )

    ],
    id="mainContainer",
    style={
        "display": "flex",
        "flex-direction": "column"
    }
)
