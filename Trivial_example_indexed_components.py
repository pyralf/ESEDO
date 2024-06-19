# -*- coding: utf-8 -*-
"""
Created on Mon Jun 10 09:22:08 2024

@author: adiaz
"""

import pyomo.environ as pyo


# 24 hours a day
time_set = set(range(0,24))

# 12 powerplants
power_plants_set = set(range(1,13))

model = pyo.ConcreteModel()

model.power_output = pyo.Var(power_plants_set, time_set, domain=pyo.NonNegativeReals)

# Indexed constraints
def example_rule(m, pp, t):
    return m.power_output[pp,t] <= 100

model.pp_limit = pyo.Constraint(power_plants_set, time_set, rule=example_rule)

def rule_objective(m):
    return pyo.quicksum(m.power_output[pp,t] for pp in power_plants_set for t in time_set)

model.objective = pyo.Objective(rule=rule_objective, sense=pyo.maximize)

opt = pyo.SolverFactory('glpk')
opt.solve(model)

for v in model.component_data_objects([pyo.Var, pyo.Objective], active=True):
    print(v, '=', pyo.value(v))
    
    
    
    
    
    
    
    
    