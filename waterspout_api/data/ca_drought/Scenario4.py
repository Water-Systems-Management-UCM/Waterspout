# -*- coding: utf-8 -*-
"""
Created on Thu Mar 31 13:21:27 2022

@author: spenc
"""

import numpy as np
from pyomo.environ import *
from pyomo.opt import SolverStatus, TerminationCondition

def Scenario(dataframe, water_shortage,shortage_type, initial, iterations, tolerance,drought_report=None):
    
    #  Define list of crops
    N = list(range(len(dataframe)))
    
    #  Define dictionary of crops
    A = dict(zip(N, dataframe.crop.values.tolist()))
    
    #  Define dictionary of regions
    B = dict(zip(N, dataframe.region.values.tolist()))
    
    #  Define dictionary of basins
    C = dict(zip(N, dataframe.basin.values.tolist()))
    
    #  Define function to find dataframe index (k value in N) relating to multiple conditions based on dictionaries defined previously (e.g. A, B,C, D)
    def FindInd(a, b, c, A, B, C):
        inds = []
        for q, z in zip([a, b, c], [A, B, C]):
            inds_sub = []
            if q != None:
                for index, value in z.items():
                    if value == q:
                        inds_sub.append(index)
                inds.append(inds_sub)
        return list(set.intersection(*map(set, inds)))[0]
    
    #  Calculate percentage water shortage in scenario to use in setting initial conditions
    percent = water_shortage/(dataframe.xland*dataframe.xwater_unit).sum()
    if initial==False:
        guess_land = dict(zip(N, [(1-percent)*value for value in dataframe.xland.values.tolist()]))
        guess_water = dict(zip(N, [(1-percent)*value for value in (dataframe.xland*dataframe.xwater_unit).values.tolist()]))
    else:
        guess_land = dict(zip(N, [(1+np.random.uniform(low=initial[0], high=initial[1]))*(1-percent)*value for value in dataframe.xland.values.tolist()]))
        guess_water = dict(zip(N, [(1+np.random.uniform(low=initial[0], high=initial[1]))*(1-percent)*value for value in (dataframe.xland*dataframe.xwater_unit).values.tolist()]))    
    
    #  Define model and decision variables
    ScarcityModel = ConcreteModel()
    ScarcityModel.xlandsc = Var(N, within=NonNegativeReals, initialize=guess_land)
    ScarcityModel.xwatersc = Var(N, within=NonNegativeReals, initialize=guess_water)
    
    #  Define objective function
    ScarcityModel.Obj = Objective(expr=sum(dataframe.p[k]*dataframe.tau[k]*(dataframe.betaland[k]*(ScarcityModel.xlandsc[k])**dataframe.rho[k]+
        dataframe.betawater[k]*ScarcityModel.xwatersc[k]**dataframe.rho[k]+
        dataframe.betasupplies[k]*(ScarcityModel.xlandsc[k])**dataframe.rho[k]+ dataframe.betalabor[k]*(ScarcityModel.xlandsc[k])**dataframe.rho[k] )**(1/dataframe.rho[k])-dataframe.delta[k]*exp(dataframe.gamma[k]*ScarcityModel.xlandsc[k])-
    dataframe.omegawater_unit[k]*ScarcityModel.xwatersc[k]-dataframe.omegasupplies[k]*ScarcityModel.xlandsc[k]--dataframe.omegalabor[k]*ScarcityModel.xlandsc[k] for k in N), sense=maximize)
    
    #  Define general water constraint; correct if shortage is greater than demand
    
    if shortage_type == 'percent':
    	ScarcityModel.WaterCon = Constraint(expr=sum(ScarcityModel.xwatersc[k] for k in N) <= (dataframe.xland*dataframe.xwater_unit).sum()*water_shortage)
    else:
    	ScarcityModel.WaterCon = Constraint(expr=sum(ScarcityModel.xwatersc[k] for k in N) <= (dataframe.xland*dataframe.xwater_unit).sum()-water_shortage)
    
    #  Define general land constraint
    ScarcityModel.LandCon = Constraint(expr=sum(ScarcityModel.xlandsc[k] for k in N) <= dataframe.xland.sum())
    
    #  Define deficit irrigation constraints for individual crops
    ScarcityModel.DefIrrigCon = ConstraintList()
    [ScarcityModel.DefIrrigCon.add(expr=(ScarcityModel.xwatersc[k]/ScarcityModel.xlandsc[k]) >= 0.9975*dataframe.xwater_unit[k]) for k in N]
    
    #  Define expansion constraints for individual crops
    ScarcityModel.ExpanCon = ConstraintList()
    [ScarcityModel.ExpanCon.add(expr=(ScarcityModel.xlandsc[k]/dataframe.xland[k]) <= 1.01) for k in N]
    
    if drought_report == True:
    
    	#  Define crop specific fallowing constraints based on ET results
    	ScarcityModel.FallowCon = ConstraintList()
    	crops = ['Pasture']
    	region_map = dataframe[['region', 'crop']].drop_duplicates()
    	region_map = region_map[region_map.crop.isin(crops)]
    	for crop, region in zip(region_map.crop, region_map.region,):
	     if region=='CLS02-North-WAs':
	        continue
	     ind = FindInd(a=crop, b=region, c=None, A=A, B=B, C=None)
	     ScarcityModel.FallowCon.add(expr=(ScarcityModel.xlandsc[ind] >= dataframe.xland[ind]-1.05*dataframe.fallow_net[ind]))
	     
	     ScarcityModel.FallowCon.add(expr=(ScarcityModel.xlandsc[ind] <= dataframe.xland[ind]-0.95*dataframe.fallow_net[ind]))
                 
    #  Set solver and iteration parameters
    Opt = SolverFactory('ipopt')  # Solve using "ipopt" solver
    Opt.options['max_iter'] = iterations  # Increase maximum number of iterations (default is 3000)
    Opt.options['tol'] = tolerance
    
    #  Take duals during optimization
    ScarcityModel.dual = Suffix(direction=Suffix.IMPORT_EXPORT)
    
    #  Try solving model, if there is an error continue after except statement
    try:
        ScarcityModelResults = Opt.solve(ScarcityModel, tee=False)
        ScarcityModel.solutions.load_from(ScarcityModelResults)
        ScarcityModelResults = Opt.solve(ScarcityModel)  # Obtain results
        if (ScarcityModelResults.solver.status == SolverStatus.ok) and (ScarcityModelResults.solver.termination_condition == TerminationCondition.optimal):
            print('\nModel solved successfully!')
            ScarcityModel.solutions.load_from(ScarcityModelResults)  # Load results
            lambdas = [ScarcityModel.dual[getattr(ScarcityModel, str(d))[index]] for d in ScarcityModel.component_objects(Constraint, active=True) for index in getattr(ScarcityModel, str(d))]  # Store Lagrange values for water to a list
            lambdawater = lambdas[0]
            dataframe['xlandsc'] = [ScarcityModel.xlandsc[k].value for k in N]  # Pass model allocations
            dataframe['xwatersc'] = [ScarcityModel.xwatersc[k].value for k in N]  # Pass model allocations
            status = 'Good'
        else:
            print('\nError in solver status or termination condition. EXITING.')
            lambdas = ['N/A']
            lambdawater = 'N/A'
            dataframe['xlandsc'] = [ScarcityModel.xlandsc[k].value for k in N]  # Pass model allocations
            dataframe['xwatersc'] = [ScarcityModel.xwatersc[k].value for k in N]  # Pass model allocations
            status = 'Non-optimal'
    except:
        print('\nOther error condition encountered. EXITING.')
        lambdas = ['N/A']
        lambdawater = 'N/A'
        dataframe['xlandsc'] = dataframe.xland  # Pass calibration land allocation values
        dataframe['xwatersc'] = dataframe.xland*dataframe.xwater_unit  # Pass calibration water use values
        status = 'Infeasible'
    
    #  Calculate results such as total water use, gross revenues, and obtain Lagrange for water
    dataframe['xwater'] = dataframe.xland*dataframe.xwater_unit  # Add base water use
    dataframe['grev'] = dataframe.xland*dataframe.p*dataframe.y  # Add base gross revenue
    dataframe['grevsc'] = dataframe.xlandsc*dataframe.p*dataframe.y  # Add scenario gross revenue
    dataframe['lambdawater'] = lambdawater  # Add lagrange for water
    dataframe['statussc'] = status  # Add status of solver at time of exit
    dataframe['difflandsc'] = abs(dataframe.xland-dataframe.xlandsc)
    dataframe['percdifflandsc'] = dataframe.difflandsc/dataframe.xland
    return dataframe
    
 
