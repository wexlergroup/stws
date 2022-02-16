"""
Interactive app for exploring the equilibrium composition for solar thermolysis
as a function of temperature and pressure
"""
import dash
import dash_bootstrap_components as dbc
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from dash import Input, Output, dcc, html
from scipy.optimize import minimize
from sklearn.preprocessing import normalize


def factsage(p):
    """ Read thermodynamic data downloaded from FactSage """
    data = []
    with open(p, encoding="iso-8859-1") as f:
        for line in f:
            if "------" in line:
                break
        condition = ""
        while condition == "":
            for line in f:
                if "------" in line:
                    break
                elif "___________" in line or "_______" in line:
                    condition = "stop"
                    break
                data.append(line.split()[:7])
    data = np.array(data).astype(float)
    df = pd.DataFrame(data, columns=["T", "dH", "dG", "dV", "dS", "dCp", "Keq"])
    return df[["T", "dH", "dG", "dS", "Keq"]].copy()


# Read thermodynamic data
H2O = factsage("solar-thermolysis-data/H2O.txt")
H = factsage("solar-thermolysis-data/H.txt")
O = factsage("solar-thermolysis-data/O.txt")
OH = factsage("solar-thermolysis-data/OH.txt")

# Remove unnecessary columns
H2O = H2O[["T", "dG"]]
H = H[["T", "dG"]]
O = O[["T", "dG"]]
OH = OH[["T", "dG"]]

# Keep only T ≥ 400 K
H2O = H2O[H2O["T"] >= 400]
H = H[H["T"] >= 400]
O = O[O["T"] >= 400]
OH = OH[OH["T"] >= 400]

# Convert energy units from J/mol to kJ/mol
H2O["dG"] /= 1000
H["dG"] /= 1000
O["dG"] /= 1000
OH["dG"] /= 1000


# Define objective function
def gibbs_free_energy(N_guess, dGfs, Press=1):
    """
Calculate nG/RT for guessed composition and standard formation free energies
    """
    N_guess = np.array(N_guess)
    N_total = N_guess.sum()
    y = N_guess / N_total  # mole fractions
    ln_y = np.log(y)
    dGfs = np.array(dGfs)
    partial_molar_gibbs_free_energy = N_guess * (dGfs + ln_y + np.log(Press))
    return partial_molar_gibbs_free_energy.sum()


app = dash.Dash(
    external_stylesheets=[dbc.themes.BOOTSTRAP]
)

controls = dbc.Card(
    [
        html.Div(
            [
                dbc.Label("Pressure (bar)"),
                dbc.Input(id="P", type="number", value=1),
            ]
        ),
    ],
    body=True,
)

app.layout = dbc.Container(
    [
        html.H2("Equilibrium composition for solar thermolysis"),  # title
        html.Hr(),  # line
        dbc.Row(
            [
                dbc.Col(
                    (
                        html.P("In this app, you can calculate the "
                               "temperature dependence of the equilibrium "
                               "composition for solar thermolysis. This is "
                               "done using the Gibbs-free-energy-minimization "
                               "method and scipy as the optimizer. All you "
                               "have to do is set the pressure in bar and "
                               "then see how the equilibrium composition "
                               "changes. Enjoy!"),
                        html.H4("Set the pressure for solar thermolysis"),
                        controls,
                    ),
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
        Input("P", "value"),
    ],
)
def make_graph(P):
    # Initialize Gibbs-free-energy minimization
    N_H2O = 0.99
    N_H2 = 0.01
    N_O2 = 0.01
    N_H = 0.01
    N_O = 0.01
    N_OH = 0.01
    N = [N_H2O, N_H2, N_O2, N_H, N_O, N_OH]

    # Define atomic-balance constraint
    constraint = (
        {"type": "eq",
         # 2 * N_H2O + 2 * N_H2 + N_H + N_OH - 2 mol H in H2O at start = 0
         "fun": lambda x: 2 * x[0] + 2 * x[1] + x[3] + x[5] - 2},
        {"type": "eq",
         # N_H2O + 2 * N_O2 + N_O + N_OH - 1 mol O in H2O at start = 0
         "fun": lambda x: x[0] + 2 * x[2] + x[4] + x[5] - 1})
    bnds = ((0, 2), (0, 2), (0, 2), (0, 2), (0, 2), (0, 2))

    # Calculate equilibrium composition (X) vs. T in a stepwise fashion
    X = []
    R = 0.008314462618  # kJ/(mol K)
    for i in range(H2O.shape[0]):
        T = H2O["T"].iloc[i]
        RT = R * T
        dGf_H2O = H2O["dG"].iloc[i] / RT
        dGf_H2 = 0  # standard state
        dGf_O2 = 0
        dGf_H = H["dG"].iloc[i] / RT
        dGf_O = O["dG"].iloc[i] / RT
        dGf_OH = OH["dG"].iloc[i] / RT
        dGf = [dGf_H2O, dGf_H2, dGf_O2, dGf_H, dGf_O, dGf_OH]

        # Minimize G
        result = minimize(fun=gibbs_free_energy, x0=N, args=(dGf, P),
                          bounds=bnds,
                          method="SLSQP", tol=1e-6, constraints=constraint)
        N = result.x  # equilibrium composition at T and P
        X.append(N)
    X = np.array(X)

    # Plot equilibrium mole fractions
    Y = normalize(X, norm="l1")  # convert moles to mole fractions
    data = [
        go.Line(
            x=H2O["T"],
            y=Y[:, 0],
            name="H2O",
        ),
        go.Line(
            x=H2O["T"],
            y=Y[:, 1],
            name="H2",
        ),
        go.Line(
            x=H2O["T"],
            y=Y[:, 2],
            name="O2",
        ),
        go.Line(
            x=H2O["T"],
            y=Y[:, 3],
            name="H",
        ),
        go.Line(
            x=H2O["T"],
            y=Y[:, 4],
            name="O",
        ),
        go.Line(
            x=H2O["T"],
            y=Y[:, 5],
            name="OH",
        ),
    ]

    layout = {"xaxis": {"title": "T"}, "yaxis": {"title": "Mole fraction"}}

    return go.Figure(data=data, layout=layout)


if __name__ == "__main__":
    app.run_server()
