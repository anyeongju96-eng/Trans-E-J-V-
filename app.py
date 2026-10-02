import streamlit as st

from translator import LANGUAGES, TranslationError, get_api_key, translate

MAX_CHARS = 5000
# 이 길이를 넘으면 번역이 오래 걸린다고 미리 안내한다
LONG_TEXT_CHARS = 1500

# 화면 표시용 라벨 (언어 목록 자체는 translator.LANGUAGES가 기준)
LANGUAGE_LABELS = {
    "en": "🇺🇸 English",
    "ja": "🇯🇵 日本語",
    "vi": "🇻🇳 Tiếng Việt",
}

CUSTOM_CSS = """
<style>
/* 번역 결과는 코드 글꼴 대신 본문 글꼴로, 조금 크게 */
.st-key-results [data-testid="stCode"] pre,
.st-key-results [data-testid="stCode"] code {
    font-family: inherit;
    font-size: 1.05rem;
    line-height: 1.7;
}
/* 모바일에서 제목이 어색하게 줄바꿈되지 않도록 */
@media (max-width: 640px) {
    h1 { font-size: 2rem !important; }
}
</style>
"""


def label(code: str) -> str:
    return LANGUAGE_LABELS.get(code, LANGUAGES[code])


@st.cache_data(show_spinner=False)
def cached_translate(text: str, target_langs: tuple[str, ...]) -> dict[str, str]:
    # 같은 입력 + 같은 언어 조합은 API를 다시 호출하지 않는다 (예외는 캐싱되지 않음)
    return translate(text, list(target_langs))


def clear():
    st.session_state.input_text = ""
    st.session_state.results = None
    st.session_state.results_source = None


st.set_page_config(page_title="다국어 번역기", page_icon="🌐", layout="centered")
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
st.session_state.setdefault("results", None)
# 결과가 어떤 입력(텍스트)에서 나온 것인지 기억해, 입력이 바뀌면 안내한다
st.session_state.setdefault("results_source", None)

st.title("🌐 다국어 번역기")
st.caption("영어 · 일본어 · 베트남어로 번역합니다")

has_api_key = bool(get_api_key())
if not has_api_key:
    st.warning("OPENAI_API_KEY가 설정되지 않았습니다. .env 파일 또는 Secrets에 API 키를 추가해 주세요.")

with st.container(border=True):
    # max_chars를 쓰면 한도를 넘는 붙여넣기가 통째로 무시되므로, 입력은 받고 번역 시 막는다
    text = st.text_area(
        "번역할 텍스트",
        key="input_text",
        height=200,
        placeholder="번역할 텍스트를 입력하세요. 원문 언어는 자동으로 감지됩니다.",
        label_visibility="collapsed",
    )
    count = f"{len(text):,} / {MAX_CHARS:,}"
    with st.container(horizontal=True, horizontal_alignment="right"):
        st.caption(f":red[{count}]" if len(text) > MAX_CHARS else count, width="content")

    with st.container(horizontal=True, gap="small"):
        selected = [
            code
            for code in LANGUAGES
            if st.checkbox(label(code), value=True, key=f"lang_{code}", width="content")
        ]

    with st.container(horizontal=True):
        translate_clicked = st.button(
            "번역하기", type="primary", icon=":material/translate:", disabled=not has_api_key
        )
        st.button("지우기", on_click=clear, icon=":material/delete:")

if translate_clicked:
    if not text.strip():
        st.warning("번역할 텍스트를 입력해 주세요.")
    elif len(text) > MAX_CHARS:
        st.warning(f"텍스트는 최대 {MAX_CHARS:,}자까지 번역할 수 있습니다. ({len(text):,}자 입력됨)")
    elif not selected:
        st.warning("번역할 언어를 하나 이상 선택해 주세요.")
    else:
        try:
            spinner_text = "번역 중..."
            if len(text) > LONG_TEXT_CHARS:
                spinner_text = "번역 중... 긴 글은 1~2분 정도 걸릴 수 있습니다."
            with st.spinner(spinner_text):
                st.session_state.results = cached_translate(text.strip(), tuple(selected))
            st.session_state.results_source = text.strip()
        except TranslationError as e:
            st.error(str(e))

with st.container(key="results"):
    results = st.session_state.results
    if results:
        if st.session_state.results_source != text.strip():
            st.caption(":orange[입력이 바뀌었습니다. 아래는 이전 입력의 번역 결과입니다.]")
        tabs = st.tabs([label(code) for code in results])
        for tab, (code, translated) in zip(tabs, results.items()):
            with tab:
                st.code(translated, language=None, wrap_lines=True)
    else:
        st.info("번역 결과가 여기에 표시됩니다. 텍스트를 입력하고 **번역하기**를 눌러 보세요.", icon=":material/info:")
