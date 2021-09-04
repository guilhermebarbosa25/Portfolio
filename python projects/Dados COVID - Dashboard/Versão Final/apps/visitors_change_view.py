import dash_core_components as dcc
import dash_html_components as html
import pandas as pd
import plotly.graph_objs as go
from dash.dependencies import Input, Output

from app import app
from country_options import options

population_behavior = pd.read_csv("data/changes-visitors-covid.csv")
population_behavior['Day'] = pd.to_datetime(population_behavior['Day'])

COUNTRIES = population_behavior['Entity'].unique()

county_options = [{'label': str(country), 'value': str(country)}
                  for country in COUNTRIES]


# Update metric distribution from selected country vs. world
@app.callback(Output('visitors_graph', 'figure'),
              [Input('country-dropdown', 'value')])
def update_visitors_country(selected_value):
    return _make_count_plot(country=selected_value)


def _make_count_plot(**kwargs):
    country = kwargs.get("country")
    visitors_data = population_behavior[population_behavior['Entity'] == country]

    fig = go.Figure([
        go.Scatter(
            x=visitors_data['Day'],
            mode='lines',
            y=visitors_data['retail_and_recreation'],
            line=dict(color='#00847E', width=3),
            opacity=0.7,
            name='Retail and Recreation'
        ),

        go.Scatter(
            x=visitors_data['Day'],
            mode='lines',
            y=visitors_data['grocery_and_pharmacy'],
            line=dict(color='royalblue', width=3),
            opacity=0.7,
            name='Grocery & Pharmacy'
        ),

        go.Scatter(
            x=visitors_data['Day'],
            mode='lines',
            y=visitors_data['parks'],
            line=dict(color='#333', width=3),
            opacity=0.7,
            name='Parks'
        ),

        go.Scatter(
            x=visitors_data['Day'],
            mode='lines',
            y=visitors_data['workplaces'],
            line=dict(color='#bc8e5a', width=3),
            opacity=0.7,
            name='Workplaces'
        )
    ])

    fig.update_layout(
        title="<b>Mudança de visitação por setor</b>",
        uniformtext_minsize=8,
        uniformtext_mode='hide',
        plot_bgcolor='rgba(0,0,0,0)',
        yaxis_title=None,
        xaxis_title=None,
        yaxis=dict(ticksuffix=".00%")
    )

    return fig


layout = html.Div(
    children=[
        html.Div([
            html.Div([html.P("")], className="one columns"),
            html.Div([
                html.H1(
                    children="Comportamento da população durante a pandemia",
                    className="bold_text"
                ),
                html.H6(
                    children="Análise de como a pandemia influenciou o comportamento de visitação da população em"
                             " diferentes setores, como parques e locais de trabalho.",
                )
            ],
                className="eight columns"
            ),
        ], id="header"),

        html.Div(
            [
                html.Div([html.P("")], className="one column"),
                html.Div([
                    html.Div([
                        html.H3(
                            "Mudança no comportamento de visitantes durante a pandemia",
                            className="bold_text section_title"
                        ),

                        html.H6("Como os visitantes mudaram o comportamento de visitação em diferentes setores durante"
                                "a pandemia?"),
                    ], className="eight columns"),

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
            ]
        ),

        html.Div(
            [html.Div([html.P("")], className="one column"),
             html.Div(
                 [
                     html.P("O gráfico ao lado ilustra a diferença em percentual (%) no comportamento de visitação"
                            "da população em diferentes setores durante a pandemia ao longo dos meses.")
                 ],
                 className="two columns section_legend_text"
             ),

             # Graph
             dcc.Graph(
                 figure=_make_count_plot(),
                 id="visitors_graph",
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
