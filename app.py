import streamlit as st
import math
import pandas as pd

# ---------------------------------------------------
# Streamlit 기본 설정
# ---------------------------------------------------
st.set_page_config(page_title="1일 칼로리 계산 앱", layout="wide")

st.title("🔥 1일 권장 칼로리 계산 앱")
st.caption("입력한 정보를 기반으로 BMR·권장 칼로리·음식 섭취량을 계산합니다.")

# ---------------------------------------------------
# 데이터
# ---------------------------------------------------
foods = {
    "탄수화물": {
        1: {"name": "백미 한 공기", "kcal": 300, "unit": "1공기(210g)"},
        2: {"name": "잡곡밥 한 공기", "kcal": 330, "unit": "1공기(210g)"},
        3: {"name": "식빵 한 조각", "kcal": 90, "unit": "1쪽"},
        4: {"name": "찐 고구마", "kcal": 115, "unit": "100g"}
    },

    "단백질": {
        1: {"name": "생선", "kcal": 200, "unit": "100g"},
        2: {"name": "소고기", "kcal": 250, "unit": "100g"},
        3: {"name": "돼지고기", "kcal": 290, "unit": "100g"},
        4: {"name": "닭고기", "kcal": 165, "unit": "100g"},
        5: {"name": "계란", "kcal": 78, "unit": "1알(50g)"},
        6: {"name": "두부", "kcal": 80, "unit": "100g"}
    },

    "면류": {
        1: {"name": "라면", "kcal": 500, "unit": "1그릇"},
        2: {"name": "짜장면", "kcal": 700, "unit": "1그릇"},
        3: {"name": "짬뽕", "kcal": 600, "unit": "1그릇"}
    },

    "과일·야채": {
        1: {"name": "사과", "kcal": 95, "unit": "1개"},
        2: {"name": "바나나", "kcal": 105, "unit": "1개"},
        3: {"name": "귤", "kcal": 40, "unit": "1개"},
        4: {"name": "샐러드", "kcal": 120, "unit": "1그릇"}
    },

    "간식": {
        1: {"name": "과자", "kcal": 450, "unit": "1봉지"},
        2: {"name": "아이스크림", "kcal": 250, "unit": "1개"},
        3: {"name": "초콜릿", "kcal": 220, "unit": "1개"}
    },

    "한 끼 식사": {
        1: {"name": "피자 한 조각", "kcal": 285, "unit": "1조각"},
        2: {"name": "떡볶이 1인분", "kcal": 550, "unit": "1인분"},
        3: {"name": "비빔밥 한 그릇", "kcal": 550, "unit": "1그릇"},
        4: {"name": "햄버거 1개", "kcal": 350, "unit": "1개"}
    }
}

cooking_methods = {
    "구이": 1.10,
    "볶음": 1.20,
    "찜/수비드": 0.95,
    "튀김": 1.40
}

# ⭐️ 운동 강도 옵션 수정 (사용자 요청 반영)
exercise_levels = {
    "유산소 30분~1시간": 200,
    "유산소 1시간~2시간": 350,
    "근력운동 30분~1시간": 150,
    "근력운동 1시간~2시간": 300,
    "유산소 + 근력운동 1시간~2시간": 450 # 새로 추가된 옵션
}

activity_factor = {
    "거의 운동 안함": 1.2,
    "가벼운 활동": 1.375,
    "보통 활동": 1.55,
    "활동적": 1.725,
    "매우 활동적": 1.9
}

# 조리 방식 선택이 필요한 카테고리
RELEVANT_COOKING_CATEGORIES = ["단백질"] 

# ---------------------------------------------------
# BMR 계산 함수
# ---------------------------------------------------
def calc_bmr(gender, weight, height, age):
    if gender == "남자":
        return 88.4 + (13.4 * weight) + (4.8 * height) - (5.68 * age)
    else:
        return 447.6 + (9.25 * weight) + (3.10 * height) - (4.33 * age)

# ---------------------------------------------------
# 상태 초기화 및 관리
# ---------------------------------------------------
# 1. BMR 계산에 사용할 '실제' 유효한 기본값/입력값 저장 (오류 방지)
if "user_data" not in st.session_state:
    st.session_state.user_data = {
        "gender": "남자", "age": 20, "height": 173.0, "weight": 60.0, 
        "activity": list(activity_factor.keys())[0], 
        "week_ex": 3, 
        # ⭐️ 초기값 수정: 새롭게 바뀐 운동 레벨의 첫 번째 옵션으로 설정
        "ex_level": list(exercise_levels.keys())[0] 
    }

# 2. st.number_input의 'value'에 들어갈 값 저장. (플레이스홀더 구현)
#    처음에는 None을 넣어 플레이스홀더만 보이게 함. 
if "input_age" not in st.session_state:
    st.session_state.input_age = None
if "input_height" not in st.session_state:
    st.session_state.input_height = None
if "input_weight" not in st.session_state:
    st.session_state.input_weight = None

if "current_step" not in st.session_state:
    st.session_state.current_step = 0
if "food_list" not in st.session_state:
    st.session_state.food_list = []


MAX_STEP = 3
step_titles = [
    "① 신체 정보 입력",
    "② 활동/운동 입력",
    "③ 음식 선택",
    "④ 결과 확인"
]

current_step = st.session_state.current_step
st.header(step_titles[current_step])

# ---------------------------------------------------
# 1) 신체 정보 입력
# ---------------------------------------------------
if current_step == 0:
    
    st.session_state.user_data["gender"] = st.radio("성별", ["남자", "여자"], 
                                                    index=["남자", "여자"].index(st.session_state.user_data["gender"]))
    
    # 만 나이
    age_input = st.number_input("만 나이", 
                                min_value=1, max_value=120, 
                                value=st.session_state.input_age,
                                key="age_input", 
                                placeholder="20") 
    
    if age_input is not None and age_input >= 1:
        st.session_state.user_data["age"] = age_input
        st.session_state.input_age = age_input
    


    # 키 (cm)
    height_input = st.number_input("키 (cm)", 
                                   min_value=100.0, max_value=250.0, 
                                   value=st.session_state.input_height,
                                   format="%.1f",
                                   key="height_input",
                                   placeholder="173.0")
    
    if height_input is not None and height_input >= 100.0:
        st.session_state.user_data["height"] = height_input
        st.session_state.input_height = height_input
    

    # 몸무게 (kg)
    weight_input = st.number_input("몸무게 (kg)", 
                                   min_value=20.0, max_value=200.0, 
                                   value=st.session_state.input_weight,
                                   format="%.1f",
                                   key="weight_input",
                                   placeholder="60.0")
    
    if weight_input is not None and weight_input >= 20.0:
        st.session_state.user_data["weight"] = weight_input
        st.session_state.input_weight = weight_input


# ---------------------------------------------------
# 2) 생활 활동량·운동 정보
# ---------------------------------------------------
elif current_step == 1:
    user_data = st.session_state.user_data
    activity_keys = list(activity_factor.keys())
    ex_level_keys = list(exercise_levels.keys())

    st.session_state.user_data["activity"] = st.selectbox("일상 생활 활동량", activity_keys, 
                                                         index=activity_keys.index(user_data["activity"]))
    st.session_state.user_data["week_ex"] = st.slider("일주일 운동 횟수", 0, 14, user_data["week_ex"])
    # ⭐️ 수정된 exercise_levels 키를 사용하여 selectbox 생성
    st.session_state.user_data["ex_level"] = st.selectbox("운동 강도 선택", ex_level_keys, 
                                                          index=ex_level_keys.index(user_data["ex_level"]))

# ---------------------------------------------------
# 3) 음식 선택
# ---------------------------------------------------
elif current_step == 2:
    col1, col2, col3 = st.columns(3)

    with col1:
        if "selected_category" not in st.session_state:
            st.session_state.selected_category = list(foods.keys())[0]
        
        category = st.selectbox("카테고리 선택", list(foods.keys()), key="cat_select", index=list(foods.keys()).index(st.session_state.selected_category))
        st.session_state.selected_category = category

    with col2:
        food_options = list(foods[category].keys())
        if f"selected_food_{category}" not in st.session_state or st.session_state[f"selected_food_{category}"] not in food_options:
            st.session_state[f"selected_food_{category}"] = food_options[0]

        food_num = st.selectbox(
            "음식 선택",
            food_options,
            key="food_select",
            index=food_options.index(st.session_state[f"selected_food_{category}"]),
            format_func=lambda x: foods[category][x]["name"]
        )
        st.session_state[f"selected_food_{category}"] = food_num
        
    with col3:
        amount = st.number_input("섭취량(배수)", min_value=0.1, value=1.0, step=0.1, key="amount_input")

    food_item = foods[category][food_num]["name"]
    base_kcal = foods[category][food_num]["kcal"]

    # --- 조리 방식 선택 조건부 로직 ---
    cook_method = "선택 안 함 (조리 영향 없음)"
    cook_factor = 1.0

    if category in RELEVANT_COOKING_CATEGORIES:
        cook_method = st.selectbox("조리 방식", list(cooking_methods.keys()))
        cook_factor = cooking_methods[cook_method]
    else:
        st.info("이 카테고리는 조리 방식 선택이 칼로리에 영향을 주지 않습니다. (계수 1.0 적용)")

    st.markdown("---")
    
    if st.button("추가하기", key="add_food_btn"):
        kcal = base_kcal * amount * cook_factor

        st.session_state.food_list.append({
            "name": food_item,
            "amount": amount,
            "method": cook_method,
            "kcal": kcal
        })

        st.success(f"**{food_item}** ({cook_method}, {amount}배) 추가 완료! (예상 칼로리: {kcal:.1f} kcal)")

    if st.session_state.food_list:
        st.subheader("현재 음식 목록")
        total_eaten_kcal = sum([f["kcal"] for f in st.session_state.food_list])
        st.info(f"총 섭취 칼로리 합계: **{total_eaten_kcal:.1f} kcal**")
        
        df = pd.DataFrame(st.session_state.food_list)
        df = df.rename(columns={"name": "음식", "amount": "섭취량(배수)", "method": "조리 방식", "kcal": "칼로리(kcal)"})
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        if st.button("음식 목록 초기화", key="clear_food_list_btn"):
            st.session_state.food_list = []
            st.rerun()


# ---------------------------------------------------
# 4) 결과 확인
# ---------------------------------------------------
elif current_step == 3:
    user_data = st.session_state.user_data
    
    # BMR 및 TDEE 계산
    bmr = calc_bmr(user_data["gender"], user_data["weight"], user_data["height"], user_data["age"])
    act_coef = activity_factor[user_data["activity"]]
    # ⭐️ 수정된 exercise_levels에서 kcal 값 가져오기
    extra_kcal = (exercise_levels[user_data["ex_level"]] * user_data["week_ex"]) / 7
    tdee = bmr * act_coef + extra_kcal
    
    # 총 섭취 칼로리 계산
    total = sum([f["kcal"] for f in st.session_state.food_list])
    
    st.subheader("✅ 계산 결과 요약")
    
    col_res1, col_res2, col_res3 = st.columns(3)
    
    with col_res1:
        st.metric("📌 기초대사량(BMR)", f"{bmr:.1f} kcal")
    with col_res2:
        st.metric("📌 1일 권장 칼로리(TDEE)", f"{tdee:.1f} kcal")
    with col_res3:
        st.metric("🍽 총 섭취 칼로리", f"{total:.1f} kcal")
    
    st.markdown("---")
    
    st.subheader("📊 칼로리 섭취량 분석")
    
    if total > tdee:
        st.error(f"⚠️ 권장 칼로리 **{tdee:.1f} kcal** 대비 **{total - tdee:.1f} kcal** 초과했습니다! 섭취량을 조절해 보세요.")
    else:
        st.success(f"🎉 권장 칼로리 **{tdee:.1f} kcal** 이하입니다! (여유 칼로리: **{tdee-total:.1f} kcal**)")

# ---------------------------------------------------
# 내비게이션 버튼 (모든 단계 하단에 표시)
# ---------------------------------------------------

st.markdown("---")
col_prev, col_spacer, col_next = st.columns([2, 5, 2])

# 이전 페이지 버튼
with col_prev:
    if current_step > 0:
        if st.button("⬅️ 이전 페이지", use_container_width=True):
            st.session_state.current_step -= 1
            st.rerun()

# 다음 페이지 버튼
with col_next:
    if current_step < MAX_STEP:
        if st.button("다음 페이지 ➡️", use_container_width=True):
            st.session_state.current_step += 1
            st.rerun()