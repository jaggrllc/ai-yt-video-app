import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
from gtts import gTTS
import base64
import io

st.set_page_config(page_title="YouTube Explainer & Shorts Maker", layout="wide")
st.title("🎬 YouTube Explainer & Shorts Maker")
st.caption("Vice Grift AI style scripts + free Google TTS + safe original branding")

# ---------- Secrets + Sidebar fallback ----------
def get_secret(key: str, label: str):
    """Prefer st.secrets, fall back to sidebar input."""
    if key in st.secrets:
        return st.secrets[key]
    return st.sidebar.text_input(label, type="password")

openai_key = get_secret("OPENAI_API_KEY", "OpenAI API Key")
serpapi_key = get_secret("SERPAPI_KEY", "SerpAPI Key")

st.sidebar.caption("Voiceover uses free Google TTS (no key needed)")
st.sidebar.markdown("---")
st.sidebar.info("Tip: Use `.streamlit/secrets.toml` for production.")

# ---------- Cached OpenAI client ----------
@st.cache_resource
def get_openai_client(api_key: str):
    return OpenAI(api_key=api_key)

# ---------- Session state ----------
defaults = {
    "script_output": "",
    "title_suggestions": [],
    "scene_images": [],
    "thumbnails": [],
    "voiceover": None,
    "banner": None,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

# ---------- Main form ----------
with st.form("main_form"):
    col1, col2, col3 = st.columns(3)
    with col1:
        topic = st.text_input("Video topic / angle")
        brand_name = st.text_input("Brand name", value="Vice Grift AI")
    with col2:
        video_type = st.selectbox("Length type", ["Short (15–60 sec)", "Explainer"])
    with col3:
        if video_type == "Short (15–60 sec)":
            duration = st.slider("Target duration (seconds)", 15, 60, 45)
        else:
            duration = st.slider(
                "Target duration (seconds)",
                60, 3600, 300,
                help="Up to 60 minutes for full explainers"
            )
        tone = st.selectbox("Tone", ["Casual homie conversation", "Energetic", "Confident & chill", "Hype but natural"])

    homie_blurb = st.text_area("Vice Grift Blurb (primary source)", height=140)
    key_points = st.text_area("Additional Key Points (optional)", height=90)

    aspect_ratio = st.radio("Video format", ["9:16 (Shorts)", "16:9 (Explainer)"], horizontal=True)
    selected_thumb_style = st.selectbox("Thumbnail style", [
        "Bold & Dramatic", "Minimalist & Clean", "Colorful & Energetic",
        "Professional", "Curiosity-driven", "Fun & Playful", "Urban Cinematic Action"
    ])
    banner_style = st.selectbox("Banner style", [
        "Urban Cinematic Night", "Bold & High Contrast", "Minimalist Dark",
        "Neon Cyberpunk City", "Luxury & Wealth", "Street Hustle Energy"
    ])
    voice_option = st.radio(
        "Voice",
        ["Google TTS (UK – deeper)", "Google TTS (AU – clearer)", "Upload own voice"],
        horizontal=True
    )

    submitted = st.form_submit_button("🚀 Generate ALL Assets", type="primary")
    script_only = st.form_submit_button("✨ Generate Script Only")

# ---------- Voice upload (outside form) ----------
if voice_option == "Upload own voice":
    uploaded = st.file_uploader("Upload voice", type=["mp3", "wav"])
    if uploaded:
        st.audio(uploaded)

gtts_tld = "co.uk" if "UK" in voice_option else "com.au" if "AU" in voice_option else "com"
is_vertical = "9:16" in aspect_ratio
image_size = "1024x1792" if is_vertical else "1792x1024"
format_note = "vertical" if is_vertical else "horizontal"

ALLOWED_PHRASES = [
    "Vice Grift AI", "Vice Grift AI Channel", "Vice Grifting", "Vice Grift",
    "Vice Grifter", "Vice Grifters", "The Vice Grifting Nation",
    "Let's go, Vice Grifters!", "Yo, Vice Grifters!"
]
FORBIDDEN = """
GTA, GTA 6, GTA VI, Grand Theft Auto, Grand Theft Auto VI, Grand Theft Auto 6,
Vice City, Leonida, Rockstar, Rockstar Games, Take-Two, Take Two,
Lucia, Jason, any Rockstar character or location names, any trademarked game titles.
"""

# ---------- Generation functions ----------
def generate_script(client):
    research = ""
    if serpapi_key:
        try:
            queries = [topic or "open world hustle", "street level scams", "heist open world"]
            for q in queries[:3]:
                res = GoogleSearch({"q": q, "api_key": serpapi_key, "num": 3}).get_dict()
                research += f"\n{q}:\n"
                for r in res.get("organic_results", [])[:2]:
                    research += f"- {r.get('snippet', '')}\n"
        except Exception:
            pass

    prompt = f"""
Write a raw spoken YouTube script in a laid-back urban homie voice focused on hustles, heists, and street-level scams.
Chill, confident, natural. Short sentences.
Length: ~{int(duration * 2.5)} words.
Tone: {tone}
Brand: {brand_name}
Topic: {topic}

Blurb:
{homie_blurb}

Extra points:
{key_points}

Research:
{research}

Use only original language. Do not mention any trademarked game titles or companies.
Output ONLY the spoken script.
"""
    return client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75
    ).choices[0].message.content

def generate_title_overlays(client):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"6 short punchy title overlays. Numbered list only.\n{topic}\n{homie_blurb[:300]}"}]
    )
    return [l.strip() for l in resp.choices[0].message.content.split("\n") if l.strip() and any(c.isdigit() for c in l[:3])][:6]

def safe_image_prompt(base: str) -> str:
    allowed = ", ".join(ALLOWED_PHRASES)
    return f"""{base}
STRICT RULES FOR TEXT:
- You may ONLY use text from this list (use one phrase once if needed): {allowed}
- Do NOT use: {FORBIDDEN}
- Focus on original urban hustle / heist energy. High quality, cinematic.
"""

def generate_scene_images(client):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"3 short original image prompts. Numbered.\n{st.session_state.script_output[:1500]}"}]
    )
    prompts = [l.strip() for l in resp.choices[0].message.content.split("\n") if l.strip() and any(c.isdigit() for c in l[:3])][:3]
    images = []
    for p in prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=safe_image_prompt(f"Cinematic urban hustle scene, {format_note}: {p}"),
                size=image_size, n=1
            )
            images.append(base64.b64decode(img.data[0].b64_json))
        except Exception:
            images.append(None)
    return images

def generate_thumbnails(client):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f'2 thumbnail prompts in style "{selected_thumb_style}". Numbered.'}]
    )
    prompts = [l.strip() for l in resp.choices[0].message.content.split("\n") if l.strip() and any(c.isdigit() for c in l[:3])][:2]
    thumbs = []
    for p in prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=safe_image_prompt(f"YouTube thumbnail, {selected_thumb_style}, bold, {format_note}: {p}"),
                size=image_size, n=1
            )
            thumbs.append(base64.b64decode(img.data[0].b64_json))
        except Exception:
            thumbs.append(None)
    return thumbs

def generate_banner(client):
    prompt = safe_image_prompt(f"""
Wide cinematic banner. Style: {banner_style}.
Urban hustle energy, dramatic lighting.
Use one allowed brand phrase exactly once in bold text.
""")
    try:
        img = client.images.generate(model="gpt-image-2.5-flare", prompt=prompt, size="1792x1024", n=1)
        return base64.b64decode(img.data[0].b64_json)
    except Exception as e:
        st.warning(f"Banner failed: {e}")
        return None

def generate_google_tts(text, tld="com"):
    try:
        tts = gTTS(text=text[:4000], lang="en", tld=tld, slow=False)
        buf = io.BytesIO()
        tts.write_to_fp(buf)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        st.error(f"TTS error: {e}")
        return None

# ---------- Run generation ----------
if submitted or script_only:
    if not openai_key or not (topic or homie_blurb):
        st.warning("OpenAI key + topic or blurb required.")
    else:
        client = get_openai_client(openai_key)
        with st.spinner("Generating..."):
            st.session_state.script_output = generate_script(client)
            if submitted:
                st.session_state.title_suggestions = generate_title_overlays(client)
                if "Upload" not in voice_option:
                    st.session_state.voiceover = generate_google_tts(st.session_state.script_output, gtts_tld)
                st.session_state.scene_images = generate_scene_images(client)
                st.session_state.thumbnails = generate_thumbnails(client)
                st.session_state.banner = generate_banner(client)
        st.rerun()

# ---------- Display ----------
if st.session_state.script_output:
    st.success("Assets ready")
    st.text_area("Script", st.session_state.script_output, height=260)

    if st.session_state.title_suggestions:
        st.subheader("Title Suggestions")
        for i, t in enumerate(st.session_state.title_suggestions, 1):
            st.write(f"**{i}.** {t}")

    if st.session_state.voiceover:
        st.subheader("Google TTS Voiceover")
        st.audio(st.session_state.voiceover, format="audio/mp3")
        st.download_button("Download Voice", st.session_state.voiceover, "voice.mp3", "audio/mp3")

    if st.session_state.banner:
        st.subheader("New Banner")
        st.image(st.session_state.banner, use_container_width=True)
        st.download_button("Download Banner", st.session_state.banner, "banner.png", "image/png")

    if st.session_state.scene_images:
        st.subheader("Scenes")
        cols = st.columns(3)
        for i, img in enumerate(st.session_state.scene_images):
            if img:
                with cols[i]:
                    st.image(img, use_container_width=True)
                    st.download_button(f"Scene {i+1}", img, f"scene_{i+1}.png", "image/png", key=f"s{i}")

    if st.session_state.thumbnails:
        st.subheader("Thumbnails")
        cols = st.columns(2)
        for i, img in enumerate(st.session_state.thumbnails):
            if img:
                with cols[i]:
                    st.image(img, use_container_width=True)
                    st.download_button(f"Thumb {i+1}", img, f"thumb_{i+1}.png", "image/png", key=f"t{i}")

    st.download_button("Download Script", st.session_state.script_output, "script.txt")
