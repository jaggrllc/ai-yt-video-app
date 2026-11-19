import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
import requests
import io

st.set_page_config(page_title="YouTube Explainer & Shorts Maker", layout="wide")
st.title("🎬 YouTube Explainer & Shorts Maker")
st.caption("Scripts + AI voiceover + Pexels stock videos for your new channel")

# Sidebar keys
with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input("OpenAI API Key", type="password")
    serpapi_key = st.text_input("SerpAPI Key", type="password")
    pexels_key = st.text_input("Pexels API Key", type="password")
    st.markdown("[OpenAI](https://platform.openai.com/api-keys) · [SerpAPI](https://serpapi.com) · [Pexels](https://www.pexels.com/api/)")

# Main controls
col1, col2, col3 = st.columns(3)
with col1:
    topic = st.text_input("Video topic", placeholder="How our app saves you 2 hours a day")
    brand_name = st.text_input("Brand / Channel name", placeholder="SuperHelper")
with col2:
    video_style = st.radio("Video style", ["Animated (Pexels stock videos)", "Text-only"])
    video_type = st.selectbox("Length type", ["Short (15–60 sec)", "Explainer"])
with col3:
    if video_type == "Short (15–60 sec)":
        duration = st.slider("Target duration (seconds)", 15, 60, 45)
    else:
        duration = st.slider("Target duration (seconds)", 60, 300, 90)
    tone = st.selectbox("Tone", ["Friendly & clear", "Energetic", "Professional", "Fun & playful"])

# Voice options
st.subheader("Voiceover")
voice_option = st.radio("Voice type", ["AI Male", "AI Female", "Upload my own voice"], horizontal=True)

ai_male_voices = {"onyx": "Deep & authoritative", "echo": "Clear & steady", "fable": "Warm storyteller", "ash": "Energetic"}
ai_female_voices = {"nova": "Bright & energetic", "shimmer": "Soft & gentle", "coral": "Warm & friendly", "sage": "Calm & professional"}

selected_voice = None
if voice_option == "AI Male":
    selected_voice = st.selectbox("Choose male voice", list(ai_male_voices.keys()), format_func=lambda x: f"{x} – {ai_male_voices[x]}")
elif voice_option == "AI Female":
    selected_voice = st.selectbox("Choose female voice", list(ai_female_voices.keys()), format_func=lambda x: f"{x} – {ai_female_voices[x]}")
else:
    uploaded_voice = st.file_uploader("Upload your voice recording (mp3/wav)", type=["mp3", "wav", "m4a"])
    if uploaded_voice:
        st.audio(uploaded_voice)
        st.info("Your voice is ready. You can use this file when editing the final video.")

if st.button("✨ Generate Everything", type="primary"):
    if not openai_key or not topic:
        st.warning("OpenAI key and topic are required.")
        st.stop()

    client = OpenAI(api_key=openai_key)

    # Research
    research = ""
    if serpapi_key:
        with st.spinner("Researching topic..."):
            try:
                search = GoogleSearch({"q": f"{topic} explainer OR how to", "api_key": serpapi_key, "num": 4})
                results = search.get_dict()
                for r in results.get("organic_results", [])[:4]:
                    research += f"- {r.get('title','')}: {r.get('snippet','')}\n"
            except:
                research = "Research skipped."

    # Word count guide (~150 words per minute)
    word_count = int(duration * 2.5)  # ~150 wpm

    structure = "Hook (first 3–5 sec) → One clear idea → Quick payoff → CTA" if duration <= 60 else \
                "Hook → Problem → Solution → How it works / benefits → CTA"

    prompt = f"""
You are a YouTube scriptwriter for the channel "{brand_name}".
Topic: {topic}
Style: {video_style}
Target length: {duration} seconds (about {word_count} words)
Tone: {tone}
Structure: {structure}

Research (use if helpful):
{research}

Write a natural spoken script. Also include:
- 5 title options
- YouTube description + 8–12 hashtags
- Scene-by-scene visual suggestions
{"For each main scene, suggest 1–2 Pexels search keywords for stock video." if "Pexels" in video_style else "Suggest simple text overlays and basic graphics for each part."}
"""

    with st.spinner("Writing script..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        script_output = response.choices[0].message.content

    st.success("Script ready!")
    st.markdown(script_output)

    # Extract plain script for TTS (simple approach)
    plain_script = script_output.split("5 title")[0] if "5 title" in script_output else script_output

    # AI Voiceover
    if voice_option in ["AI Male", "AI Female"] and selected_voice:
        with st.spinner("Generating AI voiceover..."):
            try:
                speech = client.audio.speech.create(
                    model="tts-1",
                    voice=selected_voice,
                    input=plain_script[:4000]  # safety limit
                )
                audio_bytes = speech.content
                st.audio(audio_bytes, format="audio/mp3")
                st.download_button("Download Voiceover (MP3)", audio_bytes, file_name="voiceover.mp3", mime="audio/mp3")
            except Exception as e:
                st.error(f"Voiceover error: {e}")

    # Pexels stock videos
    if "Pexels" in video_style and pexels_key:
        st.subheader("Suggested Pexels Stock Videos")
        keywords = [topic] + ["explainer", "tutorial", "people working", "technology", "success"]
        headers = {"Authorization": pexels_key}

        for kw in keywords[:3]:
            try:
                r = requests.get(
                    "https://api.pexels.com/videos/search",
                    headers=headers,
                    params={"query": kw, "per_page": 4, "orientation": "landscape"}
                )
                if r.status_code == 200:
                    videos = r.json().get("videos", [])
                    if videos:
                        st.write(f"**Search: {kw}**")
                        cols = st.columns(4)
                        for i, vid in enumerate(videos[:4]):
                            with cols[i]:
                                video_files = vid.get("video_files", [])
                                mp4 = next((f for f in video_files if f.get("quality") == "hd" or f.get("quality") == "sd"), video_files[0] if video_files else None)
                                if mp4:
                                    st.video(mp4["link"])
                                    st.caption(f"[Download]({mp4['link']})")
            except Exception as e:
                st.info(f"Pexels search issue for '{kw}'")

    st.download_button("Download Full Script", script_output, file_name="script.txt")

    st.info("""
**Next steps to finish the video:**
1. Download the voiceover.
2. Download the Pexels clips you like (or use text-only style).
3. Drop everything into CapCut, Canva, or InVideo.
4. Add your logo, captions, and music.
""")
