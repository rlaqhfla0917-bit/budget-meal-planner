import html
import logging
import streamlit as st
from core import load_data, plan_week, DEFAULT_PANTRY
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger=logging.getLogger('budget_meal')

st.set_page_config(page_title='Budget Table | 나만의 주간 식단', page_icon='🥗', layout='wide')

st.markdown('''
<style>
:root{--green:#2F6B4F;--dark:#1E2C24;--muted:#6B756E;--bg:#F6F7F3;--card:#FFF;--line:#E2E8E3;--soft:#EAF2EC;--cream:#FFF8E9;}
.stApp{background:var(--bg)}
[data-testid="stSidebar"]{background:#EEF3ED;border-right:1px solid var(--line)}
.block-container{max-width:1220px;padding-top:2rem;padding-bottom:3rem}
h1,h2,h3,p,div,span,label{font-family:Pretendard,"Noto Sans KR","Malgun Gothic",sans-serif}
.hero{background:linear-gradient(135deg,#254B39,#397156 65%,#5A8E6E);border-radius:24px;padding:34px 38px;margin-bottom:18px;box-shadow:0 14px 36px rgba(37,75,57,.12)}
.hero .badge{display:inline-block;padding:6px 10px;border-radius:999px;border:1px solid rgba(255,255,255,.25);background:rgba(255,255,255,.12);color:white;font-weight:800;font-size:.75rem;margin-bottom:12px}
.hero h1{color:#fff;font-size:2.1rem;line-height:1.25;margin:0 0 10px;letter-spacing:-.04em}.hero p{color:rgba(255,255,255,.84);line-height:1.65;margin:0}
.notice{background:white;border:1px solid var(--line);border-left:4px solid var(--green);border-radius:14px;padding:13px 16px;color:var(--muted);font-size:.86rem;line-height:1.6;margin:12px 0 20px}
[data-testid="stMetric"]{background:#fff;border:1px solid var(--line);border-radius:17px;padding:15px 17px;box-shadow:0 3px 12px rgba(30,44,36,.035)}
[data-testid="stMetricValue"]{color:var(--dark);font-weight:850}
.section{font-size:1.15rem;font-weight:850;color:var(--dark);margin:26px 0 12px;letter-spacing:-.02em}
.meal{background:#fff;border:1px solid var(--line);border-radius:17px;padding:18px;min-height:176px;margin-bottom:12px}.meal .no{font-size:.73rem;font-weight:850;color:var(--green);letter-spacing:.06em}.meal .name{font-size:1rem;font-weight:800;color:var(--dark);line-height:1.45;margin:7px 0 12px}.chip{display:inline-block;background:#F2F5F1;color:#58635C;border-radius:999px;padding:5px 8px;font-size:.72rem;margin:2px 3px 2px 0}
.rule-card{background:var(--cream);border:1px solid #F0E0BC;border-radius:14px;padding:14px 16px;color:#635641;font-size:.84rem;line-height:1.6}
div.stButton>button{background:var(--green);color:white;border:none;border-radius:12px;min-height:46px;font-weight:800}div.stButton>button:hover{background:#285F46;color:white;border:none}
</style>
''',unsafe_allow_html=True)

st.markdown('<style>' + (Path(__file__).resolve().parent / 'ui_theme.css').read_text(encoding='utf-8') + '</style>', unsafe_allow_html=True)

pool, ing, prices, options, audit, pmeta = load_data()

st.markdown('''
<div class="brandbar">BUDGET TABLE <span>SMALL BUDGET, BETTER TABLE.</span></div>
<div class="hero">
 <div class="badge">공공데이터 기반 · 주간 식단 플래너</div>
 <h1>이번 주 식단,<br><em>예산 안에서 맛있게.</em></h1>
 <p>예산과 식사 조건을 정하면, 식단부터 장보기 목록까지<br>꼼꼼하게 계산해 드려요.</p>
 <div class="hero-pills"><span>✓ 영양 조건 반영</span><span>✓ 예상 장보기비 계산</span><span>✓ 공공가격 검증</span></div>
</div>
''',unsafe_allow_html=True)

st.markdown(
    '<div class="notice">📌 <b>안내</b> · 공공가격 기반 <b>예상 장보기 비용</b>으로 실제 매장 결제금액과 다를 수 있습니다. '
    '동일 품목 가격만 계산에 사용하며, 보유 중이라고 선택한 재료는 구매비에서 제외합니다.</div>',
    unsafe_allow_html=True)

with st.sidebar:
    st.markdown('### 🍽️ 이번 주 식단 설정')
    st.markdown('<div class="sidebar-help">예산과 식사 조건을 정한 다음, 아래 버튼을 눌러주세요.</div>',unsafe_allow_html=True)
    budget=st.number_input('주간 장보기 예산',min_value=5000,max_value=200000,value=30000,step=1000,format='%d')
    meal_count=st.slider('계획할 끼니 수',3,7,5)
    household=st.slider('인원 수',1,4,1)
    st.divider()
    st.markdown('### 🌱 영양 기준')
    min_kcal=st.slider('최소 kcal',300,700,400,50)
    max_kcal=st.slider('최대 kcal',500,1000,850,50)
    min_protein=st.slider('최소 단백질(g)',5,40,15,1)
    max_sodium=st.slider('최대 나트륨(mg)',1000,3000,2000,100)
    st.caption('※ 공식 1끼 권고값이 아니라 사용자가 조정하는 MVP 필터입니다.')
    st.divider()
    st.markdown('### 🧺 집에 있는 재료')
    pantry=st.multiselect(
        '이번 장보기에서 제외할 재료',
        options=DEFAULT_PANTRY,
        default=DEFAULT_PANTRY,
        help='보유했다고 선택한 재료는 구매가격 매핑 등급과 관계없이 이번 장보기 비용에서 제외합니다.'
    )
    st.caption('기본값은 쌀·양념류를 이미 보유한 주간 장보기 시나리오입니다.')
    run=st.button('✨ 이번 주 식단 만들기',use_container_width=True,type='primary')

if not run:
    st.markdown('<div class="section">간단한 세 단계로 준비해요</div>',unsafe_allow_html=True)
    st.markdown('''
    <div class="steps-grid">
      <div class="step-card"><div class="step-icon">💰</div><strong>01. 예산 정하기</strong><p>이번 주 장보기에 쓸 금액과 인원, 끼니 수를 정해주세요.</p></div>
      <div class="step-card"><div class="step-icon">🥦</div><strong>02. 조건 선택하기</strong><p>영양 기준과 집에 이미 있는 재료를 선택할 수 있어요.</p></div>
      <div class="step-card"><div class="step-icon">🛒</div><strong>03. 한 번에 장보기</strong><p>식단과 예상 구매비, 장보기 목록을 한눈에 확인해요.</p></div>
    </div>
    ''',unsafe_allow_html=True)
    st.markdown('<div class="section">믿을 수 있는 데이터로 계산해요</div>',unsafe_allow_html=True)
    c1,c2,c3,c4=st.columns(4)
    c1.metric('검토한 메뉴',f"{audit['menu_count']:,}개")
    c2.metric('영양정보 완성률',f"{audit['all5_complete_pct']:.1f}%")
    c3.metric('가격 검증 메뉴',f"{audit['strict_menu_items_default_pantry']}개")
    c4.metric('식단 조합 후보',f"{audit['meal_options_broad']:,}개")
    with st.expander('🔎 데이터 검증 기준 자세히 보기'):
        st.markdown('''
        **가격 매핑 기준**
        - **A등급**: 같은 품목의 가격을 직접 확인한 경우에만 장보기 비용에 반영
        - **B등급**: 조리 상태나 단위 변환에 추가 근거가 필요한 경우로, 구매비 계산에서 제외
        - **C등급**: 다른 상품의 가격을 대신 쓴 경우로, 구매비 계산에서 제외
        - **R등급**: 조리수 0원처럼 명시적으로 정한 서비스 규칙

        KAMIS는 품목·품종·단위·등급별 한 행의 값을 사용하며, 참가격은 2026-08-28 동일상품 비세일·비1+1 조사값 중앙값을 사용합니다.
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
        st.markdown(f'<div class="results-heading">✨ 이번 주 식단이 완성됐어요 <span>{meal_count}끼 · {household}인 기준</span></div>',unsafe_allow_html=True)
        remain=budget-r['total_cost']
        c1,c2,c3,c4=st.columns(4)
        c1.metric('예상 장보기비',f"{r['total_cost']:,.0f}원")
        c2.metric('남는 예산',f"{remain:,.0f}원")
        c3.metric('남은 재료 예상 가치',f"{r['leftover_value']:,.0f}원")
        c4.metric('최적화 후보',f"{r['candidate_count']:,}개")
        st.progress(min(1.0, max(0.0, r['total_cost'] / budget)), text=f"예산 사용률 {r['total_cost'] / budget * 100:.1f}% · 공공가격 기준 예상비용")
        if r['within_budget']:
            st.success(f"설정한 {budget:,.0f}원 예산 안에서 {meal_count}끼 식단을 구성했어요!")
        else:
            st.warning(f"현재 조건에서 예산 내 해가 없어 최소비용 해({r['total_cost']:,.0f}원)를 표시합니다.")

        t1,t2,t3,t4=st.tabs(['🍽️ 추천 식단','🛒 장보기 목록','🔎 데이터 검증','⚠️ 계산 기준'])
        with t1:
            st.markdown('<div class="section">이번 주에 먹을 메뉴</div>',unsafe_allow_html=True)
            cols=st.columns(3)
            for i,m in enumerate(r['selected'],1):
                with cols[(i-1)%3]:
                    st.markdown(f'''
                    <div class="meal">
                      <div class="no">MEAL {i}</div>
                      <div class="name">{html.escape(str(m['meal_name']))}</div>
                      <span class="chip">🔥 {m['kcal']:.0f} kcal</span>
                      <span class="chip">💪 단백질 {m['protein_g']:.1f}g</span>
                      <span class="chip">🧂 Na {m['sodium_mg']:.0f}mg</span>
                    </div>''',unsafe_allow_html=True)
            st.caption('영양값은 메뉴젠 재료중량 × 국가표준식품성분DB 10.4의 100g당 값을 합산한 결과입니다.')
        with t2:
            st.markdown('<div class="section">한 번에 준비하는 장보기 목록</div>',unsafe_allow_html=True)
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
