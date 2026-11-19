import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
import base64
import io
from pydub import AudioSegment
from pydub.effects import normalize, compress_dynamic_range

st.set_page_config(page_title="YouTube Explainer & Shorts Maker", layout="wide")
st.title("🎬 YouTube Explainer & Shorts Maker")
st.caption("Raw spoken scripts + cleaned professional voiceover + assets")

# Sidebar keys
with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input("OpenAI API Key", type="password")
    serpapi_key = st.text_input("SerpAPI Key", type="password")
    st.markdown("[Get OpenAI key](https://platform.openai.com/api-keys) · [Get SerpAPI key](https://serpapi.com)")

# Main controls
col1, col2, col3 = st.columns(3)
with col1:
    topic = st.text_input("Video topic / angle", placeholder="e.g. release window rumors, map size, online features")
    brand_name = st.text_input("Brand / Channel name", placeholder="SuperHelper")
with col2:
    video_style = st.radio("Video style", ["Visual / Animated style", "Text-only"])
    video_type = st.selectbox("Length type", ["Short (15–60 sec)", "Explainer"])
with col3:
    if video_type == "Short (15–60 sec)":
        duration = st.slider("Target duration (seconds)", 15, 60, 45)
    else:
        duration = st.slider("Target duration (seconds)", 60, 300, 90)
    tone = st.selectbox("Tone", ["Casual homie conversation", "Energetic", "Confident & chill", "Hype but natural"])

# Key Information
st.subheader("Key Information to Talk About")
key_points = st.text_area(
    "Add specific points, facts, or angles you want in the video (optional)",
    placeholder="Example:\n- Latest map size estimates\n- Online mode changes\n- Expected release window",
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
    voice_style_note = "Write with dramatic pacing, strategic pauses (use ellipses or short sentences), strong emphasis, and trailer-like gravitas."
    st.info("Classic Trailer style active — deep voice + cinematic pacing.")
elif voice_option == "News Creator (clear authoritative)":
    selected_voice = "echo"
    voice_style_note = "Write with clear, steady, professional news-anchor delivery. Short, crisp sentences. Confident and easy to follow."
    st.info("News Creator style active — clear, authoritative delivery.")
elif voice_option == "Deep Professional VO":
    selected_voice = "onyx"
    voice_style_note = "Write with rich, measured, professional narrator pacing."
    st.info("Deep Professional VO style active.")
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

def clean_audio(audio_bytes):
    """Normalize volume and reduce low-end noise / gargling."""
    try:
        audio = AudioSegment.from_file(io.BytesIO(audio_bytes), format="mp3")
        audio = audio.high_pass_filter(80)                          # remove rumble
        audio = compress_dynamic_range(audio, threshold=-20.0, ratio=3.0, attack=5.0, release=50.0)
        audio = normalize(audio)                                    # even out volume
        buffer = io.BytesIO()
        audio.export(buffer, format="mp3", bitrate="192k")
        buffer.seek(0)
        return buffer.read()
    except Exception:
        return audio_bytes  # fallback to original if processing fails

def generate_script(client):
    research = ""
    if serpapi_key:
        try:
            search_queries = [
                "Grand Theft Auto VI release date",
                "GTA 6 map size",
                "GTA 6 online features",
                "Grand Theft Auto 6 trailer breakdown",
                "GTA 6 vs GTA 5 differences",
                "Grand Theft Auto VI news"
            ]
            for q in search_queries[:4]:
                search = GoogleSearch({
                    "q": q,
                    "api_key": serpapi_key,
                    "num": 5
                })
                results = search.get_dict()
                research += f"\n=== {q} ===\n"
                for r in results.get("organic_results", [])[:4]:
                    research += f"- {r.get('title', '')}: {r.get('snippet', '')}\n"
        except Exception:
            research = "Research skipped."

    word_count = int(duration * 2.5)
    key_points_section = f"\nMust naturally cover these points:\n{key_points}\n" if key_points.strip() else ""

    prompt = f"""
You are writing a raw spoken YouTube script that will be read out loud by an AI voice.
The topic is secretly about the upcoming big open-world crime game, but you must NEVER say the words "GTA", "Grand Theft Auto", "GTA 6", "GTA VI", or any direct title.

Style: Casual conversation with a close confident homie, with subtle hints only.
Target length: about {word_count} words ({duration} seconds).
Tone: {tone}

Voice delivery style: {voice_style_note}

Research data (use the facts, never name the game):
{research}

{key_points_section}

Rules:
- Output ONLY the pure spoken script. No titles, no scene directions, no timestamps, no director notes.
- Never mention the game name or abbreviation.
- Make it sound natural when spoken.
- Follow the voice delivery style above for pacing and emphasis.
- Keep it evergreen and well-written.
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
Do NOT use the words GTA or Grand Theft Auto.
Make them curiosity-driven.
Return as a numbered list only.

Topic angle: {topic}
Key points: {key_points[:400] if key_points else 'None'}"""
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
            "content": f"Create exactly 3 short image prompts for the main visual scenes. Do not mention any game name. Optimize for {format_note}. Return as numbered list.\n\nScript:\n{st.session_state.script_output[:2000]}"
        }]
    )
    scene_prompts = [line.strip() for line in prompt_resp.choices[0].message.content.split("\n") 
                     if line.strip() and any(c.isdigit() for c in line[:3])][:3]

    images = []
    for sp in scene_prompts:
        try:
            img = client.images.generate(
                model="gpt-image-2.5-flare",
                prompt=f"Cinematic urban open-world game style scene, modern, high quality, {format_note}: {sp}",
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
Do not mention any game name. Optimize for {format_note}. Bold, high-contrast, clear text space.
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
                prompt=f"YouTube thumbnail, {selected_thumb_style}, bold high-contrast, large text space, cinematic urban style, {format_note}: {tp}",
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
            with st.spinner("Researching and writing raw script..."):
                st.session_state.script_output = generate_script(client)
            st.rerun()

with col_btn2:
    if st.button("🚀 Generate ALL Assets", type="primary"):
        if not openai_key or not topic:
            st.warning("OpenAI key and topic required.")
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
                        # Clean the audio
                        st.session_state.voiceover = clean_audio(speech.content)
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
        st.subheader("AI Voiceover (cleaned & normalized)")
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
