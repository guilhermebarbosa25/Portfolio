import dash_bootstrap_components as dbc
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

# must add this line in order for the app to be deployed successfully on Heroku
from app import app
# import all pages in the app
from apps import kpis_overview, socioeconomic_view, visitors_change_view

dropdown = dbc.DropdownMenu(
    children=[
        dbc.DropdownMenuItem("Visão geral", href="/home"),
        dbc.DropdownMenuItem("Indicadores socioeconômicos", href="/socioeconomic"),
        dbc.DropdownMenuItem("Comportamento de visitação", href="/visitors-change"),
    ],
    nav=True,
    in_navbar=True,
    label="Explorar",
)

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.A(
                # Use row and col to control vertical alignment of logo / brand
                dbc.Row(
                    [
                        dbc.Col(html.Img(src="/assets/virus.png", height="30px")),
                        dbc.Col(dbc.NavbarBrand("Covid-19 Analytics", className="ml-4")),
                    ],
                    align="center",
                    no_gutters=True,
                ),
                href="/home",
            ),
            dbc.NavbarToggler(id="navbar-toggler2"),
            dbc.Collapse(
                dbc.Nav(
                    # right align dropdown menu with ml-auto className
                    [dropdown], className="ml-auto", navbar=True
                ),
                id="navbar-collapse2",
                navbar=True,
            ),
        ]
    ),
    color="dark",
    dark=True,
    className="mb-4"
)


def toggle_navbar_collapse(n, is_open):
    if n:
        return not is_open
    return is_open


for i in [2]:
    app.callback(
        Output(f"navbar-collapse{i}", "is_open"),
        [Input(f"navbar-toggler{i}", "n_clicks")],
        [State(f"navbar-collapse{i}", "is_open")],
    )(toggle_navbar_collapse)

# embedding the navigation bar
app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    navbar,
    html.Div(id='page-content')
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
    if pathname == '/visitors-change':
        return visitors_change_view.layout
    elif pathname == '/socioeconomic':
        return socioeconomic_view.layout
    else:
        return kpis_overview.layout


if __name__ == '__main__':
    app.run_server(debug=True)
