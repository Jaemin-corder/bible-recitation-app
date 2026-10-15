import streamlit as st
import difflib

# 페이지 기본 설정
st.set_page_config(
    page_title="말씀 암송 도우미",
    page_icon="📖",
    layout="centered"
)

# 세션 상태 초기화
if "verses" not in st.session_state:
    st.session_state.verses = []

if "quiz_active" not in st.session_state:
    st.session_state.quiz_active = False
if "selected_range" not in st.session_state:
    st.session_state.selected_range = []
if "current_index" not in st.session_state:
    st.session_state.current_index = 0

# 암송 입력창 및 결과 세션 관리
if "user_text" not in st.session_state:
    st.session_state.user_text = ""
if "last_submitted_text" not in st.session_state:
    st.session_state.last_submitted_text = ""
if "submitted" not in st.session_state:
    st.session_state.submitted = False


def diff_html(user_str, target_str):
    """
    유저가 입력한 텍스트와 정답 텍스트를 비교하여
    틀린 부분에 빨간색 취소선(~text~)과 올바른 텍스트(^correct^)를 HTML 형태로 생성합니다.
    """
    s = difflib.SequenceMatcher(None, user_str, target_str)
    user_diff_html = []

    for tag, i1, i2, j1, j2 in s.get_opcodes():
        if tag == 'equal':
            # 일치하는 부분 (엔터/줄바꿈 보존)
            user_diff_html.append(user_str[i1:i2].replace("\n", "<br>"))
        elif tag == 'replace':
            # 틀린 글자/단어: 유저 입력값에는 빨간 중간선, 위에 정답 글자를 빨간 글씨로 표시
            wrong_part = user_str[i1:i2].replace("\n", "<br>")
            correct_part = target_str[j1:j2].replace("\n", " ")
            user_diff_html.append(
                f"<span style='display:inline-block; text-align:center; vertical-align:bottom; margin: 0 2px;'>"
                f"<sup style='color:#e63946; font-weight:bold; font-size: 0.85em;'>{correct_part}</sup><br>"
                f"<del style='color:#e63946; text-decoration: line-through;'>{wrong_part}</del>"
                f"</span>"
            )
        elif tag == 'delete':
            # 유저가 불필요하게 추가한 글자
            wrong_part = user_str[i1:i2].replace("\n", "<br>")
            user_diff_html.append(
                f"<del style='color:#e63946; text-decoration: line-through;'>{wrong_part}</del>"
            )
        elif tag == 'insert':
            # 유저가 빠뜨린 글자
            missing_part = target_str[j1:j2].replace("\n", " ")
            user_diff_html.append(
                f"<span style='color:#e63946; font-weight:bold;'>[{missing_part}]</span>"
            )

    return "".join(user_diff_html)


st.title("📖 말씀 암송 도우미")

# 탭 구성
tab1, tab2 = st.tabs(["📝 말씀 저장", "🧠 암송 테스트"])

# ==========================================
# TAB 1: 말씀 저장
# ==========================================
with tab1:
    st.header("말씀 입력 및 저장")
    st.caption("💡 말씀과 말씀 사이에 **빈 줄(엔터 두 번)**을 넣어주시면 자동으로 나누어 저장됩니다.")

    raw_input = st.text_area(
        "말씀들을 한 번에 입력하세요:",
        placeholder=(
            "요한복음 3:16\n하나님이 세상을 이처럼 사랑하사 독생자를 주셨으니...\n\n"
            "시편 23:1\n여호와는 나의 목자시니 내게 부족함이 없으리로다...\n\n"
            "로마서 8:28\n우리가 알거니와 하나님을 사랑하는 자..."
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
# TAB 2: 암송 테스트
# ==========================================
with tab2:
    st.header("말씀 암송하기")

    if not st.session_state.verses:
        st.warning("저장된 말씀이 없습니다. '말씀 저장' 탭에서 먼저 말씀을 추가해주세요.")
    else:
        total_count = len(st.session_state.verses)

        # 암송 시작 전 화면
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
                    st.session_state.user_text = ""
                    st.session_state.last_submitted_text = ""
                    st.session_state.submitted = False
                    st.session_state.quiz_active = True
                    st.rerun()
            else:
                st.info("암송할 말씀을 최소 하나 이상 클릭해서 선택해주세요.")

        # 암송 진행 중 화면
        else:
            current_verse_pos = st.session_state.selected_range[st.session_state.current_index]
            target_verse = st.session_state.verses[current_verse_pos]
            current_step = st.session_state.current_index + 1
            total_steps = len(st.session_state.selected_range)

            st.subheader(f"진행 상황: ({current_step} / {total_steps}) - 말씀 {current_verse_pos + 1}번")
            st.progress(current_step / total_steps)

            # 입력 창 (제출 시 빈 문자열로 초기화하기 위해 key dynamic 지정)
            input_key = f"input_{st.session_state.current_index}_{st.session_state.get('reset_count', 0)}"
            user_input = st.text_area(
                "기억나는 말씀을 입력하세요:",
                height=150,
                key=input_key
            )

            col_check, col_retry = st.columns([1, 1])
            with col_check:
                if st.button("확인", type="primary", use_container_width=True):
                    if user_input.strip():
                        st.session_state.last_submitted_text = user_input
                        st.session_state.submitted = True
                        # 확인 시 입력창 비우기
                        st.session_state.reset_count = st.session_state.get("reset_count", 0) + 1
                        st.rerun()
                    else:
                        st.warning("말씀을 입력해 주세요.")

            with col_retry:
                if st.button("🔄 다시 시도", use_container_width=True):
                    st.session_state.last_submitted_text = ""
                    st.session_state.submitted = False
                    st.session_state.reset_count = st.session_state.get("reset_count", 0) + 1
                    st.rerun()

            # 결과 비교 및 출력 영역
            if st.session_state.submitted:
                st.divider()
                submitted_text = st.session_state.last_submitted_text

                clean_target = target_verse.replace(" ", "").replace("\n", "")
                clean_user = submitted_text.replace(" ", "").replace("\n", "")

                if clean_target == clean_user:
                    st.success("🎉 완전 일치합니다! 참 잘하셨습니다.")
                else:
                    st.error("❌ 틀린 부분이 있습니다. 아래에서 비교해 보세요.")

                # 1. 내가 입력한 말씀 & 틀린 부분 교정 표시
                st.markdown("### ✍️ 내가 입력한 말씀 (비교 교정)")
                formatted_diff = diff_html(submitted_text, target_verse)
                st.markdown(
                    f"<div style='background-color: #f8f9fa; padding: 15px; border-radius: 8px; font-size: 1.1em; line-height: 2.2;'>{formatted_diff}</div>",
                    unsafe_allow_html=True
                )

                # 2. 올바른 정답 말씀
                st.markdown("### 📖 정답 말씀")
                st.info(target_verse)

                st.divider()

                # 다음 말씀으로 이동
                if st.session_state.current_index + 1 < total_steps:
                    if st.button("다음 말씀으로 ➡️", type="primary"):
                        st.session_state.current_index += 1
                        st.session_state.last_submitted_text = ""
                        st.session_state.submitted = False
                        st.session_state.reset_count = st.session_state.get("reset_count", 0) + 1
                        st.rerun()
                else:
                    st.balloons()
                    st.success("✨ 선택한 모든 말씀 암송이 끝났습니다!")
                    if st.button("처음으로 돌아가기"):
                        st.session_state.quiz_active = False
                        st.session_state.last_submitted_text = ""
                        st.session_state.submitted = False
                        st.rerun()

            st.divider()
            if st.button("암송 종료"):
                st.session_state.quiz_active = False
                st.session_state.last_submitted_text = ""
                st.session_state.submitted = False
                st.rerun()