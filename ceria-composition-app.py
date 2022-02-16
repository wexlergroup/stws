"""
Interactive app for exploring the equilibrium composition of ceria as a function
of temperature and pressure
"""
import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash import Input, Output, dcc, html
from scipy.optimize import minimize
from sklearn.preprocessing import normalize

app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Maximum off-stoichiometry ("),
                html.I("x"),
                dbc.Label(")"),
                dbc.Input(id="x", type="number", value=0.35),
                html.I("Increasing this value means there's more removable O "
                       "per formula unit of ceria"),
                html.Br(),
                html.Br(),
            ],
            style={"textAlign": "justify"},
        ),
        html.Div(
            [
                dbc.Label("O"),
                html.Sub("2"),
                dbc.Label("(g) power ("),
                html.I("n"),
                dbc.Label(")"),
                dbc.Input(id="n", type="number", value=0.218),
                html.I(
                    (
                        "Increasing this value means the reaction order is "
                        "higher in O",
                        html.Sub("2"),
                        "(g)",
                    ),
                ),
                html.Br(),
                html.Br(),
            ],
            style={"textAlign": "justify"},
        ),
        html.Div(
            [
                dbc.Label("Oxygen vacancy formation energy ("),
                html.I(
                    (
                        "E",
                        html.Sub("v")
                    )
                ),
                dbc.Label(") in kJ/mol"),
                dbc.Input(id="Ev", type="number", value=195.6),
                html.I("Increasing this value makes it harder to form an "
                       "oxygen vacancy"),
                html.Br(),
                html.Br(),
            ],
            style={"textAlign": "justify"},
        ),
        html.Div(
            [
                dbc.Label("Ratio of Arrhenius rate constants ("),
                html.I(
                    (
                        "k",
                        html.Sub("red,0"),
                        "/k",
                        html.Sub("ox,0")
                    )
                ),
                dbc.Label(") in bar"),
                html.I(
                    (
                        html.Sup("n"),
                    )
                ),
                dbc.Input(id="kred0_kox0", type="number", value=8700),
                html.I("Increasing this value favors reduction over oxidation "
                       "via the Arrhenius prefactors"),
                html.Br(),
                html.Br(),
            ],
            style={"textAlign": "justify"},
        ),
        html.Div(
            [
                dbc.Label("Pressure (bar)"),
                dbc.Input(id="P", type="number", value=0.001),
                html.I(
                    (
                        "Decreasing this value favors the production of O",
                        html.Sub("2"),
                        "(g)",
                    ),
                ),
                html.Br(),
                html.Br(),
            ],
            style={"textAlign": "justify"},
        ),
    ],
    body=True,
)

app.layout = dbc.Container(
    [
        html.Br(),
        html.H2("Equilibrium composition of ceria"),  # title
        html.Hr(),  # line
        dbc.Row(
            [
                dbc.Col(
                    (
                        html.P("In this app, you can calculate the "
                               "temperature dependence of the equilibrium "
                               "composition of ceria during the first – "
                               "thermal reduction – step of solar "
                               "thermochemical water splitting. This is done "
                               "using the kinetic model developed in the "
                               "following paper:"),
                        html.A("https://doi.org/10.1021/jp406578z",
                               href="https://doi.org/10.1021/jp406578z",
                               target="_blank"),
                        html.Br(),
                        html.Br(),
                        html.H4("Set the kinetic parameters for the thermal "
                                "reduction of ceria"),
                        controls,
                    ),
                    style={"textAlign": "justify"}
                ),
                dbc.Col(dcc.Graph(id="equilibrium-composition")),
            ],
            align="center",
        ),
    ],
)


@app.callback(
    Output("equilibrium-composition", "figure"),
    [
        Input("x", "value"),
        Input("n", "value"),
        Input("Ev", "value"),
        Input("kred0_kox0", "value"),
        Input("P", "value")
    ],
)
def make_graph(x, n, Ev, kred0_kox0, P):
    # Define experimental conditions
    R = 0.008314462618  # kJ/(mol K)
    T = np.linspace(1300, 2300, 101)
    RT = R * T

    # Calculate equilibrium composition vs. T
    delta = x / ((kred0_kox0 * P ** (-n) * np.exp(-Ev / RT)) ** (-1) + 1)

    # Plot equilibrium composition
    data = [
        go.Line(
            x=T,
            y=delta,
            name="delta",
        ),
    ]

    layout = {"xaxis": {"title": "T"},
              "yaxis": {"title": "Mole fraction"},
              "height": 700}

    return go.Figure(data=data, layout=layout)


if __name__ == "__main__":
    app.run_server()
