from gurobipy import *
import pandas as pd

def Scheduler():
    # import the ILS data table
    df = pd.read_excel('ILS_Other.xlsx')
    # df = df.sort_values('position')  # sort the df table
    print(df)

    # Create the optimization model
    ILS_model = Model("ILS_model")

    # count the number of people in different positions
    countStov, countTick, countDish = 0, 0, 0
    for pos in df['position']:
        if 'Stove' in pos:
            countStov += 1
        if 'Ticket' in pos:
            countTick += 1
        if 'DishWasher' in pos:
            countDish += 1

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
    # obj_fn = var(Stove) + var(Ticket) + var(DishWasher)
    sumStov, sumTick, sumDish = 0, 0, 0
    meanStov, meanTick, meanDish = 0, 0, 0
    for i in range(countStov):
        sumStov += listXi[i]
    meanStov = sumStov / countStov
    for i in range(countStov, countStov+countTick):
        sumTick += listXi[i]
    meanTick = sumTick / countTick
    for i in range(countStov+countTick, countStov+countTick+countDish):
        sumDish += listXi[i]
    meanDish = sumDish / countDish

    sum1, varS = 0, 0
    for i in range(countStov):
        sum1 += (listXi[i] - meanStov) ** 2
    varS = sum1 / countStov
    sum2, varT = 0, 0
    for i in range(countStov, countStov + countTick):
        sum2 += (listXi[i] - meanTick) ** 2
    varT = sum2 / countTick
    sum3, varD = 0, 0
    for i in range(countStov + countTick, countStov + countTick + countDish):
        sum3 += (listXi[i] - meanDish) ** 2
    varD = sum3 / countDish

    obj_fn = varS + varT + varD
    ILS_model.setObjective(obj_fn, GRB.MINIMIZE)

    # add the constraints:
    # sum up xis to Xis
    # X1 = Harry, X2 = Miguel(Stove), X3 = Miguel(Ticket), X4 = Roberto, X5 = Macro
    # X6 = Ruth, X7 = Ben
    for i in range(len(df['name'])):
        ILS_model.addConstr(listXi[i] == sum(listxi[i * 14:(i + 1) * 14]))
    for i in range(14):
        if i not in [10, 12, 13]:
            ILS_model.addConstr(listxi[14 * 1 + i] + listxi[14 * 2 + i] <= 1)  # Miguel

    # limit on Stove
    ILS_model.addConstr(sumStov == 11)
    for i in range(countStov):
        ILS_model.addConstr(listXi[i] <= 11)
    # Miguel's priority
    ILS_model.addConstr(listXi[2] >= listXi[1]) # Ticket > Stove

    for i in range(14):
        summ = 0
        for j in range(countStov):
            summ += listxi[i + 14 * j]
        if i not in [10,12,13]:
            ILS_model.addConstr(summ == 1)

    # limit on Ticket
    ILS_model.addConstr(sumTick == 11)
    for i in range(countStov, countStov + countTick):
        ILS_model.addConstr(listXi[i] <= 11)
    temp = listxi[countStov * 14:]
    for i in range(14):
        summ = 0
        for j in range(countTick):
            summ += temp[i + 14 * j]
        if i not in [10,12,13]:
            ILS_model.addConstr(summ == 1)

    # limit on Dishwasher
    ILS_model.addConstr(sumDish == 11)
    for i in range(countStov + countTick, countStov + countTick + countDish):
        ILS_model.addConstr(listXi[i] <= 11)
    temp = listxi[(countStov+countTick) * 14:]
    for i in range(14):
        summ = 0
        for j in range(countDish):
            summ += temp[i + 14 * j]
        if i not in [10, 12, 13]:
            ILS_model.addConstr(summ == 1)

    # initiate the problem solver
    ILS_model.optimize()
    for v in ILS_model.getVars():
        if v.x != 0:
            print(v.varName, v.x)
    print('Optimal variance:', ILS_model.objVal)

Scheduler()