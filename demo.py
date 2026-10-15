from core import plan_week, DEFAULT_PANTRY

r=plan_week(30000,meal_count=5,household=1,pantry_groups=DEFAULT_PANTRY,
            min_kcal=400,max_kcal=850,min_protein=15,max_sodium=2000)
if not r:
    print('조건을 만족하는 계획이 없습니다.')
else:
    print('optimizer:',r['optimizer'],'candidates:',r['candidate_count'])
    print('cost:',round(r['total_cost']),'within:',r['within_budget'])
    for i,m in enumerate(r['selected'],1):
        print(i,m['meal_name'],round(m['kcal'],1),round(m['protein_g'],1),round(m['sodium_mg'],1))
    print(r['shopping'].to_string(index=False))
