# %% Import relevant packages
import pandas as pd
import matplotlib.pyplot as plt


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


# %% Calculate the market clearing price
def calculate_market_clearing_price(powerplants, demand, vre_gen=0):
    """
    Calculates the market clearing price of the merit order model.

    Parameters
    ----------
    powerplants : pandas.DataFrame
        Dataframe containing the power plant data.
    demand : float
        Demand of the system.

    Returns
    -------
    mcp : float
        Market clearing price.

    """

    demand = demand - vre_gen

    # Sort the power plants on marginal cost
    powerplants = powerplants.sort_values(by=["marginal_cost"])

    # Calculate the cumulative capacity
    powerplants["cum_capacity"] = powerplants["capacity"].cumsum()

    if demand > powerplants["cum_capacity"].iat[-1]:
        mcp = 3000
    elif demand <= 0:
        mcp = 0
    else:
        mcp = powerplants.loc[
            powerplants["cum_capacity"] >= demand, "marginal_cost"
        ].iat[0]

    return mcp


def assign_color(powerplant):
    """
    Assigns a color to a power plant based on the technology.

    Parameters
    ----------
    powerplant : pandas.Series
        Series containing the power plant data.

    Returns
    -------
    color : str
        Color of the power plant.

    """

    technology = powerplant["technology"]
    color = colors[technology]

    return color


def plot_merit_order_curve(powerplants, mcp, demand, feed_in):
    """
    Plots the merit order curve.

    Parameters
    ----------
    powerplants : pandas.DataFrame
        Dataframe containing the power plant data.
    demand : float
        Demand of the system.

    Returns
    -------
    None.

    """

    # Plot the merit order curve
    powerplants.sort_values("marginal_cost", inplace=True)

    plt.plot()
    plt.bar(
        x=0,
        height=1,
        width=feed_in,
        color="blue",
        label="Renewables",
        align="edge",
        alpha=0.4,
        edgecolor="k",
    )

    plt.bar(
        x=feed_in + powerplants.capacity.cumsum() - powerplants.capacity,
        height=powerplants["marginal_cost"],
        width=powerplants.capacity,
        align="edge",
        color=powerplants["color"],
        alpha=0.4,
        edgecolor="k",
    )

    plt.xlim(left=0)
    plt.plot([demand, demand], [0, mcp], "r--", label="demand")
    plt.plot([0, demand], [mcp, mcp], "r--", label="mcp")
    plt.xlabel("Marginal cost")
    plt.ylabel("Capacity")
    plt.title("Merit order curve")
    plt.show()


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
installed_cap = {"solar": 54360, "onshore": 54250, "offshore": 7860}  # in MW
vre_gen = cf_df * installed_cap

# %% Calculate the market clearing price
mcp_df = pd.DataFrame(index=demand_df.index, columns=["simulated_mcp"], data=0.0)

for timestep in demand_df.index:
    powerplants["marginal_cost"] = marginal_cost_df.loc[timestep]
    mcp_df.loc[timestep, "simulated_mcp"] = calculate_market_clearing_price(
        powerplants=powerplants,
        demand=demand_df["demand"].at[timestep],
        vre_gen=vre_gen.loc[timestep].sum(),
    )

# %% Plot the merit order curve
powerplants["color"] = powerplants.apply(assign_color, axis=1)

plot_timestep = "2020-05-28 11:00"
powerplants["marginal_cost"] = marginal_cost_df.loc[plot_timestep]
plot_merit_order_curve(
    powerplants,
    mcp_df.loc[plot_timestep, "simulated_mcp"],
    demand_df["demand"].at[plot_timestep],
    vre_gen.loc[plot_timestep].sum(),
)

# %% Load historical data
historical_prices = pd.read_csv(
    "inputs/2020_electricityPrices_GER_1h.csv", index_col=0, parse_dates=True
)
mcp_df["historical_mcp"] = historical_prices["Deutschland [EUR/MWh]"].values
