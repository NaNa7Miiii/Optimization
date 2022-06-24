from gurobipy import *
import pandas as pd

def Scheduler():
    # import the ILS data table
    df = pd.read_excel('ILS_Bar.xlsx')
    # df = df.sort_values('position')  # sort the df table
    print(df)

    # Create the optimization model
    ILS_model = Model("ILS_model")

    # Add decision variables
    listxi, cur = [], []
    for i in range(1, len(df['name']) + 1):
        for j in range(1, 8):
            for k in range(2):
                listxi.append('x' + str(i) + str(j) + str(k))
                cur.append(listxi[-1])
                if (str(j) in df.iloc[i - 1]['AM_not_available']):
                    if k == 0:  # check morning shift
                        listxi[-1] = ILS_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=0)
                else:
                    if k == 0:  # check morning shift
                        listxi[-1] = ILS_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=1)
                if (str(j) in df.iloc[i - 1]['PM_not_available']):
                    if k == 1:  # check afternoon shift
                        listxi[-1] = ILS_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=0)
                else:
                    if k == 1:  # check afternoon shift
                        listxi[-1] = ILS_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=1)

    # define Xi from X1 to X7
    listXi = []
    for i in range(1, len(df['name']) + 1):
        listXi.append('X' + str(i))
        listXi[-1] = ILS_model.addVar(name=listXi[-1], vtype=GRB.INTEGER, lb=0)

    # define the objective function and the problem
    # the overall goal is to calculate and minimize the variance of work time for workers in different positions separately
    # obj_fn = var(bar)
    sum_Bar, mean_Bar = 0, 0
    for i in range(len(df['name'])):
        sum_Bar += listXi[i]
    mean_Bar = sum_Bar / len(df['name'])
    sumB, varB = 0, 0
    for i in range(len(df['name'])):
        sumB += (listXi[i] - mean_Bar) ** 2
    varB = sumB / len(df['name'])

    obj_fn = varB
    ILS_model.setObjective(obj_fn, GRB.MINIMIZE)

    # add the constraints:
    # sum up xis to Xis
    # X1 = Luis, X2 = Tae, X3 = Aldo, X4 = Yoshi, X5 = Oscar, X6 = Max, X7 = Miguel(Bar)
    for i in range(len(df['name'])):
        ILS_model.addConstr(listXi[i] == sum(listxi[i * 14:(i + 1) * 14]))

    # limit on Bar
    ILS_model.addConstr(sum_Bar == 46)
    for i in range(len(df['name'])):
        ILS_model.addConstr(listXi[i] <= 11)  # don't have Saturday morning and Sunday
    for i in range(len(df['name'])):
        ILS_model.addConstr(listXi[i] >= listXi[6]) # Bar

    for i in range(14):
        summ = 0
        for j in range(len(df['name'])):
            summ += listxi[i + 14 * j]
        if i in [8, 9]:  # Friday need 5 sushi bar staff
            ILS_model.addConstr(summ == 5)
        elif i not in [10, 12, 13]:
            ILS_model.addConstr(summ == 4)

    # initiate the problem solver
    ILS_model.optimize()
    for v in ILS_model.getVars():
        if v.x != 0:
            print(v.varName, v.x)
    print('Optimal variance:', ILS_model.objVal)
Scheduler()