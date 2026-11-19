import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
import base64

st.set_page_config(page_title="YouTube Explainer & Shorts Maker", layout="wide")
st.title("🎬 YouTube Explainer & Shorts Maker")
st.caption("Scripts + AI voiceover + scene images + multi-style thumbnails + title suggestions")

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

# Thumbnail styles (updated)
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

    prompt = f"""
You are a YouTube scriptwriter for "{brand_name}".
Topic: {topic}
Style: {video_style}
Format: {aspect_ratio}
Target length: {duration} seconds (~{word_count} words)
Tone: {tone}
Structure: {structure}

Research:
{research}

Write a natural script + 
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
Script excerpt: {st.session_state.script_output[:1200]}"""
        }],
        temperature=0.7
    )
    text = resp.choices[0].message.content
    return [line.strip() for line in text.split("\n") if line.strip() and any(c.isdigit() for c in line[:3])][:6]

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
            with st.spinner("Generating script + title overlays + voiceover..."):
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
            st.rerun()

# Display results
if st.session_state.script_output:
    st.success(f"Script ready! (Format: {aspect_ratio})")
    st.markdown(st.session_state.script_output)

    plain_script = st.session_state.script_output.split("5 title")[0] if "5 title" in st.session_state.script_output else st.session_state.script_output

    # Title overlays
    st.subheader("Title Text Overlay Suggestions")
    if not st.session_state.title_suggestions and openai_key:
        if st.button("Generate Title Overlay Ideas"):
            client = OpenAI(api_key=openai_key)
            st.session_state.title_suggestions = generate_title_overlays(client)
            st.rerun()

    if st.session_state.title_suggestions:
        for i, title in enumerate(st.session_state.title_suggestions, 1):
            st.write(f"**{i}.** {title}")

    # Voiceover
    if voice_option in ["AI Male", "AI Female"] and selected_voice and openai_key:
        if "voiceover" in st.session_state and st.session_state.voiceover:
            st.audio(st.session_state.voiceover, format="audio/mp3")
            st.download_button("Download Voiceover (MP3)", st.session_state.voiceover,
                               file_name="voiceover.mp3", mime="audio/mp3")
        elif st.button("🔊 Generate AI Voiceover"):
            with st.spinner("Generating voiceover..."):
                try:
                    client = OpenAI(api_key=openai_key)
                    speech = client.audio.speech.create(
                        model="tts-1",
                        voice=selected_voice,
                        input=plain_script[:4000]
                    )
                    st.session_state.voiceover = speech.content
                    st.rerun()
                except Exception as e:
                    st.error(f"Voiceover error: {e}")

    # Scene Images
    st.subheader("AI-Generated Scene Images")
    if st.button("🎨 Generate Scene Images"):
        if openai_key:
            client = OpenAI(api_key=openai_key)
            with st.spinner("Generating scene images..."):
                prompt_resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "user",
                        "content": f"Create exactly 3 short image prompts for the main scenes of this video. Optimize for {format_note}. Return as numbered list.\n\n{st.session_state.script_output[:2500]}"
                    }]
                )
                scene_prompts = [line.strip() for line in prompt_resp.choices[0].message.content.split("\n") 
                                 if line.strip() and any(c.isdigit() for c in line[:3])][:3]

                cols = st.columns(3)
                for idx, sp in enumerate(scene_prompts):
                    try:
                        img = client.images.generate(
                            model="gpt-image-2.5-flare",
                            prompt=f"YouTube video scene, clean modern style, {format_note}: {sp}",
                            size=image_size,
                            n=1
                        )
                        img_bytes = base64.b64decode(img.data[0].b64_json)
                        with cols[idx]:
                            st.image(img_bytes, caption=f"Scene {idx+1}", use_container_width=True)
                            st.download_button(f"Download Scene {idx+1}", img_bytes, f"scene_{idx+1}.png", "image/png", key=f"s{idx}")
                    except Exception:
                        with cols[idx]:
                            st.error(f"Scene {idx+1} failed")

    # Thumbnails
    st.subheader("Thumbnail Generator")
    st.caption(f"Style: {selected_thumb_style} · Format: {aspect_ratio}")
    if st.button("🖼️ Generate Thumbnails"):
        if openai_key:
            client = OpenAI(api_key=openai_key)
            with st.spinner(f"Generating thumbnails ({selected_thumb_style})..."):
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

                cols = st.columns(2)
                for idx, tp in enumerate(thumb_prompts):
                    try:
                        img = client.images.generate(
                            model="gpt-image-2.5-flare",
                            prompt=f"YouTube thumbnail, {selected_thumb_style}, bold high-contrast, large text space, {format_note}: {tp}",
                            size=thumbnail_size,
                            n=1
                        )
                        img_bytes = base64.b64decode(img.data[0].b64_json)
                        with cols[idx]:
                            st.image(img_bytes, caption=f"Thumbnail {idx+1}", use_container_width=True)
                            st.download_button(f"Download Thumb {idx+1}", img_bytes, f"thumbnail_{idx+1}.png", "image/png", key=f"th{idx}")
                    except Exception:
                        with cols[idx]:
                            st.error(f"Thumbnail {idx+1} failed")

    st.download_button("Download Full Script", st.session_state.script_output, file_name="script.txt")

    st.info(f"""
**Finish the video ({aspect_ratio}):**
1. Use the title overlay suggestions on the thumbnail.
2. Set CapCut/Canva project to **{aspect_ratio}**.
3. Add scene images + voiceover + text + logo.
4. Export and upload.
""")
