from gurobipy import *
import pandas as pd
import matplotlib.pyplot as plt

def Scheduler():
    # import the ILS data table
    df = pd.read_excel('ILS_front.xlsx')
    # df = df.sort_values('position')  # sort the df table
    print(df)

    # Create the optimization model
    ILS_model = Model("ILS_model")

    # count the number of servers and hosts
    countServer, countHost = 0, 0
    for pos in df['position']:
        if 'SRV' in pos:
            countServer += 1
        if 'Host' in pos:
            countHost += 1
    # print(countServer)

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
                    if k == 1: # check afternoon shift
                        listxi[-1] = ILS_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=0)
                else:
                    if k == 1: # check afternoon shift
                        listxi[-1] = ILS_model.addVar(name=listxi[-1], vtype=GRB.INTEGER, lb=0, ub=1)

    # define Xi from X1 to X9
    listXi = []
    for i in range(1, len(df['name']) + 1):
        listXi.append('X' + str(i))
        listXi[-1] = ILS_model.addVar(name=listXi[-1], vtype=GRB.INTEGER, lb=0)

    # define the objective function and the problem
    # the overall goal is to calculate and minimize the variance of work time for workers in different positions separately
    # obj_fn = variance(servers) + variance(host)
    sum_server, mean_server, sum_host, mean_host = 0, 0, 0, 0
    for i in range(countServer):
        sum_server += listXi[i]
    mean_server = sum_server / countServer
    for i in range(countServer, countHost + countServer):
        sum_host += listXi[i]
    mean_host = sum_host / countHost

    sum1, var_server = 0, 0
    for i in range(countServer):
        sum1 += (listXi[i] - mean_server) ** 2
    var_server = sum1 / countServer
    sum2, var_host = 0, 0
    for i in range(countServer, countHost + countServer):
        sum2 += (listXi[i] - mean_host) ** 2
    var_host = sum2 / countHost

    obj_fn = var_server + var_host
    ILS_model.setObjective(obj_fn, GRB.MINIMIZE)

    # add the constraints:
    # sum up xis to Xis
    # X1 = Kate, X2 = Amy, X3 = Everest, X4 = Sara, X5 = Carlo, X6 = Yuka;
    # X7 = Jay, X8 = Yuka(host), X9 = Amy(host)
    # Amy and Yuka prefers to do server than to do host
    for i in range(countServer + countHost):
        ILS_model.addConstr(listXi[i] == sum(listxi[i * 14:(i + 1) * 14]))
    for i in range(14):
        if i not in [10,12,13]:
            ILS_model.addConstr(listxi[14+i] + listxi[14*8+i] <= 1)
            ILS_model.addConstr(listxi[14*5+i] + listxi[14*7+i] <= 1)

    # limit on server
    ILS_model.addConstr(sum_server == 24)  # the total worktime for servers = 24 shifts
    for i in range(countServer):
        ILS_model.addConstr(listXi[i] <= 11)  # don't have Saturday morning and Sunday

    for i in range(14):
        summ = 0
        for j in range(countServer):
            summ += listxi[i + 14 * j]
        if i in [9,11]: # Friday and Saturday night need 3 server
            ILS_model.addConstr(summ == 3)  # friday afternoon one more person
        elif i not in [10,12,13]:
            ILS_model.addConstr(summ == 2)


    # constraints on the shift limit
    for i in range(len(df['name'])):
        if 'None' not in df.iloc[i]['shift_limit']:
            value = df.iloc[i]['shift_limit'].replace('[', '').replace(']', '').replace(',', '').replace(' ', '')
            if value[0] == 'h':
                ILS_model.addConstr(listXi[i] == int(value[1:])) # hard constriant
            elif value[0] == 's':
                ILS_model.addConstr(listXi[i] <= int(value[1:])) # soft constraint

    # limit on host:
    ILS_model.addConstr(sum_host == 14)
    for i in range(countServer, countServer + countHost):
        ILS_model.addConstr(listXi[i] <= 11)
    for i in range(countServer+1, countServer + countHost):
        ILS_model.addConstr(listXi[i] <= listXi[countServer])
    ILS_model.addConstr(listXi[1] + listXi[8] <= 10) # for Amy


    temp = listxi[countServer * 14:]
    for i in range(14):
        sumK = 0
        for j in range(countHost):
            sumK += temp[i + 14 * j]
        if i in [8,9,11]: # Friday morning, Friday afternoon, and Saturday afternoon
            ILS_model.addConstr(sumK == 2)
        elif i not in [10,12,13]:
            ILS_model.addConstr(sumK == 1)

    # initiate the problem solver
    res = []
    ILS_model.optimize()
    for v in ILS_model.getVars():
        if v.varName[0] == 'X':
            res.append(v.x)
        if v.x != 0:
            print(v.varName, v.x)

    print('Optimal variance:', ILS_model.objVal)

    # # try the histogram
    # plt.hist(res, density=True, bins=30)
    # plt.ylabel('Density')
    # plt.xlabel('work time')
    # plt.show()

Scheduler()

