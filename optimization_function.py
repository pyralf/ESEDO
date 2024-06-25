# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 09:29:52 2024

@author: adiaz
"""

import pandas as pd
import pyomo.environ as pyo
from datetime import datetime, timedelta

def generate_time_steps(start_date, end_date):
    # Liste der Zeitstempel generieren
    date_list = []
    current_date = start_date
    while current_date <= end_date:
        date_list.append(current_date.strftime("%Y-%m-%d %H:%M:%S"))
        current_date += timedelta(hours=1)

    return date_list

# %% Calculate the marginal cost of a power plant
def calculate_marginal_cost(pp_dict, fuel_prices, emission_factors):
    """
    Calculates the marginal cost of a power plant based on the fuel costs and efficiencies of the power plant.

    Parameters
    ----------
    pp_dict : dict
        Dictionary of power plant data.
    fuel_prices : dict
        Dictionary of fuel data.
    emission_factors : dict
        Dictionary of emission factors.

    Returns
    -------
    marginal_cost : float
        Marginal cost of the power plant.

    """

    fuel_price = fuel_prices[pp_dict["technology"]]
    emission_factor = emission_factors["emissions"].at[pp_dict["technology"]]
    co2_price = fuel_prices["co2"]

    fuel_cost = fuel_price / pp_dict["efficiency"]
    emissions_cost = co2_price * emission_factor / pp_dict["efficiency"]
    variable_cost = pp_dict["operational_cost"]

    marginal_cost = fuel_cost + emissions_cost + variable_cost

    return marginal_cost


# %% Calculate the marginal cost of a power plant

def calculate_opt_market_clearing_price(powerplants_df, demand_df, vre_gen_df, timestep_list):
    """
    Calculates and returns the optimal market clearing prices for a given list of time steps based on
    the power plant capacities, the demand and the variable renewable energy (vre) fed in.
    """

    # Creating model
    model = pyo.ConcreteModel()
    
    # Activating dual variables
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    
    # Define set of the plants and time steps
    model.PP = pyo.Set(initialize=powerplants_df.index.tolist())
    model.T = pyo.Set(initialize=timestep_list)

    # Define variable for the power output of each plant and it's minimum
    model.P = pyo.Var(model.PP, model.T, domain=pyo.NonNegativeReals)

    # Define constraint for the demand
    def demand_rule(m, t):
        return sum(m.P[pp, t] for pp in m.PP) + vre_gen_df.loc[t].sum() >= demand_df["demand"].at[t]
    
    model.demand = pyo.Constraint(model.T, rule=demand_rule)

    # TODO Step 2: Consider the minimum capacity of power plants
    #    on_off i,t · Pi,min ≤ Pi,t ≤ on_off i,t · Pi,max ∀i ∈ {1, . . . , N}, ∀t ∈ {1, . . . , T}
    #    QUESTION: Where does Pi,min come from or how is it derived?

    # Decision variable on / off (0 / 1) for power plants at given time
    model.ON_OFF = pyo.Var(model.PP, model.T, domain=pyo.Binary)

    # Set power plants Pmin as a fictive 10% of capacity, as we have no real values!
    powerplants['Pmin'] = 0.1 * powerplants['capacity']

    # Define constraint for capacity of each power plant
    def capacity_rule_upper(m, pp, t):
        # return m.P[pp, t] <= powerplants_df.loc[pp, 'capacity']
        return m.P[pp, t] <= m.ON_OFF[pp, t] * powerplants_df.loc[pp, 'capacity']

    def capacity_rule_lower(m, pp, t):
        return m.P[pp, t] >= m.ON_OFF[pp, t] * powerplants_df.loc[pp, 'Pmin']

    model.upper_capacity = pyo.Constraint(model.PP, model.T, rule=capacity_rule_upper)
    model.lower_capacity = pyo.Constraint(model.PP, model.T, rule=capacity_rule_lower)

    # Define objective function - cost minimization
    def objective_function(m):
        # return sum(sum(powerplants['marginal_cost'].at[pp] * m.P[pp, t] for pp in m.PP) for t in m.T)
        cost = 0
        for t in m.T:
            powerplants["marginal_cost"] = marginal_cost_df.loc[t]
            cost += sum(powerplants_df['marginal_cost'].at[pp] * m.P[pp, t] for pp in m.PP)
        return cost

    model.objective = pyo.Objective(rule=objective_function, sense=pyo.minimize)
    
    # defining solver and solve
    opt = pyo.SolverFactory('glpk')
    results = opt.solve(model)
    print(results)
    print("Print in For loop:\n")
    for v in model.component_data_objects([pyo.Var, pyo.Objective], active=True):
        print(v, '=', pyo.value(v))
    
    # Dual variable of the demand is the market clearing price
    # HINT: Use model.dual.display() to display all the content of dual variable
    print(model.dual.display())
    print("\nResulting MCPs (Market Clearing Prices):")
    mcp_list = []
    for t in model.T:
        mcp = model.dual[model.demand[t]]
        mcp_list.append(mcp)
        print(f"   MCP at {t}: {mcp}")
    
    return mcp_list


# %% Define the required dictionaries
powerplants = pd.read_csv(
    "inputs/2020_majorPowerplants_GER_1h.csv", sep=",", index_col=0, na_values=["-"]
)

emission_factors = pd.read_csv("inputs/2020_emissionFactors_GER_1h.csv", index_col=0)

fuel_prices = pd.read_csv(
    "inputs/2020_fuelPrices_GER_1h.csv", index_col=0, parse_dates=True
)

cf_df = pd.read_csv(
    "inputs/2020_renewablesCF_GER_1h.csv", index_col=0, parse_dates=True
)

demand_df = pd.read_csv("inputs/2020_demand_GER_1h.csv", index_col=0, parse_dates=True)

colors = {
    "nuclear": "green",
    "lignite": "brown",
    "hard coal": "black",
    "natural gas": "red",
    "oil": "yellow",
}

# %% Calculate the marginal cost of each power plant using apply function
marginal_cost_df = powerplants.apply(
    calculate_marginal_cost,
    axis=1,
    emission_factors=emission_factors,
    fuel_prices=fuel_prices,
).T

# %% Define the installed capacity of VRE and calculate the generation
installed_cap = {"solar": 1230000, "onshore": 54250, "offshore": 7860}  # in MW
vre_gen = cf_df * installed_cap

# %% Calculate the market clearing price

timestep_list = generate_time_steps(datetime(2020, 1, 1, 0, 0, 0),
                                    datetime(2020, 1, 1, 23, 0, 0))

market_clearing_price = calculate_opt_market_clearing_price(powerplants,
                                                            demand_df,
                                                            vre_gen,
                                                            timestep_list)
