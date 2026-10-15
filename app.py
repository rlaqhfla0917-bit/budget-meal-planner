import html
import logging
import streamlit as st
from core import load_data, plan_week, DEFAULT_PANTRY
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger('budget_meal')

st.set_page_config(page_title='bowlly | 나만의 주간 식단', page_icon='🥗', layout='wide')

st.markdown('<style>' + (Path(__file__).resolve().parent / 'ui_launch.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)

pool, ing, prices, options, audit, pmeta = load_data()

st.markdown('''
<div class="brandbar"><div class="brand-id"><span class="brand-mark">🍽️</span> bowlly<small>한끼가 쉬워지는 순간</small></div><div class="brand-beta">✦ NEW · WEEKLY PLANNER</div></div>
<div class="hero">
  <div class="hero-copy">
    <div class="hero-eyebrow">✨ 이번 주도 맛있게, 가볍게</div>
    <h1>예산은 알뜰하게,<br><em>한 끼는 근사하게!</em></h1>
    <p>식단 고민은 덜고, 맛있는 시간은 더하고.<br>내 예산과 영양 조건에 맞춰 식단부터 장보기까지 한 번에 준비해요.</p>
    <div class="hero-pills"><span>💸 예산 맞춤</span><span>🥗 영양 필터</span><span>🛒 장보기 리스트</span></div>
  </div>
  <div class="hero-art" aria-hidden="true">
    <div class="hero-circle"></div><div class="hero-plate">🥗</div>
    <div class="float-note first">🛒 예상 장보기비<strong>예산에 꼭 맞게</strong></div>
    <div class="float-note second">💚 MY MEAL PLAN<strong>맛있게 완성!</strong></div>
    <div class="sparkle one">✳</div><div class="sparkle two">✦</div>
  </div>
</div>
''',unsafe_allow_html=True)

st.markdown(
    '<div class="notice">💡 <span><b>알려드려요.</b> 공공데이터 기반 예상 장보기 비용으로, 실제 마트 결제액과 차이가 있을 수 있어요. '
    '정확하게 연결된 가격만 사용하고 이미 집에 있는 재료는 구매비에서 제외해요.</span></div>',
    unsafe_allow_html=True)

with st.sidebar:
    st.markdown('<div class="sidebar-brand"><div class="mark">🍓</div><div><strong>bowlly</strong><span>YOUR WEEKLY MEAL MATE</span></div></div>',unsafe_allow_html=True)
    st.markdown('### 🌟 나만의 식단 설정')
    st.markdown('<div class="sidebar-help">이번 주 예산부터 차근차근 정해볼까요?</div>',unsafe_allow_html=True)
    budget=st.number_input('장보기 예산 (원)',min_value=5000,max_value=200000,value=30000,step=1000,format='%d')
    meal_count=st.slider('이번 주 몇 끼?',3,7,5)
    household=st.slider('함께 먹는 인원',1,4,1)
    st.divider()
    st.markdown('### 🥑 영양 취향 맞추기')
    min_kcal=st.slider('최소 kcal',300,700,400,50)
    max_kcal=st.slider('최대 kcal',500,1000,850,50)
    min_protein=st.slider('최소 단백질(g)',5,40,15,1)
    max_sodium=st.slider('최대 나트륨(mg)',1000,3000,2000,100)
    st.caption('※ 공식 1끼 권고값이 아니라 사용자가 조정하는 MVP 필터입니다.')
    st.divider()
    st.markdown('### 🧺 이미 있는 재료')
    pantry=st.multiselect(
        '이번 장보기에서 제외할 재료',
        options=DEFAULT_PANTRY,
        default=DEFAULT_PANTRY,
        help='보유했다고 선택한 재료는 구매가격 매핑 등급과 관계없이 이번 장보기 비용에서 제외합니다.'
    )
    st.caption('기본값은 쌀·양념류를 이미 보유한 주간 장보기 시나리오입니다.')
    run=st.button('🍽️ 내 식단 추천받기',use_container_width=True,type='primary')

if not run:
    st.markdown('<div class="section">bowlly와 함께, 딱 세 단계 🍓</div>',unsafe_allow_html=True)
    st.markdown('''
    <div class="steps-grid">
      <div class="step-card a"><span class="step-num">01</span><div class="step-icon">💸</div><strong>예산부터 정해요</strong><p>이번 주 얼마나 쓸지, 몇 명이 몇 끼 먹을지 입력해주세요.</p></div>
      <div class="step-card b"><span class="step-num">02</span><div class="step-icon">🥑</div><strong>내 취향을 담아요</strong><p>칼로리와 영양 기준, 이미 집에 있는 재료를 골라요.</p></div>
      <div class="step-card c"><span class="step-num">03</span><div class="step-icon">🛍️</div><strong>맛있는 한 주 완성</strong><p>추천 식단과 예상 장보기 비용, 구매 목록까지 확인해요!</p></div>
    </div>
    <div class="trust-strip"><strong>🔎 확인된 데이터로 추천해요</strong><div>영양 계산 가능 <span>91.0%</span> &nbsp;·&nbsp; 엄격 가격검증 <span>36개 메뉴</span></div></div>
    ''',unsafe_allow_html=True)
    with st.expander('📊 데이터 출처와 가격 계산 기준 자세히 보기'):
        c1,c2,c3,c4=st.columns(4)
        c1.metric('검토한 메뉴',f"{audit['menu_count']:,}개")
        c2.metric('영양정보 완성률',f"{audit['all5_complete_pct']:.1f}%")
        c3.metric('엄격 가격검증 메뉴',f"{audit['strict_menu_items_default_pantry']}개")
        c4.metric('식단 조합 후보',f"{audit['meal_options_broad']:,}개")
        st.markdown('''
        **데이터 출처**: 메뉴젠 · 국가표준식품성분DB 10.4 · KAMIS · 참가격

        - **A**: 동일 품목 가격만 구매비 계산에 사용
        - **B**: 조리 상태·단위 변환에 추가 근거 필요 → 구매비 계산 제외
        - **C**: 다른 품종·상품의 대체가격 → 구매비 계산 제외
        - **R**: 조리수 0원처럼 별도로 명시한 계산 규칙

        KAMIS는 품목·품종·단위·등급별 고정된 한 행을 사용하고, 참가격은 2026-08-28 조사된 동일상품 비세일·비1+1 가격의 중앙값을 사용합니다.
        ''')
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
        <div class="result-banner"><span class="pre">YOUR WEEKLY MEAL PLAN</span>
        <h2>{title}</h2><p>{tagline}</p></div>
        <div class="stats-grid">
          <div class="stat-card cost"><span class="label">🛒 예상 장보기비</span><strong>{r['total_cost']:,.0f}원</strong><small>공공가격 기준</small></div>
          <div class="stat-card left"><span class="label">💰 남는 예산</span><strong>{remain:,.0f}원</strong><small>설정 예산 {budget:,.0f}원</small></div>
          <div class="stat-card options"><span class="label">✨ 검토한 후보 조합</span><strong>{r['candidate_count']:,}개</strong><small>조건에 맞춰 비교했어요</small></div>
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
                    <div class="meal t{i%4}">
                      <div class="meal-top"><div class="no">MEAL {i:02d}</div><div class="meal-icon">{['🍲','🥗','🍜','🍚'][i%4]}</div></div>
                      <div class="name">{html.escape(str(m['meal_name']))}</div>
                      <span class="chip">🔥 {m['kcal']:.0f} kcal</span>
                      <span class="chip">💪 단백질 {m['protein_g']:.1f}g</span>
                      <span class="chip">🧂 Na {m['sodium_mg']:.0f}mg</span>
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

st.markdown('<div class="app-footer"><div><b>bowlly.</b> SMALL BUDGET, HAPPY TABLE.</div><div>공공데이터 기반 식단·장보기 MVP · 예상 가격은 실제 결제액과 다를 수 있어요.</div></div>',unsafe_allow_html=True)
