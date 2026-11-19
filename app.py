import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
import base64

st.set_page_config(page_title="YouTube Explainer & Shorts Maker", layout="wide")
st.title("🎬 YouTube Explainer & Shorts Maker")
st.caption("Raw spoken scripts in refined Vice City homie voice + voiceover + assets + banners")

# Sidebar keys
with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input("OpenAI API Key", type="password")
    serpapi_key = st.text_input("SerpAPI Key", type="password")
    st.markdown("[Get OpenAI key](https://platform.openai.com/api-keys) · [Get SerpAPI key](https://serpapi.com)")

# Main controls
col1, col2, col3 = st.columns(3)
with col1:
    topic = st.text_input("Video topic / angle", placeholder="e.g. release window, map size, online features, Lucia & Jason")
    brand_name = st.text_input("Brand / Channel name", placeholder="Vice Grift AI")
with col2:
    video_style = st.radio("Video style", ["Visual / Animated style", "Text-only"])
    video_type = st.selectbox("Length type", ["Short (15–60 sec)", "Explainer"])
with col3:
    if video_type == "Short (15–60 sec)":
        duration = st.slider("Target duration (seconds)", 15, 60, 45)
    else:
        duration = st.slider("Target duration (seconds)", 60, 300, 90)
    tone = st.selectbox("Tone", ["Casual homie conversation", "Energetic", "Confident & chill", "Hype but natural"])

# Vice City Homie Blurb
st.subheader("Vice City Homie Blurb (Primary Source)")
st.caption("Paste any notes, facts, angles, or rough ideas. OpenAI + SerpAPI will turn this into a natural spoken script in the laid-back urban hip-hop voice of Vice City homies.")
homie_blurb = st.text_area(
    "Enter your blurb here",
    placeholder="Example:\nJust dropped. Lucia and Jason running Leonida. Whole state lit. Cameras everywhere. Biggest one yet. Need a 50-second hype for the channel.",
    height=160
)

# Additional Key Points
st.subheader("Additional Key Points (optional)")
key_points = st.text_area(
    "Extra specific points to weave in",
    placeholder="Example:\n- Map bigger than previous entries\n- Online features teased\n- Release reactions",
    height=100
)

# Aspect Ratio
st.subheader("Video Dimensions")
aspect_ratio = st.radio(
    "Select video format",
    ["9:16 (YouTube Shorts / Vertical)", "16:9 (Explainer Videos / Horizontal)"],
    horizontal=True
)

is_vertical = "9:16" in aspect_ratio
image_size = "1024x1792" if is_vertical else "1792x1024"
thumbnail_size = image_size
format_note = "vertical 9:16 Shorts" if is_vertical else "horizontal 16:9 explainer"

# Thumbnail styles
st.subheader("Thumbnail Style")
thumbnail_styles = [
    "Bold & Dramatic (high contrast, intense)",
    "Minimalist & Clean",
    "Colorful & Energetic",
    "Professional & Trustworthy",
    "Curiosity-driven (mystery / question)",
    "Fun & Playful",
    "Urban Cinematic Action (bold colors, dramatic lighting, high contrast)"
]
selected_thumb_style = st.selectbox("Choose thumbnail style", thumbnail_styles)

# Brand Banner Generator
st.subheader("Brand Banner Generator (1500 × 500)")
st.caption("Wide banners for X (Twitter) and YouTube channel headers")

banner_style = st.selectbox(
    "Banner style",
    [
        "Urban Cinematic Night (neon, rain, luxury)",
        "Bold & High Contrast",
        "Minimalist Dark",
        "Neon Cyberpunk City",
        "Luxury & Wealth",
        "Street Hustle Energy"
    ]
)

if st.button("🖼️ Generate Brand Banner (1500×500 style)"):
    if not openai_key or not brand_name:
        st.warning("OpenAI key and Brand Name are required.")
    else:
        client = OpenAI(api_key=openai_key)
        with st.spinner("Generating wide brand banner..."):
            banner_prompt = f"""
Wide cinematic banner, 3:1 aspect ratio, perfect for X/Twitter and YouTube channel header.
Brand: {brand_name}
Theme: {banner_style}
Include the brand name "{brand_name}" in bold, stylish, high-impact text.
Urban open-world lifestyle energy, dramatic lighting, high quality, photorealistic.
No other text. Clean composition with space for the brand name.
"""
            try:
                img = client.images.generate(
                    model="gpt-image-2.5-flare",
                    prompt=banner_prompt,
                    size="1792x1024",
                    n=1
                )
                img_bytes = base64.b64decode(img.data[0].b64_json)
                st.session_state.banner = img_bytes
                st.success("Banner generated! (1792×1024 — closest to 1500×500)")
            except Exception as e:
                st.error(f"Banner generation failed: {e}")

if "banner" in st.session_state and st.session_state.banner:
    st.image(st.session_state.banner, caption=f"{brand_name} — Brand Banner", use_container_width=True)
    st.download_button(
        "Download Banner (PNG)",
        st.session_state.banner,
        file_name=f"{brand_name.replace(' ', '_')}_banner.png",
        mime="image/png"
    )

# Voice options
st.subheader("Voiceover Style")
voice_option = st.radio(
    "Voice type",
    [
        "Classic Trailer (deep cinematic)",
        "News Creator (clear authoritative)",
        "Deep Professional VO",
        "AI Male",
        "AI Female",
        "Upload my own voice"
    ],
    horizontal=True
)

ai_male_voices = {
    "onyx": "Deep & authoritative",
    "echo": "Clear & steady",
    "fable": "Warm storyteller",
    "ash": "Energetic",
    "cedar": "Rich & grounded"
}
ai_female_voices = {
    "nova": "Bright & energetic",
    "shimmer": "Soft & gentle",
    "coral": "Warm & friendly",
    "sage": "Calm & professional"
}

selected_voice = None
voice_style_note = ""

if voice_option == "Classic Trailer (deep cinematic)":
    selected_voice = "onyx"
    voice_style_note = "Write with dramatic pacing, strategic pauses, strong emphasis, and trailer-like gravitas."
elif voice_option == "News Creator (clear authoritative)":
    selected_voice = "echo"
    voice_style_note = "Write with clear, steady, professional news-anchor delivery."
elif voice_option == "Deep Professional VO":
    selected_voice = "onyx"
    voice_style_note = "Write with rich, measured, professional narrator pacing."
elif voice_option == "AI Male":
    selected_voice = st.selectbox("Choose male voice", list(ai_male_voices.keys()),
                                   format_func=lambda x: f"{x} – {ai_male_voices[x]}")
elif voice_option == "AI Female":
    selected_voice = st.selectbox("Choose female voice", list(ai_female_voices.keys()),
                                   format_func=lambda x: f"{x} – {ai_female_voices[x]}")
else:
    uploaded_voice = st.file_uploader("Upload your voice recording (mp3/wav)", type=["mp3", "wav", "m4a"])
    if uploaded_voice:
        st.audio(uploaded_voice)

# Session state
if "script_output" not in st.session_state:
    st.session_state.script_output = ""
if "title_suggestions" not in st.session_state:
    st.session_state.title_suggestions = []
if "scene_images" not in st.session_state:
    st.session_state.scene_images = []
if "thumbnails" not in st.session_state:
    st.session_state.thumbnails = []
if "voiceover" not in st.session_state:
    st.session_state.voiceover = None
if "banner" not in st.session_state:
    st.session_state.banner = None

def generate_script(client):
    research = ""
    if serpapi_key:
        try:
            search_base = topic or "Grand Theft Auto VI Vice City Leonida"
            search_queries = [
                f"{search_base} latest",
                "GTA 6 Lucia Jason",
                "Grand Theft Auto VI Leonida",
                "GTA 6 release reviews",
                "Vice City GTA 6"
            ]
            for q in search_queries[:4]:
                search = GoogleSearch({
                    "q": q,
                    "api_key": serpapi_key,
                    "num": 4
                })
                results = search.get_dict()
                research += f"\n=== {q} ===\n"
                for r in results.get("organic_results", [])[:3]:
                    research += f"- {r.get('title', '')}: {r.get('snippet', '')}\n"
        except Exception:
            research = "Research skipped."

    word_count = int(duration * 2.5)
    blurb_section = f"\nPRIMARY SOURCE BLURB (use this as the main foundation):\n{homie_blurb}\n" if homie_blurb.strip() else ""
    key_points_section = f"\nAdditional points to weave in naturally:\n{key_points}\n" if key_points.strip() else ""

    prompt = f"""
You are writing a raw spoken YouTube script that will be read out loud by an AI voice.

STYLE (mandatory): Laid-back urban hip-hop voice of someone from Vice City. 
Talk like you're catching up with your people — chill, confident, unforced. 
Use natural slang only when it fits (e.g. locked in, outside, paper, licks, real ones, stay ready). 
Keep sentences short and conversational. No forced or outdated slang. No try-hard energy.

Target length: about {word_count} words ({duration} seconds).
Tone: {tone}
Brand/Channel: {brand_name}

Topic/Angle: {topic}

{blurb_section}

Research (pull useful facts, keep the voice natural):
{research}

{key_points_section}

Voice delivery note: {voice_style_note}

Rules:
- Output ONLY the pure spoken script. No titles, no scene directions, no timestamps, no director notes.
- Make it sound natural when spoken out loud — like a real conversation.
- Prioritize the blurb as the core content.
- You can reference Vice City, Leonida, Lucia, Jason, and the big open-world game when it fits, but keep the delivery relaxed and homie-style.
- End with a natural call to stay locked in with the channel if it flows.
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.75
    )
    return response.choices[0].message.content

def generate_title_overlays(client):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""Create 6 short, punchy title text overlays (3–7 words) for a YouTube thumbnail.
Make them curiosity-driven and fitting the Vice City homie energy.
Return as a numbered list only.

Topic: {topic}
Blurb excerpt: {homie_blurb[:400] if homie_blurb else 'None'}"""
        }],
        temperature=0.7
    )
    text = resp.choices[0].message.content
    return [line.strip() for line in text.split("\n") if line.strip() and any(c.isdigit() for c in line[:3])][:6]

def generate_scene_images(client):
    prompt_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"Create exactly 3 short image prompts for the main visual scenes. Optimize for {format_note}. Return as numbered list.\n\nScript:\n{st.session_state.script_output[:2000]}"
        }]
    )
    scene_prompts = [line.strip() for line in prompt_resp.choices[0].message.content.split("\n") 
                     if line.strip() and any(c.isdigit() for c in line[:3])][:3]

    images = []
    for sp in scene_prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=f"Cinematic urban open-world Vice City style scene, modern, high quality, {format_note}: {sp}",
                size=image_size,
                n=1
            )
            img_bytes = base64.b64decode(img.data[0].b64_json)
            images.append(img_bytes)
        except Exception:
            images.append(None)
    return images

def generate_thumbnails(client):
    thumb_resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""Create 2 strong YouTube thumbnail prompts in the style: "{selected_thumb_style}".
Optimize for {format_note}. Bold, high-contrast, clear text space.
Return as numbered list.

Angle: {topic}"""
        }]
    )
    thumb_prompts = [line.strip() for line in thumb_resp.choices[0].message.content.split("\n") 
                     if line.strip() and any(c.isdigit() for c in line[:3])][:2]

    thumbs = []
    for tp in thumb_prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=f"YouTube thumbnail, {selected_thumb_style}, bold high-contrast, large text space, cinematic urban Vice City style, {format_note}: {tp}",
                size=thumbnail_size,
                n=1
            )
            img_bytes = base64.b64decode(img.data[0].b64_json)
            thumbs.append(img_bytes)
        except Exception:
            thumbs.append(None)
    return thumbs

# Buttons
col_btn1, col_btn2 = st.columns(2)
with col_btn1:
    if st.button("✨ Generate Script Only"):
        if not openai_key or (not topic and not homie_blurb):
            st.warning("OpenAI key plus either a topic or a blurb is required.")
        else:
            client = OpenAI(api_key=openai_key)
            with st.spinner("Researching and writing raw Vice City homie script..."):
                st.session_state.script_output = generate_script(client)
            st.rerun()

with col_btn2:
    if st.button("🚀 Generate ALL Assets", type="primary"):
        if not openai_key or (not topic and not homie_blurb):
            st.warning("OpenAI key plus either a topic or a blurb is required.")
        else:
            client = OpenAI(api_key=openai_key)
            with st.spinner("Generating ALL assets..."):
                st.session_state.script_output = generate_script(client)
                st.session_state.title_suggestions = generate_title_overlays(client)

                if selected_voice:
                    plain = st.session_state.script_output
                    try:
                        speech = client.audio.speech.create(
                            model="tts-1",
                            voice=selected_voice,
                            input=plain[:4000]
                        )
                        st.session_state.voiceover = speech.content
                    except Exception as e:
                        st.session_state.voiceover = None
                        st.error(f"Voiceover error: {e}")

                st.session_state.scene_images = generate_scene_images(client)
                st.session_state.thumbnails = generate_thumbnails(client)

            st.rerun()

# Display results
if st.session_state.script_output:
    st.success(f"Raw script ready! (Format: {aspect_ratio})")
    st.markdown("**Spoken Script (ready for AI voice):**")
    st.text_area("Script", st.session_state.script_output, height=300)

    if st.session_state.title_suggestions:
        st.subheader("Title Text Overlay Suggestions")
        for i, title in enumerate(st.session_state.title_suggestions, 1):
            st.write(f"**{i}.** {title}")

    if st.session_state.voiceover:
        st.subheader("AI Voiceover")
        st.audio(st.session_state.voiceover, format="audio/mp3")
        st.download_button("Download Voiceover (MP3)", st.session_state.voiceover,
                           file_name="voiceover.mp3", mime="audio/mp3")

    if st.session_state.scene_images:
        st.subheader("Scene Images")
        cols = st.columns(3)
        for idx, img_bytes in enumerate(st.session_state.scene_images):
            if img_bytes:
                with cols[idx]:
                    st.image(img_bytes, caption=f"Scene {idx+1}", use_container_width=True)
                    st.download_button(f"Download Scene {idx+1}", img_bytes, f"scene_{idx+1}.png", "image/png", key=f"s{idx}")

    if st.session_state.thumbnails:
        st.subheader(f"Thumbnails ({selected_thumb_style})")
        cols = st.columns(2)
        for idx, img_bytes in enumerate(st.session_state.thumbnails):
            if img_bytes:
                with cols[idx]:
                    st.image(img_bytes, caption=f"Thumbnail {idx+1}", use_container_width=True)
                    st.download_button(f"Download Thumb {idx+1}", img_bytes, f"thumbnail_{idx+1}.png", "image/png", key=f"th{idx}")

    st.download_button("Download Raw Script", st.session_state.script_output, file_name="script.txt")

    st.info(f"""
**Finish the video ({aspect_ratio}):**
1. Use the title overlay suggestions on the thumbnail.
2. Set CapCut/Canva project to **{aspect_ratio}**.
3. Add scene images + voiceover + text + logo.
4. Export and upload.
""")
