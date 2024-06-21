# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 09:29:52 2024

@author: adiaz
"""

import pandas as pd
import pyomo.environ as pyo

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

def calculate_opt_market_clearing_price(powerplants, demand, vre_feed_in):
    
    # Creating model
    model = pyo.ConcreteModel()
    
    # Activating dual varialbles
    model.dual = pyo.Suffix(direction=pyo.Suffix.IMPORT)
    
    # define set of the  plants
    model.PP = pyo.Set(initialize= powerplants.index.tolist())
    
    # define variable for the power output of each plant
    
    model.P = pyo.Var(model.PP, domain=pyo.NonNegativeReals)
    
    # Define constraint for the demand 
    
    def demand_rule(m):
        return sum(m.P[pp] for pp in m.PP) + vre_feed_in == demand
    
    model.demand = pyo.Constraint(rule=demand_rule)
    
    # define constraint for capacity of each power plant
    
    def capacity_rule(m, pp):
        return m.P[pp] <= powerplants.loc[pp,'capacity']

    model.capacity = pyo.Constraint(model.PP, rule=capacity_rule)
    
    # define objective function - cost minimization
    def objective_function(m):
        return sum(powerplants['marginal_cost'].at[pp] * m.P[pp] for pp in m.PP)
    
    model.objective = pyo.Objective(rule=objective_function, sense=pyo.minimize)
    
    # defining solver
    opt = pyo.SolverFactory('glpk')
    results = opt.solve(model)
    print(results)
    print("Print in For loop:\n")
    for v in model.component_data_objects([pyo.Var, pyo.Objective], active=True):
        print(v, '=', pyo.value(v))
    
    # Dual variable of the demand is the market clearing price
    mcp = model.dual[model.demand]
    
    return mcp
    
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

timestep = "2020-06-21 12:00"
powerplants["marginal_cost"] = marginal_cost_df.loc[timestep]

market_clearing_price = calculate_opt_market_clearing_price(powerplants,
                                                            demand_df["demand"].at[timestep],
                                                            vre_gen.loc[timestep].sum())
