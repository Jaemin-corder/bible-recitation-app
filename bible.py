import streamlit as st
import difflib
import random
import re

# 페이지 기본 설정
st.set_page_config(
    page_title="말씀 암송 도우미",
    page_icon="📖",
    layout="centered"
)

# 세션 상태 초기화
if "verses" not in st.session_state:
    st.session_state.verses = []

# 교리 요약 세션
if "doctrines" not in st.session_state:
    st.session_state.doctrines = []  # [{'question': ..., 'answer': ...}, ...]

# 암송 테스트 세션
if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
if "selected_range" not in st.session_state:
    st.session_state.selected_range = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# 랜덤 테스트 세션
if "random_quiz_active" not in st.session_state:
    st.session_state.random_quiz_active = False
if "random_order" not in st.session_state:
    st.session_state.random_order = []
if "random_current_index" not in st.session_state:
    st.session_state.random_current_index = 0

# 교리 테스트 세션
if "doctrine_quiz_active" not in st.session_state:
    st.session_state.doctrine_quiz_active = False
if "doctrine_current_index" not in st.session_state:
    st.session_state.doctrine_current_index = 0

# 입력 및 결과 공통 세션
if "last_submitted_text" not in st.session_state:
    st.session_state.last_submitted_text = ""
if "submitted" not in st.session_state:
    st.session_state.submitted = False


def diff_html(user_str, target_str):
    """유저 입력과 정답 텍스트를 비교하여 틀린 부분에 빨간 취소선과 정답을 표시합니다."""
    s = difflib.SequenceMatcher(None, user_str, target_str)
    user_diff_html = []

    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            user_diff_html.append(user_str[i1:i2].replace("\n", "<br>"))
        elif tag == 'replace':
            wrong_part = user_str[i1:i2].replace("\n", "<br>")
            correct_part = target_str[j1:j2].replace("\n", " ")
            user_diff_html.append(
                f"<span style='display:inline-block; text-align:center; vertical-align:bottom; margin: 0 2px;'>"
                f"<sup style='color:#e63946; font-weight:bold; font-size: 0.85em;'>{correct_part}</sup><br>"
                f"<del style='color:#e63946; text-decoration: line-through;'>{wrong_part}</del>"
                f"</span>"
            )
        elif tag == 'delete':
            wrong_part = user_str[i1:i2].replace("\n", "<br>")
            user_diff_html.append(
                f"<del style='color:#e63946; text-decoration: line-through;'>{wrong_part}</del>"
            )
        elif tag == 'insert':
            missing_part = target_str[j1:j2].replace("\n", " ")
            user_diff_html.append(
                f"<span style='color:#e63946; font-weight:bold;'>[{missing_part}]</span>"
            )

    return "".join(user_diff_html)


st.title("📖 말씀 암송 도우미")

# 탭 구성
tab1, tab2, tab3, tab4 = st.tabs(["📝 말씀 저장", "🧠 암송 테스트", "🎲 랜덤 테스트", "📚 교리 요약"])

# ==========================================
# TAB 1: 말씀 저장
# ==========================================
with tab1:
    st.header("말씀 입력 및 저장")
    st.caption("💡 말씀과 말씀 사이에 **빈 줄(엔터 두 번)**을 넣어주시면 자동으로 나누어 저장됩니다.")

    raw_input = st.text_area(
        "말씀들을 한 번에 입력하세요 (마지막 3어절은 주소로 인식됩니다):",
        placeholder=(
            "하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니 이는 그를 믿는 자마다 멸망하지 않고 영생을 얻게 하려 하심이라 요한복음 3장 16절\n\n"
            "여호와는 나의 목자시니 내게 부족함이 없으리로다 시편 23편 1절"
        ),
        height=250
    )

    split_option = st.radio(
        "구분 기준 선택",
        ["빈 줄(엔터 두 번) 기준", "한 줄(엔터 한 번) 기준"],
        horizontal=True
    )

    col1, col2 = st.columns([1, 4])
    with col1:
        save_button = st.button("말씀 저장", type="primary")

    if save_button:
        if raw_input.strip():
            if split_option == "빈 줄(엔터 두 번) 기준":
                chunks = [chunk.strip() for chunk in raw_input.split("\n\n") if chunk.strip()]
            else:
                chunks = [chunk.strip() for chunk in raw_input.split("\n") if chunk.strip()]

            st.session_state.verses.extend(chunks)
            st.success(f"총 {len(chunks)}개의 말씀이 새로 저장되었습니다!")
            st.rerun()
        else:
            st.warning("저장할 말씀 텍스트를 입력해주세요.")

    st.divider()

    st.subheader("📋 현재 저장된 말씀 목록")
    if not st.session_state.verses:
        st.info("아직 저장된 말씀이 없습니다.")
    else:
        st.write(f"총 **{len(st.session_state.verses)}개**의 말씀이 저장되어 있습니다.")
        for idx, verse in enumerate(st.session_state.verses, start=1):
            with st.expander(f"말씀 {idx}번"):
                st.write(verse)

        if st.button("전체 말씀 삭제", help="저장된 모든 말씀을 지웁니다."):
            st.session_state.verses = []
            st.rerun()

# ==========================================
# TAB 2: 순서대로 암송 테스트
# ==========================================
with tab2:
    st.header("말씀 암송하기 (선택 범위)")

    if not st.session_state.verses:
        st.warning("저장된 말씀이 없습니다. '말씀 저장' 탭에서 먼저 말씀을 추가해주세요.")
    else:
        total_count = len(st.session_state.verses)

        if not st.session_state.quiz_active:
            st.subheader("암송할 말씀 번호를 선택하세요")
            options = list(range(1, total_count + 1))

            if hasattr(st, "segmented_control"):
                selected_numbers = st.segmented_control(
                    "말씀 번호 선택 (클릭하여 선택/해제)",
                    options=options,
                    selection_mode="multi",
                    default=options
                )
            else:
                selected_numbers = st.multiselect(
                    "말씀 번호를 선택하세요:",
                    options=options,
                    default=options
                )

            if selected_numbers:
                selected_numbers = sorted(selected_numbers)
                st.write(f"선택한 말씀 번호: **{', '.join(map(str, selected_numbers))}번** (총 {len(selected_numbers)}개)")

                if st.button("암송 시작", type="primary"):
                    st.session_state.selected_range = [n - 1 for n in selected_numbers]
                    st.session_state.current_index = 0
                    st.session_state.last_submitted_text = ""
                    st.session_state.submitted = False
                    st.session_state.quiz_active = True
                    st.rerun()
            else:
                st.info("암송할 말씀을 최소 하나 이상 클릭해서 선택해주세요.")

        else:
            current_verse_pos = st.session_state.selected_range[st.session_state.current_index]
            target_verse = st.session_state.verses[current_verse_pos]
            current_step = st.session_state.current_index + 1
            total_steps = len(st.session_state.selected_range)

            st.subheader(f"진행 상황: ({current_step} / {total_steps}) - 말씀 {current_verse_pos + 1}번")
            st.progress(current_step / total_steps)

            input_key = f"input_tab2_{st.session_state.current_index}_{st.session_state.get('reset_count_tab2', 0)}"
            user_input = st.text_area("기억나는 말씀을 입력하세요:", height=150, key=input_key)

            col_check, col_retry = st.columns([1, 1])
            with col_check:
                if st.button("확인", type="primary", use_container_width=True, key="btn_check_tab2"):
                    if user_input.strip():
                        st.session_state.last_submitted_text = user_input
                        st.session_state.submitted = True
                        st.session_state.reset_count_tab2 = st.session_state.get("reset_count_tab2", 0) + 1
                        st.rerun()
                    else:
                        st.warning("말씀을 입력해 주세요.")

            with col_retry:
                if st.button("🔄 다시 시도", use_container_width=True, key="btn_retry_tab2"):
                    st.session_state.last_submitted_text = ""
                    st.session_state.submitted = False
                    st.session_state.reset_count_tab2 = st.session_state.get("reset_count_tab2", 0) + 1
                    st.rerun()

            if st.session_state.submitted:
                st.divider()
                submitted_text = st.session_state.last_submitted_text

                clean_target = target_verse.replace(" ", "").replace("\n", "")
                clean_user = submitted_text.replace(" ", "").replace("\n", "")

                if clean_target == clean_user:
                    st.success("🎉 완전 일치합니다! 참 잘하셨습니다.")
                else:
                    st.error("❌ 틀린 부분이 있습니다. 아래에서 비교해 보세요.")

                st.markdown("### ✍️ 내가 입력한 말씀 (비교 교정)")
                formatted_diff = diff_html(submitted_text, target_verse)
                st.markdown(
                    f"<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; font-size: 1.1em; line-height: 2.2;'>{formatted_diff}</div>",
                    unsafe_allow_html=True
                )

                st.markdown("### 📖 정답 말씀")
                st.info(target_verse)
                st.divider()

                if st.session_state.current_index + 1 < total_steps:
                    if st.button("다음 말씀으로 ➡️", type="primary", key="btn_next_tab2"):
                        st.session_state.current_index += 1
                        st.session_state.last_submitted_text = ""
                        st.session_state.submitted = False
                        st.session_state.reset_count_tab2 = st.session_state.get("reset_count_tab2", 0) + 1
                        st.rerun()
                else:
                    st.balloons()
                    st.success("✨ 선택한 모든 말씀 암송이 끝났습니다!")
                    if st.button("처음으로 돌아가기", key="btn_finish_tab2"):
                        st.session_state.quiz_active = False
                        st.session_state.last_submitted_text = ""
                        st.session_state.submitted = False
                        st.rerun()

            st.divider()
            if st.button("암송 종료", key="btn_exit_tab2"):
                st.session_state.quiz_active = False
                st.session_state.last_submitted_text = ""
                st.session_state.submitted = False
                st.rerun()

# ==========================================
# TAB 3: 랜덤 암송 테스트
# ==========================================
with tab3:
    st.header("🎲 랜덤 암송 테스트")

    if not st.session_state.verses:
        st.warning("저장된 말씀이 없습니다. '말씀 저장' 탭에서 먼저 말씀을 추가해주세요.")
    else:
        total_count = len(st.session_state.verses)

        if not st.session_state.random_quiz_active:
            st.subheader("전체 말씀 랜덤 암송")
            st.write(f"현재 저장된 총 **{total_count}개**의 말씀을 랜덤 순서로 테스트합니다.")
            st.caption("💡 각 문제에는 **첫 번째 어절**이 힌트로 입력되어 있으며, **마지막 3어절(주소)**이 함께 표시됩니다.")

            if st.button("🎲 랜덤 테스트 시작", type="primary"):
                shuffled_indices = list(range(total_count))
                random.shuffle(shuffled_indices)

                st.session_state.random_order = shuffled_indices
                st.session_state.random_current_index = 0
                st.session_state.last_submitted_text = ""
                st.session_state.submitted = False
                st.session_state.random_quiz_active = True
                st.rerun()

        else:
            current_verse_pos = st.session_state.random_order[st.session_state.random_current_index]
            target_verse = st.session_state.verses[current_verse_pos]
            current_step = st.session_state.random_current_index + 1
            total_steps = len(st.session_state.random_order)

            st.subheader(f"진행 상황: ({current_step} / {total_steps})")
            st.progress(current_step / total_steps)

            words = target_verse.split()

            if len(words) >= 4:
                first_word = words[0]
                target_body_words = " ".join(words[:-3])
                address_words = " ".join(words[-3:])
            else:
                first_word = words[0] if words else ""
                target_body_words = target_verse
                address_words = "주소 미상"

            st.info(f"📍 **주소 힌트:** {address_words}")

            input_key = f"input_tab3_{st.session_state.random_current_index}_{st.session_state.get('reset_count_tab3', 0)}"
            user_input = st.text_area(
                "기억나는 말씀 본문을 이어 써주세요 (주소 제외):",
                value=f"{first_word} ",
                height=150,
                key=input_key
            )

            col_check, col_retry = st.columns([1, 1])
            with col_check:
                if st.button("확인", type="primary", use_container_width=True, key="btn_check_tab3"):
                    if user_input.strip():
                        st.session_state.last_submitted_text = user_input
                        st.session_state.submitted = True
                        st.session_state.reset_count_tab3 = st.session_state.get("reset_count_tab3", 0) + 1
                        st.rerun()
                    else:
                        st.warning("말씀을 입력해 주세요.")

            with col_retry:
                if st.button("🔄 다시 시도", use_container_width=True, key="btn_retry_tab3"):
                    st.session_state.last_submitted_text = ""
                    st.session_state.submitted = False
                    st.session_state.reset_count_tab3 = st.session_state.get("reset_count_tab3", 0) + 1
                    st.rerun()

            if st.session_state.submitted:
                st.divider()
                submitted_text = st.session_state.last_submitted_text

                clean_target_body = target_body_words.replace(" ", "").replace("\n", "")
                clean_user = submitted_text.replace(" ", "").replace("\n", "")

                if clean_target_body == clean_user:
                    st.success("🎉 완전 일치합니다! 참 잘하셨습니다.")
                else:
                    st.error("❌ 틀린 부분이 있습니다. 아래에서 비교해 보세요.")

                st.markdown("### ✍️ 내가 입력한 말씀 본문 (비교 교정)")
                formatted_diff = diff_html(submitted_text, target_body_words)
                st.markdown(
                    f"<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; font-size: 1.1em; line-height: 2.2;'>{formatted_diff}</div>",
                    unsafe_allow_html=True
                )

                st.markdown("### 📖 정답 말씀 (본문)")
                st.info(target_body_words)
                st.divider()

                if st.session_state.random_current_index + 1 < total_steps:
                    if st.button("다음 문제로 ➡️", type="primary", key="btn_next_tab3"):
                        st.session_state.random_current_index += 1
                        st.session_state.last_submitted_text = ""
                        st.session_state.submitted = False
                        st.session_state.reset_count_tab3 = st.session_state.get("reset_count_tab3", 0) + 1
                        st.rerun()
                else:
                    st.balloons()
                    st.success("✨ 저장된 모든 말씀의 랜덤 테스트를 완료하셨습니다!")
                    if st.button("처음으로 돌아가기", key="btn_finish_tab3"):
                        st.session_state.random_quiz_active = False
                        st.session_state.last_submitted_text = ""
                        st.session_state.submitted = False
                        st.rerun()

            st.divider()
            if st.button("테스트 종료", key="btn_exit_tab3"):
                st.session_state.random_quiz_active = False
                st.session_state.last_submitted_text = ""
                st.session_state.submitted = False
                st.rerun()

# ==========================================
# TAB 4: 교리 요약 (저장 시 '정답:' 자동 제거)
# ==========================================
with tab4:
    st.header("📚 교리 요약 저장 및 테스트")

    st.subheader("1. 교리 문제 및 정답 입력")
    st.caption("💡 각 덩어리(엔터 두 번)의 **첫번째 줄은 문제**, **두번째 줄은 정답**으로 저장됩니다.")
    st.caption("✨ 정답 입력 시 앞에 붙은 '정답:' 부분은 자동으로 제거된 후 저장됩니다.")

    doctrine_raw_input = st.text_area(
        "교리 문제와 정답을 입력하세요:",
        placeholder=(
            "1. 성경은 무엇인가요?\n정답: 성경은 하나님의 영감으로 기록된 말씀입니다.\n\n"
            "2. 하나님은 어떤 분이신가요?\n정답: 하나님은 만물을 창조하신 유일한 창조주이십니다."
        ),
        height=200,
        key="doctrine_input_area"
    )

    if st.button("교리 저장", type="primary", key="btn_save_doctrine"):
        if doctrine_raw_input.strip():
            chunks = [chunk.strip() for chunk in doctrine_raw_input.split("\n\n") if chunk.strip()]
            new_doctrines = []

            for chunk in chunks:
                lines = [line.strip() for line in chunk.split("\n") if line.strip()]
                if len(lines) >= 2:
                    q_text = lines[0]
                    raw_a_text = "\n".join(lines[1:])
                    # 저장 시 '정답:', '정답 :', '정답 -' 등의 무의미한 접두어 자동 제거
                    clean_a_text = re.sub(r'^(정답\s*[:\.-]?\s*)', '', raw_a_text).strip()
                    new_doctrines.append({"question": q_text, "answer": clean_a_text})
                elif len(lines) == 1:
                    new_doctrines.append({"question": lines[0], "answer": ""})

            st.session_state.doctrines.extend(new_doctrines)
            st.success(f"총 {len(new_doctrines)}개의 교리 문제가 새로 저장되었습니다!")
            st.rerun()
        else:
            st.warning("저장할 교리 내용을 입력해주세요.")

    st.divider()

    st.subheader("📋 현재 저장된 교리 목록")
    if not st.session_state.doctrines:
        st.info("아직 저장된 교리가 없습니다.")
    else:
        st.write(f"총 **{len(st.session_state.doctrines)}개**의 교리 문제가 저장되어 있습니다.")
        for idx, doc in enumerate(st.session_state.doctrines, start=1):
            with st.expander(f"문제 {idx}: {doc['question']}"):
                st.write(f"**정답:** {doc['answer']}")

        if st.button("전체 교리 삭제", key="btn_clear_doctrines"):
            st.session_state.doctrines = []
            st.rerun()

    st.divider()

    st.subheader("2. 교리 테스트 진행")
    if not st.session_state.doctrines:
        st.info("저장된 교리 문제가 있어야 테스트를 시작할 수 있습니다.")
    else:
        if not st.session_state.doctrine_quiz_active:
            if st.button("🚀 교리 테스트 시작", type="primary", key="btn_start_doctrine_test"):
                st.session_state.doctrine_current_index = 0
                st.session_state.last_submitted_text = ""
                st.session_state.submitted = False
                st.session_state.doctrine_quiz_active = True
                st.rerun()
        else:
            current_doc = st.session_state.doctrines[st.session_state.doctrine_current_index]
            current_step = st.session_state.doctrine_current_index + 1
            total_steps = len(st.session_state.doctrines)

            st.subheader(f"진행 상황: ({current_step} / {total_steps})")
            st.progress(current_step / total_steps)

            st.markdown(f"#### ❓ 문제: {current_doc['question']}")

            target_check_answer = current_doc['answer']

            input_key = f"input_tab4_{st.session_state.doctrine_current_index}_{st.session_state.get('reset_count_tab4', 0)}"
            user_input = st.text_area(
                "정답을 입력하세요:",
                height=150,
                key=input_key
            )

            col_check, col_retry = st.columns([1, 1])
            with col_check:
                if st.button("확인", type="primary", use_container_width=True, key="btn_check_tab4"):
                    if user_input.strip():
                        st.session_state.last_submitted_text = user_input
                        st.session_state.submitted = True
                        st.session_state.reset_count_tab4 = st.session_state.get("reset_count_tab4", 0) + 1
                        st.rerun()
                    else:
                        st.warning("정답을 입력해 주세요.")

            with col_retry:
                if st.button("🔄 다시 시도", use_container_width=True, key="btn_retry_tab4"):
                    st.session_state.last_submitted_text = ""
                    st.session_state.submitted = False
                    st.session_state.reset_count_tab4 = st.session_state.get("reset_count_tab4", 0) + 1
                    st.rerun()

            if st.session_state.submitted:
                st.divider()
                submitted_text = st.session_state.last_submitted_text

                clean_target = target_check_answer.replace(" ", "").replace("\n", "")
                clean_user = submitted_text.replace(" ", "").replace("\n", "")

                if clean_target == clean_user:
                    st.success("🎉 정답입니다! 참 잘하셨습니다.")
                else:
                    st.error("❌ 틀린 부분이 있습니다. 아래에서 비교해 보세요.")

                st.markdown("### ✍️ 내가 입력한 정답 (비교 교정)")
                formatted_diff = diff_html(submitted_text, target_check_answer)
                st.markdown(
                    f"<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; font-size: 1.1em; line-height: 2.2;'>{formatted_diff}</div>",
                    unsafe_allow_html=True
                )

                st.markdown("### 📖 정답 (기준)")
                st.info(target_check_answer)
                st.divider()

                if st.session_state.doctrine_current_index + 1 < total_steps:
                    if st.button("다음 문제로 ➡️", type="primary", key="btn_next_tab4"):
                        st.session_state.doctrine_current_index += 1
                        st.session_state.last_submitted_text = ""
                        st.session_state.submitted = False
                        st.session_state.reset_count_tab4 = st.session_state.get("reset_count_tab4", 0) + 1
                        st.rerun()
                else:
                    st.balloons()
                    st.success("✨ 저장된 모든 교리 테스트를 완료하셨습니다!")
                    if st.button("처음으로 돌아가기", key="btn_finish_tab4"):
                        st.session_state.doctrine_quiz_active = False
                        st.session_state.last_submitted_text = ""
                        st.session_state.submitted = False
                        st.rerun()

            st.divider()
            if st.button("테스트 종료", key="btn_exit_tab4"):
                st.session_state.doctrine_quiz_active = False
                st.session_state.last_submitted_text = ""
                st.session_state.submitted = False
                st.rerun()