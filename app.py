import html
import json
import logging
from pathlib import Path
from urllib.parse import quote

import pandas as pd
import streamlit as st
from streamlit_local_storage import LocalStorage
from core import load_data, plan_week, DEFAULT_PANTRY
from ui_helpers import (
    HISTORY_KEY, create_record, history_json, mark_purchased,
    meal_parts, read_history, merge_history, recipe_search_url,
)

logger = logging.getLogger('bowlly')
logging.basicConfig(level=logging.INFO)
st.set_page_config(page_title='bowlly | 이번 주 식단과 장보기', page_icon='🍽️', layout='wide')
st.markdown('<style>' + (Path(__file__).parent / 'ui_dashboard.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)

pool, ing, prices, options, audit, pmeta = load_data()

# Only browser-local storage is used. No cross-user shared server JSON or session data.
local_storage = LocalStorage()
raw_saved = local_storage.getItem(HISTORY_KEY, key='bowlly_history_read')
if 'history' not in st.session_state:
    st.session_state.history = []
if 'history_loaded' not in st.session_state:
    st.session_state.history_loaded = False
if raw_saved is not None and not st.session_state.history_loaded:
    st.session_state.history = merge_history(st.session_state.history, raw_saved)
    st.session_state.history_loaded = True


def store_history(records):
    st.session_state.history = read_history(records)
    st.session_state.history_loaded = True
    local_storage.setItem(HISTORY_KEY, history_json(st.session_state.history), key='bowlly_history_write')


def food_picture(index=0):
    urls = [
        'https://images.unsplash.com/photo-1547592180-85f173990554?auto=format&fit=crop&w=700&q=80',
        'https://images.unsplash.com/photo-1512621776951-a57141f2eefd?auto=format&fit=crop&w=700&q=80',
        'https://images.unsplash.com/photo-1546069901-ba9599a7e63c?auto=format&fit=crop&w=700&q=80',
    ]
    return urls[index % len(urls)]


def show_meal(meal, index):
    components = meal_parts(meal)
    rows = ''.join(
        f'<div class="part"><span class="role">{html.escape(p["role"])}</span><strong>{html.escape(p["name"])}</strong></div>'
        for p in components
    )
    st.markdown(f'''
      <div class="meal-card">
        <div class="meal-photo" style="background-image:url('{food_picture(index)}')"><span>MEAL {index+1:02d}</span></div>
        <div class="meal-body">{rows}
        <div class="nutrition">🔥 {float(meal.get('kcal',0)):,.0f} kcal &nbsp; · &nbsp; 단백질 {float(meal.get('protein_g',0)):.1f}g</div>
        </div>
      </div>''', unsafe_allow_html=True)
    with st.popover(f'📖 {index+1}번째 식단 레시피 검색', use_container_width=True):
        st.caption('레시피 원문이 없는 데이터이므로 외부 검색 결과로 연결합니다. 사진은 해당 식단의 실제 조리 사진이 아닌 대표 이미지예요.')
        for component in components:
            st.link_button(f'{component["role"]} · {component["name"]}', recipe_search_url(component['name']), use_container_width=True)


def show_shopping(rows):
    df = pd.DataFrame(rows)
    if df.empty:
        st.info('이번 조건에는 새로 구매할 재료가 없어요.')
        return
    cols = [c for c in ['품목', '필요량_g', '구매량_g', '예상비용_원', '계산방식'] if c in df.columns]
    view = df[cols].copy()
    st.dataframe(view, use_container_width=True, hide_index=True)
    st.download_button('🛒 장보기 목록 내려받기', df.to_csv(index=False).encode('utf-8-sig'),
                       file_name='bowlly_shopping.csv', mime='text/csv', use_container_width=True)


records = st.session_state.history
st.markdown('''<div class="shell-top"><div class="wordmark"><span>✳</span> bowlly.</div>
  <div class="top-note">나의 작은 식탁 다이어리 &nbsp; ✦ &nbsp; BUDGET MEAL PLANNER</div></div>''', unsafe_allow_html=True)

navigation = st.segmented_control('메뉴', ['🏠 홈', '🍽️ 이번 주 식단', '🛒 장보기 기록', '📒 내 기록'], default='🏠 홈', label_visibility='collapsed')

st.markdown('''<div class="welcome"><div>
  <span class="eyebrow">GOOD FOOD, LITTLE MOMENTS</span>
  <h1>오늘도 맛있게,<br><em>내일도 알뜰하게.</em></h1>
  <p>장보기 예산부터 한 끼 상차림까지. 예쁘고 간편하게 한 주를 준비해요.</p>
  </div><div class="welcome-image"></div></div>''', unsafe_allow_html=True)

if navigation in ['🏠 홈', '🍽️ 이번 주 식단']:
    formcol, sidecol = st.columns([1.65, 1], gap='large')
    with formcol:
        st.markdown('<div class="section-head"><h2>이번 주 식단 만들기</h2><span>YOUR WEEKLY PLAN</span></div>', unsafe_allow_html=True)
        with st.container(border=True):
            with st.form('meal_form'):
                a, b, c = st.columns([1.2,1,1])
                with a: budget = st.number_input('장보기 예산 (원)', min_value=5000, max_value=200000, step=1000, value=30000)
                with b: meal_count = st.selectbox('몇 끼를 준비할까요?', [3,4,5,6,7], index=2)
                with c: household = st.selectbox('식사 인원', [1,2,3,4])
                with st.expander('⚙️ 영양 기준과 집에 있는 재료 (선택)'):
                    l, rr = st.columns(2)
                    with l:
                        min_kcal=st.slider('최소 kcal',300,700,400,50)
                        min_protein=st.slider('최소 단백질(g)',5,40,15,1)
                    with rr:
                        max_kcal=st.slider('최대 kcal',500,1000,850,50)
                        max_sodium=st.slider('최대 나트륨(mg)',1000,3000,2000,100)
                    pantry = st.multiselect('이미 보유한 재료', DEFAULT_PANTRY, default=DEFAULT_PANTRY)
                    st.caption('선택한 재료는 구매비에서 제외해요. 영양 기준은 의료·영양 처방이 아닙니다.')
                submit = st.form_submit_button('✨ 이번 주 식단 추천받기', type='primary', use_container_width=True)
        st.markdown('''<div class="info-row"><div><span>01</span> 예산 입력</div><div><span>02</span> 식단 추천</div><div><span>03</span> 기록 저장</div></div>''', unsafe_allow_html=True)
    with sidecol:
        st.markdown('<div class="section-head"><h2>나의 최근 기록</h2><span>HISTORY</span></div>',unsafe_allow_html=True)
        if not records:
            st.markdown('''<div class="empty-card">📔<h3>아직 저장한 식단이 없어요.</h3><p>식단을 추천받고 저장하면<br>날짜별 기록이 여기에 남아요.</p></div>''',unsafe_allow_html=True)
        else:
            for rec in records[:3]:
                status='장보기 완료' if rec.get('status')=='purchased' else '계획 저장'
                st.markdown(f'<div class="recent"><span>{html.escape(rec.get("created_at",""))} · {status}</span><b>{int(rec.get("meal_count",0))}끼 식단</b><strong>{int(rec.get("total_cost",0)):,}원</strong></div>', unsafe_allow_html=True)
        st.markdown('''<div class="soft-card"><b>🛍️ 장보기도 깔끔하게</b><p>같은 재료는 모아보고, 예상 장보기비를 확인해요. 기록은 이 브라우저에만 저장돼요.</p></div>''',unsafe_allow_html=True)
    if submit:
        try:
            with st.spinner('식단을 예쁘게 차리는 중이에요…'):
                response = plan_week(budget,meal_count,household,pantry,min_kcal,max_kcal,min_protein,max_sodium)
            st.session_state.result = response
            st.session_state.budget = budget
            st.session_state.meal_count = meal_count
            st.session_state.household = household
            st.session_state.saved_result_id = None
        except ValueError as exc:
            st.warning(str(exc))
            st.session_state.result = None
        except Exception:
            logger.exception('추천 계산 실패')
            st.error('추천 계산 중 오류가 발생했습니다. 설정을 확인하고 다시 시도해 주세요.')
            st.session_state.result = None

    result = st.session_state.get('result')
    if result:
        cost = float(result['total_cost'])
        difference = st.session_state.budget-cost
        st.markdown('<div class="section-head"><h2>완성된 나의 식단 🍽️</h2><span>MEAL PLAN</span></div>', unsafe_allow_html=True)
        st.markdown(f'''<div class="summary-grid">
          <div><span>예상 장보기비</span><strong>{cost:,.0f}원</strong></div>
          <div><span>남는 예산</span><strong>{difference:,.0f}원</strong></div>
          <div><span>추천 끼니</span><strong>{len(result['selected'])}끼</strong></div></div>''', unsafe_allow_html=True)
        if not result['within_budget']:
            st.warning('설정한 예산을 초과해요. 현재 조건에서 가장 저렴한 대안을 보여드립니다.')
        st.markdown('<div class="section-subtitle">밥 · 국/찌개 · 주메뉴 · 반찬을 한 상에 담았어요.</div>',unsafe_allow_html=True)
        cards = st.columns(2)
        for i,meal in enumerate(result['selected']):
            with cards[i%2]:show_meal(meal,i)
        a,b=st.columns([1,1])
        with a:
            if st.button('💗 날짜별 식단 기록에 저장', use_container_width=True, type='primary', disabled=bool(st.session_state.get('saved_result_id'))):
                record=create_record(result,st.session_state.budget,st.session_state.household,st.session_state.meal_count)
                store_history([record]+st.session_state.history)
                st.session_state.saved_result_id=record['id']
                st.success(f"{record['created_at']} 식단을 이 브라우저에 저장했어요!")
        with b:
            st.download_button('⬇️ 내 식단 JSON 백업',json.dumps(result['selected'],ensure_ascii=False,default=str,indent=2),file_name='bowlly_meals.json',mime='application/json',use_container_width=True)
        st.markdown('<div class="section-head"><h2>이렇게 장보세요 🧺</h2><span>GROCERY LIST</span></div>',unsafe_allow_html=True)
        show_shopping(json.loads(result['shopping'].to_json(orient='records',force_ascii=False)))
    elif submit:
        st.warning('지금 조건에는 가능한 식단이 없어요. 영양 범위를 넓히거나 보유재료 조건을 변경해 주세요.')

if navigation in ['📒 내 기록', '🛒 장보기 기록']:
    st.markdown('<div class="section-head"><h2>나의 식단 다이어리</h2><span>MY COLLECTION</span></div>',unsafe_allow_html=True)
    st.caption('기록은 현재 브라우저에 보관돼요. 다른 기기·시크릿 창과 동기화되지 않으며 브라우저 데이터를 삭제하면 사라질 수 있어요.')
    if st.button('🔄 이 브라우저의 기록 다시 불러오기'):
        st.session_state.history_loaded=False
        st.rerun()
    if not records:
        st.info('저장된 기록이 없습니다. 홈에서 식단을 추천받은 뒤 저장해 주세요.')
    for rec in records:
        rid=rec['id']
        status='✅ 장보기 완료' if rec.get('status')=='purchased' else '📋 장보기 계획'
        label=f"{rec.get('created_at','날짜 없음')}  ·  {rec.get('meal_count',0)}끼  ·  {int(rec.get('total_cost',0)):,}원  ·  {status}"
        with st.expander(label):
            st.write(f"**설정 예산** {int(rec.get('budget',0)):,}원  |  **인원** {rec.get('household',1)}명")
            if navigation=='📒 내 기록':
                for i,meal in enumerate(rec['meals']):show_meal(meal,i)
            if navigation=='🛒 장보기 기록':
                show_shopping(rec['shopping'])
                if rec.get('purchased_at'):
                    st.caption(f"장보기 완료 표시: {rec['purchased_at']}")
            c1,c2=st.columns(2)
            with c1:
                if rec.get('status')!='purchased' and st.button('✅ 장보기 완료로 표시',key=f'bought_{rid}',use_container_width=True):
                    new=[mark_purchased(x) if x['id']==rid else x for x in st.session_state.history]
                    store_history(new)
                    st.rerun()
            with c2:
                if st.button('🗑️ 이 기록 삭제',key=f'del_{rid}',use_container_width=True):
                    store_history([x for x in st.session_state.history if x['id']!=rid])
                    st.rerun()
    if records:
        st.download_button('⬇️ 나의 전체 기록 백업 (JSON)',history_json(records),file_name='bowlly_history.json',mime='application/json',use_container_width=True)
    if navigation=='📒 내 기록':
        with st.expander('📤 다른 브라우저에서 가져온 기록 복원'):
            backup=st.file_uploader('기록 JSON 파일',type=['json'])
            if backup and st.button('기록 가져오기'):
                try:
                    imported=read_history(backup.getvalue().decode('utf-8'))
                    if not imported:st.warning('유효한 식단 기록을 찾지 못했습니다.')
                    else:
                        store_history(merge_history(st.session_state.history,imported))
                        st.success(f'{len(imported)}건의 기록을 가져왔어요.')
                except (UnicodeDecodeError, ValueError):st.error('JSON 파일을 읽을 수 없어요.')

with st.expander('🔎 데이터 출처와 검증 기준 · 개발 정보'):
    st.write(f"원자료 메뉴 **{audit['menu_count']:,}개** · 주요 영양소 5종 계산 가능 **{audit['all5_complete_pct']:.1f}%** · 엄격 가격 검증 메뉴 **{audit['strict_menu_items_default_pantry']}개**")
    st.write('메뉴젠 / 국가표준식품성분DB 10.4 / KAMIS / 한국소비자원 참가격. 같은 품목으로 직접 연결된 A등급 가격만 장보기비 계산에 사용해요. 별도의 변환 또는 다른 상품 대체가격(B/C)은 계산에서 제외합니다.')
    st.write('원자료에 조리 순서나 실제 음식 사진이 없어 식단별 레시피는 외부 검색으로 연결하고, 사진은 예시 이미지로 제공해요.')
st.markdown('<div class="footer">© 2026 bowlly. &nbsp; Made for easy little meals. <span>공공가격 기준 예상금액 · 실제 구매 금액과 다를 수 있어요.</span></div>',unsafe_allow_html=True)