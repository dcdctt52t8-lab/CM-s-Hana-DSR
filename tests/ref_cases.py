# 부동산계산기.com / 금융위 DSR 산정 기준을 독립 구현한 기준값 생성기
import json, random
random.seed(20261030)

def pmt(rate, years, pv):
    r = rate/100/12; n = max(1, round(years*12))
    if r < 1e-12: return pv/n
    return pv*r*(1+r)**n/((1+r)**n-1)

def first_year(rate, years, amt, repay):
    """향후 1년간 DSR 산입 상환액"""
    if repay == 'equal':
        return pmt(rate, years, amt)*12
    if repay == 'principal':           # 원금균등: 12개월 실제 상환액을 월별로 합산
        n = max(1, round(years*12)); r = rate/100/12; bal = amt; tot = 0
        for _ in range(min(12, n)):
            prin = amt/n; tot += prin + bal*r; bal -= prin
        return tot
    if repay == 'bullet':              # 원금 ÷ min(만기,10년) + 이자
        return amt/min(max(years,0.5),10) + amt*rate/100
    return amt*rate/100                # 체증식: 초회 이자

def loan(l):
    a, r, t = l['amt'], l['rate'], l['term']; i = a*r/100
    if l['type'] == 'mn':  return a/5 + i, i
    if l['type'] == 'mid': return a/25 + i, a/25 + i
    if l['type'] == 'cr':
        if l['repay'] == 'bullet': return a/5 + i, i
        return pmt(r, min(max(t,0.5),10), a)*12, i
    if l['type'] == 'cd':  return pmt(r, max(t,0.5), a)*12, i
    v = first_year(r, max(t,0.5), a, l['repay']); return v, v   # 주담대

STYPE = {'수도권·규제 변동':(3,1),'수도권·규제 혼합':(3,.8),'수도권·규제 주기형':(3,.4),'수도권·규제 고정':(0,0),
         '지방 변동':(.75,1),'지방 혼합':(.75,.8),'지방 주기형':(.75,.4),'지방 고정':(0,0)}
cases = []
for k in range(50):
    c = dict(income=random.randrange(2000, 25001, 100), itype=random.choice(['1.00','0.90','0.60','0.50']),
             dsrlim=random.choice(['40','50','60']), term=random.randint(5,40),
             rate=round(random.randrange(200, 801, 5)/100, 2), repay=random.choice(['equal','principal','bullet','deferred']),
             stype=random.choice(list(STYPE)), amt=random.randrange(5000, 150001, 1000), loans=[])
    for _ in range(random.randint(0,3)):
        t = random.choice(['jd','cr','mn','cd','mid'])
        L = dict(type=t, amt=random.randrange(300, 40001, 100), rate=round(random.uniform(2,16),1),
                 term=random.choice([1,2,3,5,7,10,15,20,30]), repay='equal')
        if t == 'jd': L['repay'] = random.choice(['equal','principal','bullet'])
        if t == 'cr': L['repay'] = random.choice(['equal','bullet'])
        c['loans'].append(L)
    # 기준값
    inc = c['income']*float(c['itype']); sb, sm = STYPE[c['stype']]; st = round(sb*sm, 3)
    eD = sum(loan(l)[0] for l in c['loans']); eT = sum(loan(l)[1] for l in c['loans'])
    nD = first_year(c['rate']+st, c['term'], c['amt'], c['repay'])
    nT = first_year(c['rate'], c['term'], c['amt'], c['repay'])
    budget = inc*int(c['dsrlim'])/100
    unit = first_year(c['rate']+st, c['term'], 1, c['repay'])
    c['expect'] = dict(dsr=(nD+eD)/inc*100, dti=(nT+eT)/inc*100,
                       maxLoan=max(0, budget-eD)/unit)
    cases.append(c)
json.dump(cases, open(__import__('sys').argv[1],'w'), ensure_ascii=False)
print(len(cases), 'cases')
