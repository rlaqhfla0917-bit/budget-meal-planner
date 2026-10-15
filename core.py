from pathlib import Path
import json, math
import numpy as np
import pandas as pd
from scipy.optimize import milp, LinearConstraint, Bounds
from scipy.sparse import lil_matrix, vstack, csr_matrix

BASE = Path(__file__).resolve().parent
DATA = BASE / 'data'
_CACHE = {}

DEFAULT_PANTRY = ['쌀','간장','마늘','설탕','소금','식용유','참기름','고추장','된장','물엿','고춧가루','조리수']


def load_data():
    if 'data' not in _CACHE:
        pool = pd.read_csv(DATA/'strict_menu_pool.csv')
        ing = pd.read_csv(DATA/'menu_ingredients_strict.csv')
        prices = pd.read_csv(DATA/'price_catalog_strict.csv')
        options = pd.read_csv(DATA/'meal_options_strict.csv')
        audit = json.loads((DATA/'audit_summary.json').read_text(encoding='utf-8'))
        pmeta = prices.set_index('price_key').to_dict('index')
        _CACHE['data']=(pool,ing,prices,options,audit,pmeta)
    return _CACHE['data']


def _eligible_dishes(ing, pantry_groups):
    pantry=set(pantry_groups or [])
    ok={}
    for code,g in ing.groupby('음식코드'):
        valid=True
        for _,r in g.iterrows():
            pg = '' if pd.isna(r.get('pantry_group')) else str(r.get('pantry_group'))
            grade = '' if pd.isna(r.get('map_grade')) else str(r.get('map_grade'))
            if pg and pg in pantry:
                continue
            if grade == 'R':
                continue
            if grade != 'A' or pd.isna(r.get('price_key')) or str(r.get('price_key')) == '':
                valid=False
                break
        ok[str(code)] = valid
    return ok


def _dish_requirements(ing, pantry_groups):
    pantry=set(pantry_groups or [])
    req={}
    for code,g in ing.groupby('음식코드'):
        d={}
        for _,r in g.iterrows():
            pg = '' if pd.isna(r.get('pantry_group')) else str(r.get('pantry_group'))
            grade = '' if pd.isna(r.get('map_grade')) else str(r.get('map_grade'))
            if pg and pg in pantry:
                continue
            if grade == 'R':
                continue
            if grade == 'A' and pd.notna(r.get('price_key')) and str(r.get('price_key')):
                k=str(r['price_key'])
                d[k]=d.get(k,0.0)+float(r['purchase_g'])
        req[str(code)]=d
    return req


def _merge_req(dicts, household=1):
    out={}
    for d in dicts:
        for k,v in d.items():
            out[k]=out.get(k,0.0)+float(v)*household
    return out


def _cost_from_req(req, pmeta):
    total=0.0
    rows=[]
    for k,needed in req.items():
        m=pmeta[k]
        needed=float(needed)
        if m['purchase_mode']=='package':
            pg=float(m['package_g']); pp=float(m['package_price'])
            packs=int(math.ceil(needed/pg)) if needed>0 else 0
            buy_g=packs*pg
            cost=packs*pp
            leftover=max(0.0,buy_g-needed)
            mode='실제 포장규격'
        else:
            packs=np.nan
            buy_g=needed
            cost=needed*float(m['won_per_g'])
            leftover=np.nan
            mode='KAMIS 중량단가'
        total += cost
        rows.append({
            'price_key':k,'품목':m['display_name'],'필요량_g':round(needed,1),
            '구매량_g':round(buy_g,1),'구매팩수':packs,'예상비용_원':round(cost),
            '잔여량_g': None if pd.isna(leftover) else round(leftover,1),
            '계산방식':mode,'가격원':m['source'],'가격근거':m['reference']
        })
    df=pd.DataFrame(rows)
    if not df.empty:
        df=df.sort_values('예상비용_원',ascending=False).reset_index(drop=True)
    return total,df


def _candidate_requirements(opts, dish_req, household):
    reqs=[]
    proxy=[]
    _,_,_,_,_,pmeta=load_data()
    for r in opts.itertuples(index=False):
        ds=[dish_req[str(r.code1)],dish_req[str(r.code2)],dish_req[str(r.code3)],dish_req[str(r.code4)]]
        q=_merge_req(ds,household)
        reqs.append(q)
        c=0.0
        for k,v in q.items():
            c += float(v)*float(pmeta[k]['won_per_g'])
        proxy.append(c)
    return reqs,np.array(proxy,dtype=float)


def _solve_milp(opts, reqs, budget, meal_count, pmeta, enforce_budget=True, max_repeat=2):
    n=len(opts)
    package_keys=sorted({k for q in reqs for k in q if pmeta[k]['purchase_mode']=='package'})
    p_index={k:i for i,k in enumerate(package_keys)}
    m=len(package_keys)
    N=n+m

    # Objective: purchase cost + small leftover-value penalty for package items.
    c=np.zeros(N,dtype=float)
    for j,q in enumerate(reqs):
        weight_cost=0.0
        package_used_value=0.0
        for k,v in q.items():
            meta=pmeta[k]
            if meta['purchase_mode']=='package':
                package_used_value += float(v)*float(meta['won_per_g'])
            else:
                weight_cost += float(v)*float(meta['won_per_g'])
        c[j]=weight_cost - 0.15*package_used_value
    for k,i in p_index.items():
        c[n+i]=float(pmeta[k]['package_price'])*1.15

    integrality=np.ones(N,dtype=int)
    lb=np.zeros(N); ub=np.full(N,np.inf)
    ub[:n]=1
    # package count upper bounds: generous but finite
    ub[n:]=30
    bounds=Bounds(lb,ub)

    rows=[]; lows=[]; highs=[]
    # Exactly meal_count options
    a=np.zeros(N); a[:n]=1
    rows.append(a); lows.append(meal_count); highs.append(meal_count)

    # Package requirement constraints sum(req*x) <= package_g*y
    for k,i in p_index.items():
        a=np.zeros(N)
        for j,q in enumerate(reqs):
            a[j]=q.get(k,0.0)
        a[n+i]=-float(pmeta[k]['package_g'])
        rows.append(a); lows.append(-np.inf); highs.append(0.0)

    # Repetition limits by actual dish code.
    role_cols=['code1','code2','code3','code4']
    # The strict MVP includes only three distinct side dishes. A hard
    # maximum of two repeats makes a seven-meal request impossible
    # (3 dishes * 2 repeats = 6). Relax only as much as necessary.
    role_limits = {
        col: max(2, math.ceil(meal_count / max(1, opts[col].astype(str).nunique())))
        for col in role_cols
    }
    for col in role_cols:
        for code in opts[col].astype(str).unique():
            a=np.zeros(N)
            a[:n]=(opts[col].astype(str).values==code).astype(float)
            rows.append(a); lows.append(-np.inf); highs.append(role_limits[col])

    # Budget uses actual purchase model.
    if enforce_budget:
        a=np.zeros(N)
        for j,q in enumerate(reqs):
            wc=0.0
            for k,v in q.items():
                meta=pmeta[k]
                if meta['purchase_mode']!='package':
                    wc += float(v)*float(meta['won_per_g'])
            a[j]=wc
        for k,i in p_index.items():
            a[n+i]=float(pmeta[k]['package_price'])
        rows.append(a); lows.append(-np.inf); highs.append(float(budget))

    A=csr_matrix(np.vstack(rows))
    cons=LinearConstraint(A,np.array(lows),np.array(highs))
    res=milp(c,integrality=integrality,bounds=bounds,constraints=cons,
             options={'time_limit':10.0,'mip_rel_gap':0.0,'presolve':True})
    return res, package_keys


def plan_week(budget, meal_count=5, household=1, pantry_groups=None,
              min_kcal=400, max_kcal=850, min_protein=15, max_sodium=2000):
    pool,ing,prices,options,audit,pmeta=load_data()
    pantry_groups = DEFAULT_PANTRY if pantry_groups is None else pantry_groups
    elig=_eligible_dishes(ing,pantry_groups)
    dish_req=_dish_requirements(ing,pantry_groups)

    # Invalid/empty filter combinations must never break the UI.
    if (not isinstance(meal_count, int) or meal_count < 1 or
            not isinstance(household, int) or household < 1 or
            not np.isfinite(budget) or budget < 0 or
            min_kcal > max_kcal):
        raise ValueError('예산, 끼니 수, 인원 수 또는 영양 범위를 확인해주세요.')

    o=options.loc[
        options['kcal'].between(min_kcal,max_kcal)
        & (options['protein_g']>=min_protein)
        & (options['sodium_mg']<=max_sodium)
    ].copy()
    for c in ['code1','code2','code3','code4']:
        if o.empty:
            return None
        # An empty pandas Series may have object dtype and be mistaken
        # for column labels in df[mask]. Explicit .loc[boolean] fixes it.
        mask=o[c].astype(str).map(elig).fillna(False).astype(bool)
        o=o.loc[mask].copy()
    if o.empty:
        return None

    reqs,proxy=_candidate_requirements(o,dish_req,household)
    o=o.assign(_proxy=proxy)
    # deterministic candidate cap for fast MILP; keep low-cost candidates across main/side pairs
    o=o.sort_values('_proxy')
    keep=[]; pair_counts={}
    for idx,r in o.iterrows():
        pair=(str(r['code3']),str(r['code4']))
        if pair_counts.get(pair,0)<50:
            keep.append(idx); pair_counts[pair]=pair_counts.get(pair,0)+1
        if len(keep)>=1400: break
    o=o.loc[keep].reset_index(drop=True)
    reqs,_=_candidate_requirements(o,dish_req,household)

    res,pkeys=_solve_milp(o,reqs,budget,meal_count,pmeta,enforce_budget=True)
    within=True
    if not res.success:
        res,pkeys=_solve_milp(o,reqs,budget,meal_count,pmeta,enforce_budget=False)
        within=False
        if not res.success:
            return None

    x=res.x[:len(o)]
    chosen=np.where(x>0.5)[0].tolist()
    selected=[]; total_req={}
    for j in chosen:
        row=o.iloc[j].to_dict()
        row.pop('_proxy',None)
        selected.append(row)
        for k,v in reqs[j].items():
            total_req[k]=total_req.get(k,0.0)+v
    total,shopping=_cost_from_req(total_req,pmeta)
    within=bool(total<=budget+1e-6)

    # Package leftover value only where actual package size exists.
    leftover_value=0.0
    if not shopping.empty:
        for _,r in shopping.iterrows():
            if pd.notna(r['잔여량_g']):
                leftover_value += float(r['잔여량_g'])*float(pmeta[r['price_key']]['won_per_g'])

    return {
        'selected':selected,'shopping':shopping,'total_cost':float(total),
        'budget':float(budget),'within_budget':within,'leftover_value':float(leftover_value),
        'candidate_count':int(len(o)),'optimizer':'SciPy MILP',
        'pantry_groups':list(pantry_groups),'audit':audit
    }
