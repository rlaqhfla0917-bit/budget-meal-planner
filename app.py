import html
import logging
import streamlit as st
from core import load_data, plan_week, DEFAULT_PANTRY
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger('budget_meal')

st.set_page_config(page_title='bowlly | 나만의 주간 식단', page_icon='🥗', layout='wide')

st.markdown('<style>' + (Path(__file__).resolve().parent / 'ui_editorial.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)

pool, ing, prices, options, audit, pmeta = load_data()

st.markdown('''
<div class="brandbar"><div class="logo"><span class="logo-mark">b.</span>bowlly</div>
<div class="brand-right"><span>좋은 한 끼를 위한 작은 계획</span><b>WEEKLY MEAL PLANNER</b></div></div>
<div class="hero">
  <div class="hero-content">
    <div class="hero-kicker">WHAT'S ON YOUR TABLE?</div>
    <h1>장보기는 가볍게.<br><em>식탁은 더 풍성하게.</em></h1>
    <p>이번 주, 뭘 먹을지 고민하지 마세요.<br>내 예산에 맞는 식단부터 필요한 장보기 목록까지,<br>한 번에 준비해 드려요.</p>
    <div class="hero-chips"><span>✦ 예산 맞춤</span><span>✦ 영양 기준</span><span>✦ 장보기 리스트</span></div>
  </div>
  <div class="hero-media" aria-hidden="true"><div class="hero-photo"></div>
   <div class="hero-bubble one">🌱 오늘의 선택<strong>든든하고 알뜰하게</strong></div>
   <div class="hero-bubble two">🛒 나만의 장보기<strong>필요한 만큼만</strong></div>
   <div class="hero-star">✳</div>
  </div>
</div>
''',unsafe_allow_html=True)

st.markdown('<div class="introline"><h2>우리 집 이번 주 식단 만들기</h2><span>세 가지만 입력하면 시작할 수 있어요.</span></div>',unsafe_allow_html=True)

st.markdown('<div class="planner-card"><div class="planner-heading"><strong>🍽️ 내 식단에 맞게 설정하기</strong><span>STEP 01 · START HERE</span></div></div>',unsafe_allow_html=True)
# 기본 입력은 메인 화면. 계산은 기존 core.plan_week 그대로 사용.
with st.form('meal_planner_form', clear_on_submit=False):
    col_budget,col_count,col_house=st.columns([1.35,1,1])
    with col_budget:
        budget=st.number_input('장보기 예산 (원)',min_value=5000,max_value=200000,value=30000,step=1000,format='%d')
    with col_count:
        meal_count=st.select_slider('식사 횟수',options=[3,4,5,6,7],value=5)
    with col_house:
        household=st.select_slider('인원 수',options=[1,2,3,4],value=1)
    with st.expander('⚙️ 영양 조건 및 보유재료 맞춤 설정 (선택)'):
        st.caption('원하는 한 끼 영양 범위와 이미 집에 있는 재료를 설정하세요. 모두 선택 사항입니다.')
        col_min,col_max=st.columns(2)
        with col_min:
            min_kcal=st.slider('최소 열량(kcal)',300,700,400,50)
            min_protein=st.slider('최소 단백질(g)',5,40,15,1)
        with col_max:
            max_kcal=st.slider('최대 열량(kcal)',500,1000,850,50)
            max_sodium=st.slider('최대 나트륨(mg)',1000,3000,2000,100)
        pantry=st.multiselect('집에 있는 기본재료 (장보기에서 제외)',options=DEFAULT_PANTRY,default=DEFAULT_PANTRY)
        st.caption('선택한 재료는 보유 중이라고 가정합니다. 영양 조건은 의료·영양 처방 기준이 아닙니다.')
    run=st.form_submit_button('🍽️ 이 조건으로 식단 만들기 →',use_container_width=True,type='primary')
st.markdown('<div class="tiny-note">🔒 회원가입 필요 없음 · 공공 데이터 기반 예상 가격 · 2026년 자료</div>',unsafe_allow_html=True)

if not run:
    st.markdown('''
    <div class="feature-strip">
     <div class="feature a"><span class="number">01 / SMART BUDGET</span><span class="icon">💸</span><strong>예산에 맞게</strong><p>장보기 예산부터 정하고 그 안에서 식단을 찾아요.</p></div>
     <div class="feature b"><span class="number">02 / BALANCED MEALS</span><span class="icon">🥬</span><strong>영양도 꼼꼼하게</strong><p>열량·단백질 등 원하는 조건에 맞춰 메뉴를 골라요.</p></div>
     <div class="feature c"><span class="number">03 / EASY SHOPPING</span><span class="icon">🛍️</span><strong>장보기까지 한 번에</strong><p>중복 재료를 모아서 살 것만 확인할 수 있어요.</p></div>
    </div>
    ''',unsafe_allow_html=True)
    with st.expander('🔍 데이터 출처·검증 기준 확인하기'):
        col1,col2,col3=st.columns(3)
        col1.metric('원자료 메뉴',f"{audit['menu_count']:,}개")
        col2.metric('영양 5종 계산 가능',f"{audit['all5_complete_pct']:.1f}%")
        col3.metric('엄격 검증 메뉴',f"{audit['strict_menu_items_default_pantry']}개")
        st.markdown('**출처:** 메뉴젠 · 국가표준식품성분DB 10.4 · KAMIS · 한국소비자원 참가격. '
                    '동일 품목과 직접 연결된 A등급 가격만 구매비 계산에 사용하고, 추가 근거가 필요한 B등급·대체품 C등급 가격은 제외합니다.')
else:
    try:
        with st.spinner('가격·영양 조건을 확인하며 식단을 계산하고 있어요…'):
            r=plan_week(budget,meal_count,household,pantry,min_kcal,max_kcal,min_protein,max_sodium)
    except ValueError as exc:
        st.warning(str(exc))
        st.stop()
    except Exception:
        logger.exception('식단 계산 중 예상치 못한 오류')
        st.error('식단 계산 중 문제가 발생했습니다. 조건을 다시 설정하고 재시도해 주세요.')
        st.stop()
    if not r:
        st.error('현재 보유재료/영양 조건에서는 A등급 가격만으로 완성 가능한 식단이 없습니다. 보유재료를 늘리거나 영양 범위를 완화해주세요.')
    else:
        remain=budget-r['total_cost']
        within=r['within_budget']
        title='이번 주 식단 완성! 🎉' if within else '조건에 맞는 식단을 찾았어요'
        tagline=f'{meal_count}끼 · {household}인 기준 · 공공가격 기반 예상비용'
        st.markdown(f'''
        <div class="result-hero"><span class="overline">YOUR WEEKLY PLAN IS READY</span>
        <h2>{title}</h2><p>{tagline}</p></div>
        <div class="overview-grid">
         <div class="overview-card one"><span class="label">🛒 예상 장보기비</span><strong>{r['total_cost']:,.0f}원</strong><small>공공가격 기준 예상액</small></div>
         <div class="overview-card two"><span class="label">💰 남는 예산</span><strong>{remain:,.0f}원</strong><small>입력 예산 {budget:,.0f}원</small></div>
         <div class="overview-card three"><span class="label">✨ 비교 후보</span><strong>{r['candidate_count']:,}개</strong><small>최적화 대상 조합</small></div>
        </div>
        ''',unsafe_allow_html=True)
        st.progress(min(1.0, max(0.0, r['total_cost'] / budget)), text=f"예산 사용률 {r['total_cost'] / budget * 100:.1f}% · 공공가격 기준 예상비용")
        if r['within_budget']:
            st.success(f"설정한 {budget:,.0f}원 예산 안에서 {meal_count}끼 식단을 구성했어요!")
        else:
            st.warning(f"현재 조건에서 예산 내 해가 없어 최소비용 해({r['total_cost']:,.0f}원)를 표시합니다.")

        t1,t2,t3,t4=st.tabs(['🍽️ 추천 식단','🛒 장보기 목록','🔎 데이터 검증','⚠️ 계산 기준'])
        with t1:
            st.markdown('<div class="section">오늘은 뭘 먹을까요? 😋</div>',unsafe_allow_html=True)
            cols=st.columns(3)
            for i,m in enumerate(r['selected'],1):
                with cols[(i-1)%3]:
                    st.markdown(f'''
                    <div class="meal-card">
                      <div class="meal-head"><span class="meal-index">MEAL {i:02d}</span><span class="meal-emoji">{['🍲','🥗','🍜','🍚'][i%4]}</span></div>
                      <div class="meal-name">{html.escape(str(m['meal_name']))}</div>
                      <div class="nutri-tags"><span>🔥 {m['kcal']:.0f} kcal</span>
                      <span>단백질 {m['protein_g']:.1f}g</span>
                      <span>Na {m['sodium_mg']:.0f}mg</span></div>
                    </div>''',unsafe_allow_html=True)
            st.caption('영양값은 메뉴젠 재료중량 × 국가표준식품성분DB 10.4의 100g당 값을 합산한 결과입니다.')
        with t2:
            st.markdown('<div class="section">장보기도 한 번에 끝내요 🛍️</div>',unsafe_allow_html=True)
            st.dataframe(r['shopping'],use_container_width=True,hide_index=True)
            if not r['shopping'].empty:
                st.download_button(
                    '⬇️ 장보기 목록 저장하기 (CSV)',
                    data=r['shopping'].to_csv(index=False).encode('utf-8-sig'),
                    file_name='shopping_list.csv',
                    mime='text/csv',
                    use_container_width=True,
                )
            st.info('KAMIS 품목은 가격표의 g당 기준단가로 예상비용을 계산하므로 잔여량을 만들지 않습니다. 참가격의 g 표기 실제 상품만 포장단위 구매와 잔여량을 계산합니다.')
        with t3:
            st.markdown('<div class="section">실제 사용한 근거</div>',unsafe_allow_html=True)
            st.write(f"- 최적화 방식: **{r['optimizer']} (혼합정수선형계획)**")
            st.write(f"- 메뉴젠 고유 재료 ↔ 국가표준식품성분DB exact match: **{audit['fooddb_exact_match_count']:,}/{audit['unique_ingredients']:,}**")
            st.write(f"- 에너지·단백질·칼슘·철·나트륨 모두 완전계산: **{audit['all5_complete_menus']:,}개 ({audit['all5_complete_pct']:.1f}%)**")
            st.write(f"- 가격매핑 수동 검토 재료: **{audit['reviewed_mvp_ingredient_names']}개**")
            st.write(f"- A/B/C/R: **{audit['mapping_grade_counts']['A']} / {audit['mapping_grade_counts']['B']} / {audit['mapping_grade_counts']['C']} / {audit['mapping_grade_counts']['R']}**")
            st.write(f"- 기본 보유재료 가정에서 A등급 구매가격만으로 구성 가능한 식사용 메뉴: **{audit['strict_menu_items_default_pantry']}개**")
        with t4:
            st.markdown('<div class="section">이번 버전에서 일부러 쓰지 않은 것</div>',unsafe_allow_html=True)
            st.write('- `재래간장 → 양조간장`, `순두부 → 일반두부`, `감자전분 → 생감자` 같은 **C등급 대체가격은 모두 구매비 계산에서 제외**했습니다.')
            st.write('- 계란 개수→g, 조리밥→생쌀, 데친 재료→생재료, ml→g 변환처럼 별도 근거가 필요한 **B등급도 구매비 계산에서 제외**했습니다.')
            st.write('- KAMIS의 1kg·100g 등은 실제 최소 포장단위로 간주하지 않고 **중량 기준 예상비용**으로만 계산합니다.')
            st.write('- 기대효과 20%·30%·50% 등의 수치는 아직 사용자 실증 전이므로 **성과값으로 표시하지 않습니다.**')

st.markdown('<div class="footer"><div><b>bowlly.</b> GOOD FOOD, SMART BUDGET.</div><div>2026 공공데이터 기반 · 실제 구매가격은 다를 수 있습니다.</div></div>',unsafe_allow_html=True)
