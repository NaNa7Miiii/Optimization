from gurobipy import *
import pandas as pd

def Scheduler():
    # import the ILS data table
    df = pd.read_excel('GeorgeTown.xlsx')
    # df = df.sort_values('position')  # sort the df table
    print(df)

    # Create the optimization model
    GT_model = Model("GT_model")

    # count the number of servers and kitchen staff
    countServer, countKitchen = 0, 0
    for pos in df['position']:
        if 'Server' in pos:
            countServer += 1
        if 'Kitchen' in pos:
            countKitchen += 1

        # Add decision variables
    listxi, cur = [], []
    for i in range(1, len(df['name']) + 1):
        for j in range(1, 8):
            for k in range(2):
                listxi.append('x' + str(i) + str(j) + str(k))
                cur.append(listxi[-1])
                if (str(j) in df.iloc[i - 1]['AM_not_available']):
                    if k == 0:  # check morning shift
                        listxi[-1] = GT_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=0)
                else:
                    if k == 0:  # check morning shift
                        listxi[-1] = GT_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=1)
                if (str(j) in df.iloc[i - 1]['PM_not_available']):
                    if k == 1:  # check afternoon shift
                        listxi[-1] = GT_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=0)
                else:
                    if k == 1:  # check afternoon shift
                        listxi[-1] = GT_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=1)

    # define Xi from X1 to X7
    # X1 = Yuka, X2 = Jeannie, X3 = Mylinh, X4 = Hayato, X5 = Jonathan, X6 = Shogo, X7 = Yoshi, X8 = JP
    listXi = []
    for i in range(1, len(df['name']) + 1):
        listXi.append('X' + str(i))
        listXi[-1] = GT_model.addVar(name=listXi[-1], vtype=GRB.INTEGER, lb=0)

    # define the objective function and the problem
    # the overall goal is to calculate and minimize the variance of work time for workers in different positions separately
    # obj_fn = variance(servers) + variance(kitchen)
    sum_server, mean_server, sum_kitchen, mean_kitchen = 0, 0, 0, 0
    for i in range(countServer):
        sum_server += listXi[i]
    mean_server = sum_server / countServer
    for i in range(countServer, countKitchen + countServer):
        sum_kitchen += listXi[i]
    mean_kitchen = sum_kitchen / countKitchen
    sum1, var_server = 0, 0
    for i in range(countServer):
        sum1 += (listXi[i] - mean_server) ** 2
    var_server = sum1 / countServer
    sum2, var_kitchen = 0, 0
    for i in range(countServer, countKitchen + countServer):
        sum2 += (listXi[i] - mean_kitchen) ** 2
    var_kitchen = sum2 / countKitchen

    obj_fn = var_server + var_kitchen
    GT_model.setObjective(obj_fn, GRB.MINIMIZE)

    # add the constraints:
    # sum up xis to Xis
    for i in range(countServer+countKitchen):
        GT_model.addConstr(listXi[i] == sum(listxi[i * 14:(i + 1) * 14]))

    # limit on server
    GT_model.addConstr(sum_server == 13)  # the total worktime for servers = 13 shifts
    for i in range(countServer):
        GT_model.addConstr(listXi[i] <= 11)

    print(cur)
    for i in range(14):
        summ = 0
        for j in range(countServer):
            summ += listxi[i + 14 * j]
        if i in [9,13]: # Friday and Sunday dinner need 2 server
            GT_model.addConstr(summ == 2)
        elif i not in [0,1,12]:
            GT_model.addConstr(summ == 1)

    # limit on kitchen:
    GT_model.addConstr(sum_kitchen == 22)
    for i in range(countServer, countServer + countKitchen):
        GT_model.addConstr(listXi[i] <= 11)

    temp = listxi[countServer * 14:]
    for i in range(14):
        sumK = 0
        for j in range(countKitchen):
            sumK += temp[i + 14 * j]
        if i not in [0,1,12]:
            GT_model.addConstr(sumK == 2)

    # initiate the problem solver
    GT_model.optimize()
    for v in GT_model.getVars():
        if v.x != 0:
            print(v.varName, v.x)
    print('Optimal variance:', GT_model.objVal)


    temp, i, cur = listxi[countServer * 14:], 0, cur[countServer * 14:]  # Ex. temp = from x4000, x4001, x4010 to x8501, x8510, x8511
    while i < len(temp):
        if 'cold' in df.iloc[(int(cur[i][1]) - 1)]['weight']:
            GT_model.addConstr(temp[i] >= temp[i + 1])
        elif 'hot' in df.iloc[(int(cur[i][1]) - 1)]['weight']:
            GT_model.addConstr(temp[i] <= temp[i + 1])
        i += 2

    # constraints on the shift limit
    for i in range(len(df['name'])):
        if 'None' not in df.iloc[i]['shift_limit']:
            value = df.iloc[i]['shift_limit'].replace('[', '').replace(']', '').replace(',', '').replace(' ', '')
            if value[0] == 'h':
                GT_model.addConstr(listXi[i] == int(value[1:])) # hard constriant
            elif value[0] == 's':
                GT_model.addConstr(listXi[i] <= int(value[1:])) # soft constraint
Scheduler()