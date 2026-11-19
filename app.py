import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
import base64

st.set_page_config(page_title="YouTube Explainer & Shorts Maker", layout="wide")
st.title("🎬 YouTube Explainer & Shorts Maker")
st.caption("One-click generation of script, voiceover, scene images & thumbnails")

# Sidebar keys
with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input("OpenAI API Key", type="password")
    serpapi_key = st.text_input("SerpAPI Key", type="password")
    st.markdown("[Get OpenAI key](https://platform.openai.com/api-keys) · [Get SerpAPI key](https://serpapi.com)")

# Main controls
col1, col2, col3 = st.columns(3)
with col1:
    topic = st.text_input("Video topic", placeholder="How our app saves you 2 hours a day")
    brand_name = st.text_input("Brand / Channel name", placeholder="SuperHelper")
with col2:
    video_style = st.radio("Video style", ["Visual / Animated style", "Text-only"])
    video_type = st.selectbox("Length type", ["Short (15–60 sec)", "Explainer"])
with col3:
    if video_type == "Short (15–60 sec)":
        duration = st.slider("Target duration (seconds)", 15, 60, 45)
    else:
        duration = st.slider("Target duration (seconds)", 60, 300, 90)
    tone = st.selectbox("Tone", ["Friendly & clear", "Energetic", "Professional", "Fun & playful"])

# ========== NEW: Bot Name / Wake-Up Word ==========
st.subheader("Bot Name / Wake-Up Word")
bot_name = st.text_input(
    "WAKE UP WORD / NAME OF THE BOT",
    placeholder="e.g. Alex, Nova, HelperBot, or just leave blank",
    help="The script will be written as if this named bot is speaking."
)

# Key Information
st.subheader("Key Information to Talk About")
key_points = st.text_area(
    "Add specific points, facts, features, or messages you want in the video (optional)",
    placeholder="Example:\n- Our app has a 30-day free trial\n- Saves an average of 2 hours per day\n- Used by over 50,000 users",
    height=140
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

# Voice options
st.subheader("Voiceover")
voice_option = st.radio("Voice type", ["AI Male", "AI Female", "Upload my own voice"], horizontal=True)

ai_male_voices = {
    "onyx": "Deep & authoritative",
    "echo": "Clear & steady",
    "fable": "Warm storyteller",
    "ash": "Energetic"
}
ai_female_voices = {
    "nova": "Bright & energetic",
    "shimmer": "Soft & gentle",
    "coral": "Warm & friendly",
    "sage": "Calm & professional"
}

selected_voice = None
if voice_option == "AI Male":
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

def generate_script(client):
    research = ""
    if serpapi_key:
        try:
            search = GoogleSearch({
                "q": f"{topic} explainer OR how to OR tips",
                "api_key": serpapi_key,
                "num": 5
            })
            results = search.get_dict()
            for r in results.get("organic_results", [])[:5]:
                research += f"- {r.get('title', '')}: {r.get('snippet', '')}\n"
        except Exception:
            research = "Research skipped."

    word_count = int(duration * 2.5)
    structure = ("Hook (first 3–5 sec) → One clear idea → Quick payoff → CTA" 
                 if duration <= 60 else 
                 "Hook → Problem → Solution → How it works / benefits → CTA")

    visual_instruction = (
        f"For each major scene, give clear visual suggestions optimized for {format_note}."
        if "Visual" in video_style else
        f"Focus on strong on-screen text suitable for {format_note}."
    )

    key_points_section = f"\nIMPORTANT – Must include these key points in the script:\n{key_points}\n" if key_points.strip() else ""

    bot_instruction = ""
    if bot_name.strip():
        bot_instruction = f"""
The video is presented by a bot named "{bot_name}".
Write the script in first person as if {bot_name} is speaking directly to the viewer.
Start with a natural introduction that includes the name if it fits, and keep the personality consistent.
"""

    prompt = f"""
You are a YouTube scriptwriter for "{brand_name}".
Topic: {topic}
Style: {video_style}
Format: {aspect_ratio}
Target length: {duration} seconds (~{word_count} words)
Tone: {tone}
Structure: {structure}
{bot_instruction}

Research:
{research}
{key_points_section}
Write a natural, easy-to-speak script that incorporates the key points above naturally.
Also include:
- 5 title options
- YouTube description + hashtags
- Scene-by-scene breakdown

{visual_instruction}
"""
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.8
    )
    return response.choices[0].message.content

def generate_title_overlays(client):
    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{
            "role": "user",
            "content": f"""Based on this topic and script, create 6 short, punchy title text overlays for a YouTube thumbnail.
Make them 3–7 words, high impact, easy to read.
Return as a numbered list only.

Topic: {topic}
Bot name: {bot_name if bot_name else 'None'}
Key points: {key_points[:500] if key_points else 'None'}
Script excerpt: {st.session_state.script_output[:1200]}"""
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
            "content": f"Create exactly 3 short image prompts for the main scenes of this video. Optimize for {format_note}. Return as numbered list.\n\n{st.session_state.script_output[:2500]}"
        }]
    )
    scene_prompts = [line.strip() for line in prompt_resp.choices[0].message.content.split("\n") 
                     if line.strip() and any(c.isdigit() for c in line[:3])][:3]

    images = []
    for sp in scene_prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=f"YouTube video scene, clean modern style, {format_note}: {sp}",
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

Topic: {topic}"""
        }]
    )
    thumb_prompts = [line.strip() for line in thumb_resp.choices[0].message.content.split("\n") 
                     if line.strip() and any(c.isdigit() for c in line[:3])][:2]

    thumbs = []
    for tp in thumb_prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=f"YouTube thumbnail, {selected_thumb_style}, bold high-contrast, large text space, {format_note}: {tp}",
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
        if not openai_key or not topic:
            st.warning("OpenAI key and topic required.")
        else:
            client = OpenAI(api_key=openai_key)
            with st.spinner("Writing script..."):
                st.session_state.script_output = generate_script(client)
            st.rerun()

with col_btn2:
    if st.button("🚀 Generate ALL Assets", type="primary"):
        if not openai_key or not topic:
            st.warning("OpenAI key and topic required.")
        else:
            client = OpenAI(api_key=openai_key)
            with st.spinner("Generating ALL assets (script, voiceover, scenes, thumbnails)..."):
                st.session_state.script_output = generate_script(client)
                st.session_state.title_suggestions = generate_title_overlays(client)

                if voice_option in ["AI Male", "AI Female"] and selected_voice:
                    plain = st.session_state.script_output.split("5 title")[0] if "5 title" in st.session_state.script_output else st.session_state.script_output
                    try:
                        speech = client.audio.speech.create(
                            model="tts-1",
                            voice=selected_voice,
                            input=plain[:4000]
                        )
                        st.session_state.voiceover = speech.content
                    except Exception:
                        st.session_state.voiceover = None

                st.session_state.scene_images = generate_scene_images(client)
                st.session_state.thumbnails = generate_thumbnails(client)

            st.rerun()

# Display results
if st.session_state.script_output:
    st.success(f"All assets ready! (Format: {aspect_ratio})")
    if bot_name.strip():
        st.info(f"Script written as presented by **{bot_name}**")
    st.markdown(st.session_state.script_output)

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

    st.download_button("Download Full Script", st.session_state.script_output, file_name="script.txt")

    st.info(f"""
**Finish the video ({aspect_ratio}):**
1. Use the title overlay suggestions on the thumbnail.
2. Set CapCut/Canva project to **{aspect_ratio}**.
3. Add scene images + voiceover + text + logo.
4. Export and upload.
""")
