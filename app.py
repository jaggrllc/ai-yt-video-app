import streamlit as st
from openai import OpenAI
from serpapi import GoogleSearch
import base64
import io

st.set_page_config(page_title="YouTube Explainer & Shorts Maker", layout="wide")
st.title("🎬 YouTube Explainer & Shorts Maker")
st.caption("Scripts + AI voiceover + visual ideas + AI-generated scene images")

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
        st.info("Your voice is ready. Use this file when you edit the final video.")

# Session state for script
if "script_output" not in st.session_state:
    st.session_state.script_output = ""

if st.button("✨ Generate Everything", type="primary"):
    if not openai_key or not topic:
        st.warning("OpenAI key and topic are required.")
        st.stop()

    client = OpenAI(api_key=openai_key)

    # Research with SerpAPI
    research = ""
    if serpapi_key:
        with st.spinner("Researching topic..."):
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
        "For each major scene, give clear visual suggestions (what to show on screen) "
        "and 1–2 simple image search keywords."
        if "Visual" in video_style else
        "Focus on strong, short on-screen text overlays and simple graphics for each part."
    )

    prompt = f"""
You are a YouTube scriptwriter for the channel "{brand_name}".
Topic: {topic}
Style: {video_style}
Target length: {duration} seconds (about {word_count} words)
Tone: {tone}
Structure: {structure}

Research (use if helpful, do not copy):
{research}

Write a natural, easy-to-speak script.
Also include:
- 5 catchy title options
- YouTube description + 8–12 hashtags
- Scene-by-scene breakdown

{visual_instruction}
"""

    with st.spinner("Writing script..."):
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.8
        )
        st.session_state.script_output = response.choices[0].message.content

# Display script if available
if st.session_state.script_output:
    st.success("Script ready!")
    st.markdown(st.session_state.script_output)

    plain_script = st.session_state.script_output.split("5 title")[0] if "5 title" in st.session_state.script_output else st.session_state.script_output

    # AI Voiceover
    if voice_option in ["AI Male", "AI Female"] and selected_voice and openai_key:
        if st.button("🔊 Generate AI Voiceover"):
            with st.spinner("Generating AI voiceover..."):
                try:
                    client = OpenAI(api_key=openai_key)
                    speech = client.audio.speech.create(
                        model="tts-1",
                        voice=selected_voice,
                        input=plain_script[:4000]
                    )
                    audio_bytes = speech.content
                    st.audio(audio_bytes, format="audio/mp3")
                    st.download_button("Download Voiceover (MP3)", audio_bytes,
                                       file_name="voiceover.mp3", mime="audio/mp3")
                except Exception as e:
                    st.error(f"Voiceover error: {e}")

    # Visual ideas via SerpAPI (optional)
    if "Visual" in video_style and serpapi_key:
        st.subheader("Suggested Image Ideas (via SerpAPI)")
        keywords = [topic, f"{topic} illustration", "success motivation", "technology workspace"]
        for kw in keywords[:3]:
            try:
                img_search = GoogleSearch({
                    "engine": "google_images",
                    "q": kw,
                    "api_key": serpapi_key,
                    "num": 4
                })
                img_results = img_search.get_dict()
                images = img_results.get("images_results", [])[:4]
                if images:
                    st.write(f"**Ideas for: {kw}**")
                    cols = st.columns(4)
                    for i, img in enumerate(images):
                        with cols[i]:
                            thumbnail = img.get("thumbnail")
                            if thumbnail:
                                st.image(thumbnail, use_container_width=True)
            except Exception:
                pass

    # ===== NEW: AI Image Generation Button =====
    st.subheader("AI-Generated Scene Images")
    if st.button("🎨 Generate AI Images for Main Scenes"):
        if not openai_key:
            st.warning("OpenAI key required.")
        else:
            client = OpenAI(api_key=openai_key)
            with st.spinner("Creating image prompts and generating images..."):
                # Ask OpenAI for 3 strong scene image prompts
                prompt_resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "user",
                        "content": f"""Based on this video script, create exactly 3 short, clear image prompts for the main scenes. 
Each prompt should be suitable for AI image generation (detailed but not too long).
Return them as a numbered list only.

Script:
{st.session_state.script_output[:3000]}"""
                    }],
                    temperature=0.7
                )
                prompts_text = prompt_resp.choices[0].message.content
                # Simple split into prompts
                scene_prompts = [line.strip() for line in prompts_text.split("\n") if line.strip() and any(c.isdigit() for c in line[:3])]

                if not scene_prompts:
                    scene_prompts = [topic] * 3  # fallback

                st.write("**Generated image prompts:**")
                for i, p in enumerate(scene_prompts[:3], 1):
                    st.write(f"{i}. {p}")

                # Generate images
                cols = st.columns(3)
                for idx, scene_prompt in enumerate(scene_prompts[:3]):
                    try:
                        img_response = client.images.generate(
                            model="gpt-image-2.5-flare",
                            prompt=f"YouTube explainer video scene, clean modern style, high quality: {scene_prompt}",
                            size="1024x1024",
                            n=1
                        )
                        b64_img = img_response.data[0].b64_json
                        img_bytes = base64.b64decode(b64_img)

                        with cols[idx]:
                            st.image(img_bytes, caption=f"Scene {idx+1}", use_container_width=True)
                            st.download_button(
                                f"Download Scene {idx+1}",
                                data=img_bytes,
                                file_name=f"scene_{idx+1}.png",
                                mime="image/png",
                                key=f"dl_{idx}"
                            )
                    except Exception as e:
                        with cols[idx]:
                            st.error(f"Scene {idx+1} failed: {str(e)[:100]}")

    st.download_button("Download Full Script", st.session_state.script_output, file_name="script.txt")

    st.info("""
**How to finish the video:**
1. Download the voiceover and AI images.
2. Open CapCut or Canva.
3. Drop in the images, add text overlays, transitions, and your logo.
4. Sync with the voiceover and export.
""")
