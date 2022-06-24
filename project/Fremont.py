from gurobipy import *
import pandas as pd

def Scheduler():
    # import the ILS data table
    df = pd.read_excel('Fremont.xlsx')
    # df = df.sort_values('position')  # sort the df table
    print(df)

    # Create the optimization model
    Fremont_model = Model("Fremont_model")

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
                        listxi[-1] = Fremont_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=0)
                else:
                    if k == 0:  # check morning shift
                        listxi[-1] = Fremont_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=1)
                if (str(j) in df.iloc[i - 1]['PM_not_available']):
                    if k == 1:  # check afternoon shift
                        listxi[-1] = Fremont_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=0)
                else:
                    if k == 1:  # check afternoon shift
                        listxi[-1] = Fremont_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=1)

    # define Xi from X1 to X12
    # X1 = Mara, X2 = Alair, X3 = Yuka, X4 = Arthur, X5 = Mila, X6 = Michelle, X7 = Shogo； X8 = Kato, X9 = Eusebio
    # X10 = Miguel, X11 = Kevin, X12 = Shogo(kitchen)
    listXi = []
    for i in range(1, len(df['name']) + 1):
        listXi.append('X' + str(i))
        listXi[-1] = Fremont_model.addVar(name=listXi[-1], vtype=GRB.INTEGER, lb=0)

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
    Fremont_model.setObjective(obj_fn, GRB.MINIMIZE)

    # add the constraints:
    # sum up xis to Xis
    for i in range(countServer+countKitchen):
        Fremont_model.addConstr(listXi[i] == sum(listxi[i * 14:(i + 1) * 14]))

    # limit on server
    Fremont_model.addConstr(sum_server == 25)  # the total worktime for servers = 25 shifts
    for i in range(countServer):
        Fremont_model.addConstr(listXi[i] <= 12)  # don't have monday shifts
    for i in range(countServer-1):
        if i not in [4,5]:
            Fremont_model.addConstr(listXi[i] >= listXi[countServer-1])
    for i in range(14):
        if i not in [0,1]:
            Fremont_model.addConstr(listxi[14*6 + i] + listxi[14*11 + i] <= 1)

    for i in range(14):
        summ = 0
        for j in range(countServer):
            summ += listxi[i + 14 * j]
        if i == 13: # Sunday night need 3 server
            Fremont_model.addConstr(summ == 3)
        elif i not in [0, 1]:
            Fremont_model.addConstr(summ == 2)

    # constraints on the shift limit
    for i in range(len(df['name'])):
        if 'None' not in df.iloc[i]['shift_limit']:
            value = df.iloc[i]['shift_limit'].replace('[', '').replace(']', '').replace(',', '').replace(' ', '')
            if value[0] == 'h':
                Fremont_model.addConstr(listXi[i] == int(value[1:])) # hard constriant
            elif value[0] == 's':
                Fremont_model.addConstr(listXi[i] <= int(value[1:])) # soft constraint

    # limit on kitchen:
    Fremont_model.addConstr(sum_kitchen==41)
    for i in range(countServer, countServer + countKitchen):
        Fremont_model.addConstr(listXi[i] <= 12)
    temp = listxi[countServer * 14:]
    for i in range(14):
        sumK = 0
        for j in range(countKitchen):
            sumK += temp[i + 14 * j]
        if i in [2, 3, 4, 10, 11]:
            Fremont_model.addConstr(sumK == 4)
        elif i not in [0, 1]:
            Fremont_model.addConstr(sumK == 3)

    # initiate the problem solver
    Fremont_model.optimize()
    for v in Fremont_model.getVars():
        if v.x != 0:
            print(v.varName, v.x)
    print('Optimal variance:', Fremont_model.objVal)

Scheduler()