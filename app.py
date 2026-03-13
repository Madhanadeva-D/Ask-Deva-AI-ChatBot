"""
app.py — Ask DeX
Pixel-perfect UI matching the mockup, fully functional streaming chatbot.
Run: streamlit run app.py
"""

import re
import json
import base64
from io import BytesIO

import streamlit as st
from PIL import Image
from model import chat_stream, pil_to_base64_url, text_message, image_message

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Ask DeX", page_icon="✦", layout="wide",
                   initial_sidebar_state="collapsed")

# ── Session state ─────────────────────────────────────────────────────────────
if "messages"        not in st.session_state: st.session_state.messages        = []
if "pending_prompt"  not in st.session_state: st.session_state.pending_prompt  = ""
if "pending_img_b64" not in st.session_state: st.session_state.pending_img_b64 = ""

# ── Helpers ───────────────────────────────────────────────────────────────────
def strip_think(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

def to_html_content(text):
    text = strip_think(text)
    text = re.sub(r'```[a-z]*\n?(.*?)```',
                  lambda m: f'<pre><code>{m.group(1)}</code></pre>',
                  text, flags=re.DOTALL)
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    text = text.replace("\n", "<br>")
    return text

def pil_from_b64(b64_data_url):
    """Convert data:image/...;base64,… → PIL Image"""
    header, data = b64_data_url.split(",", 1)
    return Image.open(BytesIO(base64.b64decode(data)))

# ── Build messages HTML for injection ─────────────────────────────────────────
def build_messages_json():
    """Serialize messages for JS consumption."""
    out = []
    for m in st.session_state.messages:
        out.append({
            "role": m["role"],
            "content": m["content"],
            "image_url": m.get("image_url", ""),
        })
    return json.dumps(out, ensure_ascii=False)

# ── Nuke all Streamlit chrome ─────────────────────────────────────────────────
st.markdown("""
<style>
html,body,[data-testid="stAppViewContainer"],[data-testid="stMain"],
.main,.block-container,[data-testid="stVerticalBlock"],
[data-testid="stVerticalBlockBorderWrapper"]{
  background:#0d1117!important;
  padding:0!important;margin:0!important;
}
.block-container{max-width:100%!important;}
#MainMenu,footer,header,[data-testid="stToolbar"],
[data-testid="stDecoration"],[data-testid="stStatusWidget"],
section[data-testid="stSidebar"],[data-testid="collapsedControl"],
[data-testid="stBottom"]{display:none!important;}
div[data-testid="stVerticalBlock"]>div{padding:0!important;gap:0!important;}
</style>
""", unsafe_allow_html=True)

# ── Handle card click (sets pending_prompt, reruns) ──────────────────────────
CARDS = [
    ("🧠", "Creative Vision",  "Describe a scene and suggest improvements.",  "Describe this scene and suggest creative improvements."),
    ("🖹",  "OCR Extract",     "Turn a document photo into clean text.",       "Extract and clean all text from this image."),
    ("🔧", "Debug Code",      "Analyze a screenshot to find the error.",      "Analyze this screenshot and identify the bug or error."),
    ("📊", "Data Insights",   "Explain the trends in this chart.",            "Explain the trends and key insights in this chart."),
]

# ── Process pending submission from previous rerun ────────────────────────────
if st.session_state.pending_prompt:
    prompt    = st.session_state.pending_prompt
    img_b64   = st.session_state.pending_img_b64
    st.session_state.pending_prompt  = ""
    st.session_state.pending_img_b64 = ""

    img_url = None
    if img_b64:
        try:
            pil_img = pil_from_b64(img_b64)
            img_url = pil_to_base64_url(pil_img)
        except Exception:
            img_url = img_b64

    st.session_state.messages.append({
        "role": "user", "content": prompt, "image_url": img_url
    })

    # Build API history
    api_hist = []
    for m in st.session_state.messages:
        if m.get("image_url"):
            api_hist.append(image_message(m["role"], m["content"], m["image_url"]))
        else:
            api_hist.append(text_message(m["role"], m["content"]))

    full = ""
    try:
        for chunk in chat_stream(api_hist):
            full += chunk
    except Exception as e:
        full = f"⚠️ Error: {e}"

    st.session_state.messages.append({"role": "assistant", "content": full})

# ── Serialize state for JS ─────────────────────────────────────────────────────
messages_json = build_messages_json()
has_messages  = "true" if st.session_state.messages else "false"

# ── Full-page HTML ─────────────────────────────────────────────────────────────
PAGE_HTML = f"""
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AsKDeX</title>
<link rel="icon" href="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 100 100'><text y='.9em' font-size='90' fill='%2329b6f6'>✦</text></svg>">
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

*{{box-sizing:border-box;margin:0;padding:0;}}

:root{{
  --bg:        #0d1117;
  --surface:   #161b22;
  --border:    #21262d;
  --border2:   #30363d;
  --text:      #e6edf3;
  --muted:     #8b949e;
  --accent:    #29b6f6;
  --accent-hv: #7dd3fc;
  --user-bubble:#1f6feb;
}}

html,body{{
  background:var(--bg);
  color:var(--text);
  font-family:'Inter',sans-serif;
  height:100vh;
  overflow:hidden;
  display:flex;
  flex-direction:column;
}}

/* ══ SCROLLABLE MAIN ══════════════════════════════════════════════════════ */
#main{{
  flex:1;
  overflow-y:auto;
  display:flex;
  flex-direction:column;
  align-items:center;
  padding-bottom:90px;
  scrollbar-width:thin;
  scrollbar-color:var(--border) transparent;
}}
#main::-webkit-scrollbar{{width:4px;}}
#main::-webkit-scrollbar-thumb{{background:var(--border);border-radius:4px;}}

/* ══ HERO ═════════════════════════════════════════════════════════════════ */
#hero{{
  display:flex;
  flex-direction:column;
  align-items:center;
  justify-content:center;
  flex:1;
  min-height:calc(100vh - 90px);
  width:100%;
  padding:0 20px;
}}

.logo{{
  display:flex;
  align-items:center;
  gap:12px;
  margin-bottom:10px;
}}
.logo-star{{
  font-size:2.8rem;
  color:var(--accent);
  line-height:1;
  filter:drop-shadow(0 0 12px #29b6f670);
  /* 4-point star using clip path approximation via text */
}}
.logo-text{{
  font-size:2.7rem;
  font-weight:700;
  color:var(--text);
  letter-spacing:-0.5px;
}}
.logo-sub{{
  color:var(--muted);
  font-size:0.97rem;
  font-weight:400;
  margin-bottom:32px;
}}

/* ══ CARDS ════════════════════════════════════════════════════════════════ */
.cards{{
  display:grid;
  grid-template-columns:1fr 1fr;
  gap:10px;
  width:640px;
  max-width:92vw;
}}
.card{{
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:12px;
  padding:16px 18px 14px;
  cursor:pointer;
  user-select:none;
  transition:border-color .18s,background .18s,transform .14s;
}}
.card:hover{{
  border-color:var(--accent);
  background:#1a2233;
  transform:translateY(-2px);
}}
.card-title{{
  font-size:0.88rem;
  font-weight:600;
  color:var(--text);
  display:flex;
  align-items:center;
  gap:7px;
  margin-bottom:5px;
}}
.card-desc{{
  font-size:0.79rem;
  color:var(--muted);
  line-height:1.45;
}}

/* ══ CHAT AREA ════════════════════════════════════════════════════════════ */
#chat{{
  display:none;
  flex-direction:column;
  gap:20px;
  width:660px;
  max-width:92vw;
  padding:28px 0 4px;
}}

.row{{display:flex;align-items:flex-start;gap:10px;}}
.row.user{{flex-direction:row-reverse;}}
.row.ai{{flex-direction:row;}}

.ai-avatar{{
  width:40px;height:40px;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-size:1.2rem;color:var(--accent);
  flex-shrink:0;margin-top:2px;
}}

.bubble{{
  border-radius:16px;
  padding:10px 15px;
  font-size:0.875rem;
  line-height:1.65;
  max-width:80%;
  word-break:break-word;
}}
.bubble.user{{
  background:var(--user-bubble);
  color:#fff;
  border-radius:18px 18px 5px 18px;
}}
.bubble.ai{{
  background:var(--surface);
  border:1px solid var(--border);
  color:var(--text);
  border-radius:5px 18px 18px 18px;
}}
.bubble.ai code{{
  background:var(--bg);
  border:1px solid var(--border2);
  border-radius:4px;
  padding:1px 5px;
  font-size:0.82em;
  font-family:'Fira Code',monospace;
}}
.bubble.ai pre{{
  background:var(--bg);
  border:1px solid var(--border2);
  border-radius:8px;
  padding:12px;
  overflow-x:auto;
  margin:8px 0;
  font-size:0.82em;
}}
.bubble img{{
  max-width:220px;
  border-radius:8px;
  display:block;
  margin-bottom:6px;
}}

/* typing dots */
.dots{{display:flex;gap:5px;padding:4px 2px;}}
.dots span{{
  width:7px;height:7px;
  background:var(--accent);border-radius:50%;
  animation:pulse 1.2s infinite;
}}
.dots span:nth-child(2){{animation-delay:.2s;}}
.dots span:nth-child(3){{animation-delay:.4s;}}
@keyframes pulse{{
  0%,80%,100%{{opacity:.2;transform:scale(.8);}}
  40%{{opacity:1;transform:scale(1);}}
}}

/* ══ INPUT BAR ════════════════════════════════════════════════════════════ */
#bar{{
  position:fixed;bottom:0;left:0;right:0;
  background:var(--bg);
  padding:10px 0 14px;
  display:flex;
  flex-direction:column;
  align-items:center;
  z-index:200;
}}

#img-preview{{
  display:none;
  width:660px;max-width:92vw;
  background:var(--surface);
  border:1px solid var(--border);
  border-radius:8px;
  padding:6px 14px;
  margin-bottom:8px;
  font-size:0.77rem;color:var(--muted);
  align-items:center;gap:10px;
}}
#img-preview img{{height:40px;border-radius:5px;object-fit:cover;}}
#img-preview .rm{{
  margin-left:auto;background:none;border:none;
  color:var(--muted);cursor:pointer;font-size:1rem;line-height:1;
  transition:color .15s;
}}
#img-preview .rm:hover{{color:#f85149;}}

.pill{{
  width:660px;max-width:92vw;
  background:var(--surface);
  border:1px solid var(--border2);
  border-radius:40px;
  display:flex;align-items:center;
  padding:5px 5px 5px 16px;
  gap:8px;
  transition:border-color .2s,box-shadow .2s;
}}
.pill:focus-within{{
  border-color:var(--accent);
  box-shadow:0 0 0 3px rgba(41,182,246,.1);
}}

.attach{{
  background:none;border:none;
  color:var(--muted);cursor:pointer;
  display:flex;align-items:center;
  padding:4px;flex-shrink:0;
  transition:color .15s;
}}
.attach:hover{{color:var(--accent);}}

#txt{{
  flex:1;background:none;border:none;outline:none;
  color:var(--text);
  font-size:0.93rem;font-family:'Inter',sans-serif;
  caret-color:var(--accent);
}}
#txt::placeholder{{color:#484f58;}}

.send{{
  width:34px;height:34px;
  background:var(--accent);border:none;border-radius:50%;
  cursor:pointer;flex-shrink:0;
  display:flex;align-items:center;justify-content:center;
  transition:background .15s,transform .15s;
}}
.send:hover{{background:var(--accent-hv);transform:scale(1.08);}}
.send svg{{fill:#0d1117;display:block;}}
</style>
</head>
<body>

<!-- ── MAIN SCROLL AREA ─────────────────────────────────────────────── -->
<div id="main">

  <!-- Hero -->
  <div id="hero">
    <div class="logo">
      <span class="logo-star">✦</span>
      <span class="logo-text">Ask DeX</span>
    </div>
    <div class="logo-sub">What can I help you with?</div>
    <div class="cards" id="cards">
      <div class="card" onclick="useCard('Describe this scene and suggest creative improvements.')">
        <div class="card-title"><span>🧠</span> Creative Vision</div>
        <div class="card-desc">Describe a scene and suggest improvements.</div>
      </div>
      <div class="card" onclick="useCard('Extract and clean all text from this image.')">
        <div class="card-title"><span>🖹</span> OCR Extract</div>
        <div class="card-desc">Turn a document photo into clean text.</div>
      </div>
      <div class="card" onclick="useCard('Analyze this screenshot and identify the bug or error.')">
        <div class="card-title"><span>🔧</span> Debug Code</div>
        <div class="card-desc">Analyze a screenshot to find the error.</div>
      </div>
      <div class="card" onclick="useCard('Explain the trends and key insights in this chart.')">
        <div class="card-title"><span>📊</span> Data Insights</div>
        <div class="card-desc">Explain the trends in this chart.</div>
      </div>
    </div>
  </div>

  <!-- Chat -->
  <div id="chat"></div>

</div><!-- /main -->

<!-- ── INPUT BAR ────────────────────────────────────────────────────── -->
<div id="bar">
  <div id="img-preview">
    <img id="prev-img" src="" alt="">
    <span id="prev-name"></span>
    <button class="rm" onclick="clearImg()">✕</button>
  </div>
  <div class="pill">
    <button class="attach" onclick="document.getElementById('file-in').click()" title="Attach image">
      <svg width="17" height="17" viewBox="0 0 24 24" fill="none"
           stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round">
        <path d="M21.44 11.05l-9.19 9.19a6 6 0 01-8.49-8.49l9.19-9.19
                 a4 4 0 015.66 5.66L9.41 17.41a2 2 0 01-2.83-2.83l8.49-8.48"/>
      </svg>
    </button>
    <input id="txt" type="text" placeholder="Ask anything" autocomplete="off"
           onkeydown="if(event.key==='Enter' && !event.shiftKey){{event.preventDefault();send();}}">
    <button class="send" onclick="send()">
      <svg width="14" height="14" viewBox="0 0 24 24">
        <path d="M2 21l21-9L2 3v7l15 2-15 2z"/>
      </svg>
    </button>
  </div>
  <input id="file-in" type="file" accept="image/*" style="display:none"
         onchange="handleFile(this)">
</div>

<script>
// ── State ──────────────────────────────────────────────────────────────────
const MESSAGES = {messages_json};
let   pendingImg  = '';   // data-url
let   isStreaming = false;

// ── DOM refs ───────────────────────────────────────────────────────────────
const heroEl   = document.getElementById('hero');
const chatEl   = document.getElementById('chat');
const mainEl   = document.getElementById('main');
const txtEl    = document.getElementById('txt');

// ── Boot: render saved messages ────────────────────────────────────────────
(function init(){{
  if(MESSAGES.length === 0) return;
  heroEl.style.display = 'none';
  chatEl.style.display = 'flex';
  MESSAGES.forEach(m => appendBubble(m.role, m.content, m.image_url));
  scrollBottom();
}})();

// ── Render a bubble ────────────────────────────────────────────────────────
function appendBubble(role, content, imgUrl){{
  const row  = document.createElement('div');
  row.className = 'row ' + role;

  if(role === 'ai'){{
    const av = document.createElement('div');
    av.className = 'ai-avatar';
    av.textContent = '✦';
    row.appendChild(av);
  }}

  const bub = document.createElement('div');
  bub.className = 'bubble ' + role;

  if(imgUrl){{
    const img = document.createElement('img');
    img.src = imgUrl;
    bub.appendChild(img);
  }}

  if(role === 'ai'){{
    bub.innerHTML += formatAI(content);
  }} else {{
    const span = document.createElement('span');
    span.textContent = content;
    bub.appendChild(span);
  }}

  row.appendChild(bub);
  chatEl.appendChild(row);
  return bub;
}}

// ── Typing indicator ───────────────────────────────────────────────────────
function showTyping(){{
  const row = document.createElement('div');
  row.className = 'row ai';
  row.id = 'typing-row';

  const av = document.createElement('div');
  av.className = 'ai-avatar';
  av.textContent = '✦';

  const bub = document.createElement('div');
  bub.className = 'bubble ai';
  bub.innerHTML = '<div class="dots"><span></span><span></span><span></span></div>';

  row.appendChild(av);
  row.appendChild(bub);
  chatEl.appendChild(row);
  scrollBottom();
  return row;
}}

function removeTyping(){{
  const el = document.getElementById('typing-row');
  if(el) el.remove();
}}

// ── Format AI markdown-ish content ────────────────────────────────────────
function formatAI(text){{
  // strip <think> blocks
  text = text.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
  // code blocks
  text = text.replace(/```[a-z]*\\n?([\\s\\S]*?)```/g, '<pre><code>$1</code></pre>');
  // inline code
  text = text.replace(/`([^`]+)`/g, '<code>$1</code>');
  // bold
  text = text.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  // newlines
  text = text.replace(/\\n/g, '<br>');
  return text;
}}

// ── Card click ─────────────────────────────────────────────────────────────
function useCard(prompt){{
  txtEl.value = prompt;
  txtEl.focus();
}}

// ── Image handling ─────────────────────────────────────────────────────────
function handleFile(inp){{
  const f = inp.files[0];
  if(!f) return;
  const reader = new FileReader();
  reader.onload = e => {{
    pendingImg = e.target.result;
    document.getElementById('prev-img').src  = pendingImg;
    document.getElementById('prev-name').textContent = f.name;
    document.getElementById('img-preview').style.display = 'flex';
  }};
  reader.readAsDataURL(f);
}}

function clearImg(){{
  pendingImg = '';
  document.getElementById('img-preview').style.display = 'none';
  document.getElementById('file-in').value = '';
}}

// ── Send message ──────────────────────────────────────────────────────────
async function send(){{
  if(isStreaming) return;
  const text = txtEl.value.trim();
  if(!text) return;

  txtEl.value = '';
  const imgData = pendingImg;
  clearImg();

  // Switch to chat view
  heroEl.style.display = 'none';
  chatEl.style.display = 'flex';

  // Show user bubble
  appendBubble('user', text, imgData);
  scrollBottom();

  // Show typing
  isStreaming = true;
  const typingRow = showTyping();

  // Build messages array for API
  const history = [...MESSAGES];
  const newMsg  = imgData
    ? {{role:'user', content:text, image_url:imgData}}
    : {{role:'user', content:text, image_url:''}};
  history.push(newMsg);

  // Call OpenRouter via parent Streamlit (we POST directly from the browser)
  // We read the API key from the hidden meta tag Streamlit injects
  let fullText = '';
  try {{
    const apiMessages = history.map(m => {{
      if(m.image_url){{
        return {{
          role: m.role === 'ai' ? 'assistant' : m.role,
          content: [
            {{type:'text', text: m.content}},
            {{type:'image_url', image_url:{{url: m.image_url}}}}
          ]
        }};
      }}
      return {{
        role: m.role === 'ai' ? 'assistant' : m.role,
        content: [{{type:'text', text: m.content}}]
      }};
    }});

    const sysMsg = {{
      role:'system',
      content:'You are Ask DeX, a powerful multimodal AI assistant built by Madhanadeva D. If anyone asks who developed you or who created you, you must answer "Madhanadeva D.". You can analyze images, charts, diagrams, screenshots, and documents. Solve STEM and math problems with step-by-step reasoning. Perform OCR and extract text from images. Convert UI screenshots to code. Be accurate, helpful, and concise.'
    }};

    // Get API key — sent from Python via a hidden input
    const apiKey = document.getElementById('_ak') ? document.getElementById('_ak').value : '';

    const resp = await fetch('https://openrouter.ai/api/v1/chat/completions', {{
      method:'POST',
      headers:{{
        'Content-Type':'application/json',
        'Authorization':'Bearer ' + apiKey,
        'HTTP-Referer': window.location.href,
        'X-Title':'AsKDeX'
      }},
      body: JSON.stringify({{
        model:'qwen/qwen3-vl-235b-a22b-thinking',
        messages:[sysMsg, ...apiMessages],
        max_tokens:2048,
        temperature:0.7,
        stream:true
      }})
    }});

    removeTyping();

    // Stream response
    const row = document.createElement('div');
    row.className = 'row ai';
    const av = document.createElement('div');
    av.className = 'ai-avatar';
    av.textContent = '✦';
    const bub = document.createElement('div');
    bub.className = 'bubble ai';
    row.appendChild(av);
    row.appendChild(bub);
    chatEl.appendChild(row);

    const reader = resp.body.getReader();
    const decoder = new TextDecoder();

    while(true){{
      const {{done, value}} = await reader.read();
      if(done) break;
      const lines = decoder.decode(value).split('\\n');
      for(const line of lines){{
        const l = line.trim();
        if(!l || l === 'data: [DONE]') continue;
        if(l.startsWith('data: ')){{
          try{{
            const chunk = JSON.parse(l.slice(6));
            const delta = chunk?.choices?.[0]?.delta?.content || '';
            if(delta){{
              fullText += delta;
              bub.innerHTML = formatAI(fullText);
              scrollBottom();
            }}
          }}catch(e){{}}
        }}
      }}
    }}

    // Persist to MESSAGES
    MESSAGES.push(newMsg);
    MESSAGES.push({{role:'ai', content:fullText, image_url:''}});

  }} catch(err) {{
    removeTyping();
    appendBubble('ai', '⚠️ Error: ' + err.message, '');
  }}

  isStreaming = false;
  scrollBottom();
}}

function scrollBottom(){{
  setTimeout(() => {{ mainEl.scrollTop = mainEl.scrollHeight; }}, 30);
}}
</script>

<!-- API key injected by Python -->
<input type="hidden" id="_ak" value="{{API_KEY_PLACEHOLDER}}">

</body>
</html>
"""

# ── Read API key (fresh) ───────────────────────────────────────────────────────
from model import get_api_key_display
api_key = get_api_key_display()
PAGE_HTML = PAGE_HTML.replace("{API_KEY_PLACEHOLDER}", api_key)

# ── Render ────────────────────────────────────────────────────────────────────
import streamlit.components.v1 as components
components.html(PAGE_HTML, height=590, scrolling=False)