# ESEDO
 Energy System Economic Dispatch with Optimization

## Problems with original scope of assignment

### Added printout of solver results

~~~ Python
# defining solver
    opt = pyo.SolverFactory('glpk')
    results = opt.solve(model)
    print(results)
    print("Print in For loop:\n")
    for v in model.component_data_objects([pyo.Var, pyo.Objective], active=True):
        print(v, '=', pyo.value(v))
~~~

### Output of *print(results)* statement

> **NOTE:** Termination condition: infeasible
~~~ 
Problem: 
- Name: unknown
  Lower bound: -inf
  Upper bound: inf
  Number of objectives: 1
  Number of constraints: 246
  Number of variables: 245
  Number of nonzeros: 490
  Sense: minimize
Solver: 
- Status: ok
  Termination condition: infeasible
  Statistics: 
    Branch and bound: 
      Number of bounded subproblems: 0
~~~ 
