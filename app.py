"""
app.py — AsKDeX: Qwen3-VL ChatGPT-style UI
Run: python -m streamlit run app.py
"""

import streamlit as st
from PIL import Image
from model import (
    MODEL, get_api_key_display, pil_to_base64_url,
    text_message, image_message, chat_stream,
)

st.set_page_config(
    page_title="AsKDeX AI",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── STYLES ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@300;400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

:root {
    --bg:        #0A0A0A;
    --surface:   #141414;
    --border:    #242424;
    --border-hi: #1D8CF8;
    --text:      #E2E8F0;
    --muted:     #4A5568;
    --blue:      #1D8CF8;
    --blue-glow: rgba(29, 140, 248, 0.18);
}

html, body, [class*="css"] {
    font-family: 'Sora', sans-serif !important;
    background-color: var(--bg) !important;
    color: var(--text) !important;
}

#MainMenu, footer, header { visibility: hidden; }
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stStatusWidget"] { display: none !important; }

/* layout */
.block-container {
    max-width: 760px !important;
    margin: 0 auto !important;
    padding: 0 1rem !important;
}

/* sidebar */
[data-testid="stSidebar"] {
    background: #0D0D0D !important;
    border-right: 1px solid var(--border) !important;
}

/* Hide the default Streamlit chat input, but keep it functional */
[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0 !important;
    left: 0 !important;
    width: 100% !important;
    opacity: 0 !important;
    pointer-events: auto !important;
    z-index: 10000 !important;
    height: 60px !important;
}

/* ── FLOATING PILL BAR (editable visual input) ── */
.input-shell {
    position: fixed;
    bottom: 28px;
    left: 50%;
    transform: translateX(-50%);
    width: min(720px, calc(100vw - 48px));
    z-index: 9999;
    pointer-events: none;
}
.pill-bar {
    display: flex;
    align-items: center;
    gap: 10px;
    background: #161616;
    border: 1px solid #2A2A2A;
    border-radius: 999px;
    padding: 10px 12px 10px 18px;
    box-shadow: 0 8px 40px rgba(0,0,0,0.6);
    transition: border-color 0.2s ease, box-shadow 0.2s ease;
    pointer-events: none;
}
.pill-bar:focus-within {
    border-color: var(--border-hi);
    box-shadow: 0 8px 40px rgba(0,0,0,0.7), 0 0 0 3px var(--blue-glow);
}
.pill-attach {
    color: var(--muted);
    display: flex; align-items: center;
    padding: 4px; border-radius: 6px;
    transition: color 0.15s;
    pointer-events: auto;
    cursor: pointer;
}
.pill-attach:hover { color: var(--blue); }
.pill-input {
    flex: 1;
    background: transparent;
    border: none;
    outline: none;
    color: var(--text);
    font-family: 'Sora', sans-serif;
    font-size: 0.95rem;
    caret-color: var(--blue);
    min-width: 0;
    pointer-events: auto;
}
.pill-input::placeholder { color: var(--muted); }
.pill-send {
    width: 36px; height: 36px; border-radius: 50%;
    background: var(--blue); border: none;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 0 14px rgba(29,140,248,0.4);
    pointer-events: auto;
    cursor: pointer;
    transition: background 0.15s, transform 0.1s;
}
.pill-send:hover { background: #3DA0FF; transform: scale(1.06); }
.pill-send svg { fill: #000; width: 15px; height: 15px; }

/* ── chat area ── */
.chat-area { padding: 28px 0 120px; }

.msg-row {
    display: flex; margin-bottom: 26px; gap: 12px;
    animation: fadeUp 0.3s ease-out both;
}
@keyframes fadeUp {
    from { opacity:0; transform:translateY(8px); }
    to   { opacity:1; transform:translateY(0); }
}
.av-wrap {
    width: 32px; height: 32px; border-radius: 8px;
    display: flex; align-items: center; justify-content: center;
    font-weight: 600; flex-shrink: 0;
    font-size: 0.78rem; margin-top: 2px;
}
.av-bot {
    background: linear-gradient(135deg, #1D8CF8, #00C6FF);
    color: #000; box-shadow: 0 0 12px rgba(29,140,248,0.4);
}
.av-user { background: #1A2535; color: #6B9ED0; border: 1px solid #253548; }

.msg-content { line-height: 1.75; font-size: 0.95rem; }
.user-content {
    background: #111B2A; padding: 12px 16px;
    border-radius: 18px 18px 4px 18px;
    max-width: 80%; margin-left: auto;
    border: 1px solid #1A2B42; color: #B8D0F0;
}
.bot-content { color: #C8D8E8; width: 100%; padding-top: 2px; }

pre, code {
    background: #080808 !important; border: 1px solid #1E2D4A !important;
    border-radius: 8px !important;
    font-family: 'JetBrains Mono', monospace !important;
    font-size: 0.88rem !important;
}

/* ── welcome ── */
.welcome-wrap {
    display: flex; flex-direction: column;
    align-items: center; justify-content: center;
    padding-top: 14vh; text-align: center;
}
.welcome-logo {
    font-size: 2.8rem; letter-spacing: -1.5px; font-weight: 600;
    background: linear-gradient(130deg, #1D8CF8, #00C6FF 60%, #7DD3FC);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.35rem; line-height: 1.1;
}
.welcome-sub { color: #3A5070; font-size: 0.95rem; margin-bottom: 2.2rem; }
.suggestion-grid {
    display: grid; grid-template-columns: 1fr 1fr;
    gap: 9px; width: 100%; max-width: 600px;
}
.sug-card {
    border: 1px solid #1A2335; padding: 14px 16px;
    border-radius: 12px; background: #0C1420;
    text-align: left; font-size: 0.87rem; color: #5A7A9A;
    line-height: 1.5; transition: all 0.2s ease;
}
.sug-card:hover {
    background: #0F1C30; border-color: var(--blue);
    color: #A8C8E8; transform: translateY(-2px);
    box-shadow: 0 4px 18px rgba(29,140,248,0.1);
}
.sug-card b { display: block; color: #A8C8E8; margin-bottom: 3px; font-size: 0.9rem; }

/* sidebar buttons */
.stButton > button {
    background: #111 !important; border: 1px solid #222 !important;
    color: #6B9ED0 !important; border-radius: 10px !important;
    font-family: 'Sora', sans-serif !important; font-size: 0.86rem !important;
    transition: all 0.18s ease !important;
}
.stButton > button:hover {
    background: #161F2E !important; border-color: var(--blue) !important;
    color: #B0D0F0 !important;
}

@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }
</style>
""", unsafe_allow_html=True)

# ── SESSION STATE ─────────────────────────────────────────────────────────────
for k, v in [("messages", []), ("api_messages", []), ("pending_img_b64", None)]:
    if k not in st.session_state:
        st.session_state[k] = v

# ── SIDEBAR ───────────────────────────────────────────────────────────────────
# Read the API key fresh every render so the status dot is always accurate.
_api_key = get_api_key_display()

with st.sidebar:
    st.markdown("""
        <div style="padding:0 0 10px;">
            <h2 style="color:#1D8CF8;margin-bottom:2px;font-size:2rem;">✦ AsKDeX</h2>
            <p style="font-size:0.8rem;color:#3A5070;margin:0;">Qwen3-VL · 235B A22B Thinking</p>
        </div>
    """, unsafe_allow_html=True)

    if st.button("＋  New Conversation", use_container_width=True):
        st.session_state.messages = []
        st.session_state.api_messages = []
        st.session_state.pending_img_b64 = None
        st.rerun()

    st.markdown("<hr style='border-color:#1A2335;margin:14px 0;'>", unsafe_allow_html=True)
    st.markdown("<p style='font-size:1rem;color:#3A5070;margin-bottom:6px;'>📎 Attach Image</p>", unsafe_allow_html=True)
    uploaded = st.file_uploader("img", type=["png","jpg","jpeg","webp"], label_visibility="collapsed")
    if uploaded:
        pil_img = Image.open(uploaded)
        st.image(pil_img, use_container_width=True)  # Fixed: use_column_width is deprecated
        uploaded.seek(0)
        st.session_state.pending_img_b64 = pil_to_base64_url(Image.open(uploaded))
    else:
        st.session_state.pending_img_b64 = None

    st.markdown("<hr style='border-color:#1A2335;margin:14px 0;'>", unsafe_allow_html=True)
    dot = "🔵" if _api_key else "🔴"
    st.markdown(f"<p style='font-size:0.7rem;color:#2A4060;'>{dot} {'Connected' if _api_key else 'No API Key'}</p>", unsafe_allow_html=True)
    st.markdown(f"<p style='font-size:0.7rem;color:#2A4060;'>Model: {MODEL}</p>", unsafe_allow_html=True)

# ── MESSAGE RENDERING ─────────────────────────────────────────────────────────
def render_user_message(content: str, img_b64: str | None = None):
    """Render a user bubble. Content is plain text — escaped before injection."""
    import html as _html
    safe_content = _html.escape(content).replace("\n", "<br>")
    img_tag = (
        f'<img src="{img_b64}" style="width:100%;border-radius:10px;margin-bottom:9px;display:block;"/>'
        if img_b64 else ""
    )
    st.markdown(f"""
    <div class="msg-row" style="flex-direction:row-reverse;">
        <div class="av-wrap av-user">U</div>
        <div class="user-content msg-content">{img_tag}{safe_content}</div>
    </div>""", unsafe_allow_html=True)


def render_bot_message(content: str):
    """Render an assistant bubble using st.markdown for proper markdown support."""
    col_av, col_msg = st.columns([0.06, 0.94])
    with col_av:
        st.markdown(
            '<div class="av-wrap av-bot" style="margin-top:4px;">D</div>',
            unsafe_allow_html=True,
        )
    with col_msg:
        # st.markdown handles code blocks, bold, tables, etc. correctly
        st.markdown(content)


# ── MAIN CHAT AREA ────────────────────────────────────────────────────────────
st.markdown('<div class="chat-area">', unsafe_allow_html=True)

if not st.session_state.messages:
    st.markdown("""
    <div class="welcome-wrap">
        <div class="welcome-logo">✦ AsKDeX</div>
        <p class="welcome-sub">What can I help you with?</p>
        <div class="suggestion-grid">
            <div class="sug-card"><b>🎨 Creative Vision</b>Describe a scene and suggest improvements.</div>
            <div class="sug-card"><b>📜 OCR Extract</b>Turn a document photo into clean text.</div>
            <div class="sug-card"><b>🐍 Debug Code</b>Analyze a screenshot to find the error.</div>
            <div class="sug-card"><b>📊 Data Insights</b>Explain the trends in this chart.</div>
        </div>
    </div>""", unsafe_allow_html=True)
else:
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            render_user_message(msg["content"], msg.get("img_b64"))
        else:
            render_bot_message(msg["content"])

st.markdown('</div>', unsafe_allow_html=True)

# ── VISUAL PILL BAR (editable, robust submit) ─────────────────────────────────
st.markdown("""
<div class="input-shell">
    <div class="pill-bar" id="pillBar">
        <span class="pill-attach" id="attachIcon" title="Attach image (open sidebar)">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none"
                 stroke="currentColor" stroke-width="2"
                 stroke-linecap="round" stroke-linejoin="round">
                <path d="M21.44 11.05l-9.19 9.19a6 6 0 0 1-8.49-8.49l9.19-9.19a4 4 0 0 1 5.66 5.66l-9.2 9.19a2 2 0 0 1-2.83-2.83l8.49-8.48"/>
            </svg>
        </span>
        <input class="pill-input" id="pillInput" type="text"
               placeholder="Ask anything" autofocus />
        <button class="pill-send" id="pillSend" title="Send">
            <svg viewBox="0 0 24 24"><path d="M2 21l21-9L2 3v7l15 2-15 2v7z"/></svg>
        </button>
    </div>
</div>

<script>
(function() {
    function init() {
        const realInput = document.querySelector('[data-testid="stChatInput"] textarea');
        if (!realInput) {
            setTimeout(init, 100);
            return;
        }

        const pillInput = document.getElementById('pillInput');
        const pillSend = document.getElementById('pillSend');
        const attachIcon = document.getElementById('attachIcon');

        function setRealInputValue(value) {
            const setter = Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set;
            setter.call(realInput, value);
            realInput.dispatchEvent(new Event('input', { bubbles: true }));
            realInput.dispatchEvent(new Event('change', { bubbles: true }));
        }

        pillInput.addEventListener('input', function() {
            setRealInputValue(pillInput.value);
        });

        realInput.addEventListener('input', function() {
            pillInput.value = realInput.value;
        });

        function submitMessage() {
            if (!pillInput.value.trim()) return;
            realInput.focus();
            const enterEvent = new KeyboardEvent('keydown', {
                key: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true
            });
            realInput.dispatchEvent(enterEvent);
            const keypressEvent = new KeyboardEvent('keypress', {
                key: 'Enter', keyCode: 13, which: 13, bubbles: true, cancelable: true
            });
            realInput.dispatchEvent(keypressEvent);
            pillInput.value = '';
            setRealInputValue('');
        }

        pillInput.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitMessage();
            }
        });

        pillSend.addEventListener('click', function() {
            submitMessage();
        });

        attachIcon.addEventListener('click', function() {
            const btn = document.querySelector('[data-testid="stSidebarNavButton"]')
                     || document.querySelector('[data-testid="stSidebarCollapsedControl"]');
            if (btn) btn.click();
        });

        pillInput.value = realInput.value;
    }

    init();
})();
</script>
""", unsafe_allow_html=True)

# ── REAL CHAT INPUT (invisible but functional) ───────────────────────────────
if prompt := st.chat_input("Ask anything"):
    if not _api_key:
        st.error("⚠️ API key missing. Add OPENROUTER_API_KEY to your env file.")
        st.stop()

    img_b64 = st.session_state.get("pending_img_b64")

    # Append user message to display history
    st.session_state.messages.append({"role": "user", "content": prompt, "img_b64": img_b64})

    # Build API message (with or without image)
    api_msg = image_message("user", prompt, img_b64) if img_b64 else text_message("user", prompt)
    st.session_state.api_messages.append(api_msg)

    # Clear the pending image so it isn't re-attached to the next message
    st.session_state.pending_img_b64 = None

    # ── STREAM RESPONSE ──────────────────────────────────────────────────────
    # Render user message immediately, then stream bot response below it.
    render_user_message(prompt, img_b64)

    col_av, col_msg = st.columns([0.06, 0.94])
    with col_av:
        st.markdown(
            '<div class="av-wrap av-bot" style="margin-top:4px;">D</div>',
            unsafe_allow_html=True,
        )
    with col_msg:
        message_placeholder = st.empty()
        full_response = ""
        try:
            for chunk in chat_stream(st.session_state.api_messages, max_tokens=2048, temperature=0.7):
                full_response += chunk
                # Show streaming text with a blinking cursor appended as plain text
                message_placeholder.markdown(full_response + "▌")
            # Final render without cursor
            message_placeholder.markdown(full_response)
        except Exception as e:
            error_msg = f"⚠️ Error communicating with the API: {e}"
            message_placeholder.error(error_msg)
            # Don't save a failed response to history
            st.stop()

    # Persist the completed response
    st.session_state.messages.append({"role": "assistant", "content": full_response})
    st.session_state.api_messages.append({"role": "assistant", "content": full_response})