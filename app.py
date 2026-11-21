import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
from gtts import gTTS
import base64
import io

st.set_page_config(page_title="YouTube Explainer & Shorts Maker", layout="wide")
st.title("🎬 YouTube Explainer & Shorts Maker")
st.caption("Vice Grift AI style scripts + free Google TTS + safe original branding")

# Sidebar
with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input("OpenAI API Key", type="password")
    serpapi_key = st.text_input("SerpAPI Key", type="password")
    st.caption("Voiceover uses free Google TTS")

# Main inputs
col1, col2, col3 = st.columns(3)
with col1:
    topic = st.text_input("Video topic / angle")
    brand_name = st.text_input("Brand name", value="Vice Grift AI")
with col2:
    video_type = st.selectbox("Length type", ["Short (15–60 sec)", "Explainer"])
with col3:
    duration = st.slider("Target duration (seconds)", 15, 60, 45) if video_type == "Short (15–60 sec)" else st.slider("Target duration (seconds)", 60, 300, 90)
    tone = st.selectbox("Tone", ["Casual homie conversation", "Energetic", "Confident & chill", "Hype but natural"])

st.subheader("Vice Grift Blurb")
homie_blurb = st.text_area("Primary source material", height=140)

st.subheader("Additional Key Points (optional)")
key_points = st.text_area("Extra points", height=90)

aspect_ratio = st.radio("Video format", ["9:16 (Shorts)", "16:9 (Explainer)"], horizontal=True)
is_vertical = "9:16" in aspect_ratio
image_size = "1024x1792" if is_vertical else "1792x1024"
format_note = "vertical" if is_vertical else "horizontal"

selected_thumb_style = st.selectbox("Thumbnail style", [
    "Bold & Dramatic", "Minimalist & Clean", "Colorful & Energetic",
    "Professional", "Curiosity-driven", "Fun & Playful", "Urban Cinematic Action"
])

banner_style = st.selectbox("Banner style (auto-generated)", [
    "Urban Cinematic Night", "Bold & High Contrast", "Minimalist Dark",
    "Neon Cyberpunk City", "Luxury & Wealth", "Street Hustle Energy"
])

voice_option = st.radio("Voice", ["Google TTS (UK – deeper)", "Google TTS (AU – clearer)", "Upload own voice"], horizontal=True)
gtts_tld = "co.uk" if "UK" in voice_option else "com.au" if "AU" in voice_option else "com"

if "Upload" in voice_option:
    uploaded = st.file_uploader("Upload voice", type=["mp3", "wav"])
    if uploaded:
        st.audio(uploaded)

# Session state
for k in ["script_output", "title_suggestions", "scene_images", "thumbnails", "voiceover", "banner"]:
    if k not in st.session_state:
        st.session_state[k] = "" if k == "script_output" else ([] if "images" in k or "thumb" in k or "suggest" in k else None)

ALLOWED_PHRASES = [
    "Vice Grift AI",
    "Vice Grift AI Channel",
    "Vice Grifting",
    "Vice Grift",
    "Vice Grifter",
    "Vice Grifters",
    "The Vice Grifting Nation",
    "Let's go, Vice Grifters!",
    "Yo, Vice Grifters!"
]

FORBIDDEN = """
GTA, GTA 6, GTA VI, Grand Theft Auto, Grand Theft Auto VI, Grand Theft Auto 6,
Vice City, Leonida, Rockstar, Rockstar Games, Take-Two, Take Two, 
Lucia, Jason, any Rockstar character names, any Rockstar location names,
any trademarked game titles or company names.
"""

def generate_script(client):
    research = ""
    if serpapi_key:
        try:
            queries = [topic or "open world hustle game", "street level scams open world", "heist open world reviews"]
            for q in queries[:3]:
                res = GoogleSearch({"q": q, "api_key": serpapi_key, "num": 3}).get_dict()
                research += f"\n{q}:\n"
                for r in res.get("organic_results", [])[:2]:
                    research += f"- {r.get('snippet', '')}\n"
        except:
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
        messages=[{"role": "user", "content": f"6 short punchy title overlays using original hustle language. Numbered list only.\n{topic}\n{homie_blurb[:300]}"}]
    )
    return [l.strip() for l in resp.choices[0].message.content.split("\n") if l.strip() and any(c.isdigit() for c in l[:3])][:6]

def safe_image_prompt(base: str) -> str:
    allowed = ", ".join(ALLOWED_PHRASES)
    return f"""{base}

STRICT RULES FOR TEXT IN THE IMAGE:
- You may ONLY use text from this exact list (use one phrase once if text is needed): {allowed}
- Do NOT use any of the following words or anything similar: {FORBIDDEN}
- Focus on original urban hustle / heist / street-level scam energy.
- High quality, cinematic, dramatic lighting.
"""

def generate_scene_images(client):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f"3 short original image prompts about hustles and street energy. Numbered list.\n{st.session_state.script_output[:1500]}"}]
    )
    prompts = [l.strip() for l in resp.choices[0].message.content.split("\n") if l.strip() and any(c.isdigit() for c in l[:3])][:3]
    images = []
    for p in prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=safe_image_prompt(f"Cinematic urban hustle scene, {format_note}: {p}"),
                size=image_size,
                n=1
            )
            images.append(base64.b64decode(img.data[0].b64_json))
        except:
            images.append(None)
    return images

def generate_thumbnails(client):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": f'2 original thumbnail prompts in style "{selected_thumb_style}". Numbered.'}]
    )
    prompts = [l.strip() for l in resp.choices[0].message.content.split("\n") if l.strip() and any(c.isdigit() for c in l[:3])][:2]
    thumbs = []
    for p in prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=safe_image_prompt(f"YouTube thumbnail, {selected_thumb_style}, bold, {format_note}: {p}"),
                size=image_size,
                n=1
            )
            thumbs.append(base64.b64decode(img.data[0].b64_json))
        except:
            thumbs.append(None)
    return thumbs

def generate_banner(client):
    prompt = safe_image_prompt(f"""
Wide cinematic banner for channel header.
Style: {banner_style}.
Urban hustle and street energy, dramatic lighting, high quality.
Use one of the allowed brand phrases exactly once in bold stylish text.
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

# Buttons
c1, c2 = st.columns(2)
with c1:
    if st.button("✨ Generate Script Only"):
        if openai_key and (topic or homie_blurb):
            client = OpenAI(api_key=openai_key)
            with st.spinner("Writing script..."):
                st.session_state.script_output = generate_script(client)
            st.rerun()

with c2:
    if st.button("🚀 Generate ALL Assets", type="primary"):
        if openai_key and (topic or homie_blurb):
            client = OpenAI(api_key=openai_key)
            with st.spinner("Generating everything..."):
                st.session_state.script_output = generate_script(client)
                st.session_state.title_suggestions = generate_title_overlays(client)
                if "Upload" not in voice_option:
                    st.session_state.voiceover = generate_google_tts(st.session_state.script_output, gtts_tld)
                st.session_state.scene_images = generate_scene_images(client)
                st.session_state.thumbnails = generate_thumbnails(client)
                st.session_state.banner = generate_banner(client)
            st.rerun()

# Display
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
