import streamlit as st
import requests
import subprocess
import os
import re
import time
import io

st.set_page_config(page_title="AASHIQ AI VIDEO - Auto", layout="wide")
st.title("💖 AASHIQ AI VIDEO - Fully Automated")
st.markdown("---")

### ✍️ Step 1: Write Your Story
Your story will be used to automatically generate a matching image and a natural voiceover.
")

# --- Story Input Section ---
if 'story' not in st.session_state:
    st.session_state.story = ""

story_text = st.text_area(
    "✍️ **Write or paste your Hindi story here:**",
    value=st.session_state.story,
    height=200
)

# --- Voice Selection ---
st.markdown("### 🎙️ Step 2: Choose Your Voice")
col1, col2 = st.columns(2)
with col1:
    voice_choice = st.radio(
        "Select Speaker:",
        ["Female (Natural)", "Male (Natural)"],
        horizontal=True,
        index=0
    )
with col2:
    st.caption("Powered by Pollinations.ai for natural-sounding Hindi speech")

# --- Main Generate Button ---
if st.button("🚀 **Generate Full AI Video**", type="primary", use_container_width=True):
    if not story_text.strip():
        st.error("❌ Please write a story first.")
    else:
        # Step 1: Automatically generate an AI image prompt from the story
        with st.status("🤖 **Step 1/3: Analyzing Story & Generating Image...**", expanded=True) as status:
            st.write("Extracting key theme from your story...")
            # For this example, we're using the first 200 characters as a prompt.
            # For better results, you could integrate a free LLM to summarize.
            image_prompt = story_text[:200].strip() + ", beautiful scene, cinematic lighting, high quality"
            st.write(f"**Generated Prompt:** {image_prompt}")

            st.write("Generating image with Pollinations.ai...")
            img_url = f"https://image.pollinations.ai/prompt/{image_prompt.replace(' ', '%20')}?width=720&height=1280&nologo=true"
            
            try:
                img_response = requests.get(img_url, timeout=20)
                if img_response.status_code == 200:
                    img_path = "temp_scene.jpg"
                    with open(img_path, "wb") as f:
                        f.write(img_response.content)
                    st.session_state['auto_img_path'] = img_path
                    st.image(img_path, caption="Automatically Generated Scene", use_container_width=True)
                    status.update(label="✅ Image Generated!", state="complete")
                else:
                    st.error("Image generation failed. Please try again.")
                    st.stop()
            except Exception as e:
                st.error(f"Network error during image generation: {e}")
                st.stop()
            time.sleep(1)

        # Step 2: Generate natural-sounding Hindi audio (Online)
        with st.status("🎤 **Step 2/3: Creating Natural Voiceover...**", expanded=True) as status:
            st.write(f"Generating {voice_choice} voice with Pollinations TTS...")
            # Determine voice selection for Pollinations API
            voice_param = "female" if "Female" in voice_choice else "male"
            tts_url = f"https://text.pollinations.ai/{story_text}?voice={voice_param}&language=hi"
            try:
                audio_response = requests.get(tts_url, timeout=30)
                if audio_response.status_code == 200:
                    with open("voiceover.mp3", "wb") as f:
                        f.write(audio_response.content)
                    st.audio("voiceover.mp3", format="audio/mp3")
                    status.update(label="✅ Voiceover Ready!", state="complete")
                else:
                    st.error(f"TTS API error: {audio_response.status_code}")
                    st.stop()
            except Exception as e:
                st.error(f"Network error during TTS generation: {e}")
                st.stop()
            time.sleep(1)

        # Step 3: Combine everything into a video
        with st.status("🎬 **Step 3/3: Assembling Final Video...**", expanded=True) as status:
            st.write("Calculating audio duration...")
            # Get audio duration using ffprobe
            dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "voiceover.mp3"]
            result = subprocess.run(dur_cmd, capture_output=True, text=True)
            duration = float(result.stdout.strip())

            st.write("Creating subtitles...")
            # Create SRT subtitles from story
            sentences = re.split(r'(?<=[।!?;]) +', story_text)
            if not sentences:
                sentences = [story_text]
            seg_duration = duration / len(sentences)
            
            def format_srt_time(seconds):
                h = int(seconds // 3600)
                m = int((seconds % 3600) // 60)
                s = int(seconds % 60)
                ms = int((seconds % 1) * 1000)
                return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
            
            with open("subtitles.srt", "w", encoding="utf-8") as srt:
                for i, line in enumerate(sentences):
                    start = i * seg_duration
                    end = (i+1) * seg_duration
                    srt.write(f"{i+1}\n")
                    srt.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
                    srt.write(f"{line.strip()}\n\n")

            st.write("Rendering video with ffmpeg...")
            # Create video with ffmpeg
            cmd = [
                "ffmpeg", "-y",
                "-loop", "1",
                "-i", st.session_state['auto_img_path'],
                "-i", "voiceover.mp3",
                "-vf", f"subtitles=subtitles.srt:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Alignment=10'",
                "-c:v", "libx264",
                "-c:a", "aac",
                "-pix_fmt", "yuv420p",
                "-shortest",
                "final_video.mp4"
            ]
            subprocess.run(cmd, check=True)
            status.update(label="✅ Video Ready!", state="complete")

        st.balloons()
        st.success("🎉 **Your AI video is ready!**")
        with open("final_video.mp4", "rb") as f:
            video_bytes = f.read()
        st.video(video_bytes)
        st.download_button(
            "💾 **Download Your AASHIQ Video**",
            data=video_bytes,
            file_name="AASHIQ_AI_Video.mp4",
            mime="video/mp4",
            use_container_width=True
)# ------------------- Story Input -------------------
st.subheader("📝 अपनी कहानी लिखें (या ऊपर बोलें)")
if 'story' not in st.session_state:
    st.session_state.story = ""

# Text area for story
story_text = st.text_area("कहानी", value=st.session_state.story, height=200, key="story_area")

# Optional: AI story generation (mock, no API key needed)
topic = st.text_input("कोई टॉपिक दें (वैकल्पिक) – AI से कहानी बनाने के लिए")
if st.button("🤖 AI से कहानी बनाएँ (मुफ्त, बिना key)"):
    if topic:
        # Use a free public story generation API (example: huggingface inference without token? Not reliable)
        # Simpler: generate a template story based on topic
        story = f"✨ {topic} की अद्भुत कहानी।\nएक समय की बात है। {topic} ने अपने सपनों को पूरा करने की ठान ली। मुश्किलें आईं, लेकिन हार नहीं मानी। अंत में सबको खुशी मिली। यह कहानी हमें सिखाती है कि प्यार और मेहनत से सब मुमकिन है।"
        st.session_state.story = story
        st.session_state.story_area = story
        st.experimental_rerun()
    else:
        st.warning("पहले टॉपिक लिखें")

# ------------------- Image Generation -------------------
st.subheader("🎨 AI से फोटो बनाएँ")
img_prompt = st.text_input("फोटो का अंग्रेजी विवरण (जैसे: 'Indian couple in love')")
if st.button("🖼️ फोटो जनरेट करें"):
    if img_prompt:
        with st.spinner("फोटो बन रही है..."):
            # Pollinations.ai - working URL
            url = f"https://image.pollinations.ai/prompt/{img_prompt.replace(' ', '%20')}?width=720&height=1280&nologo=true"
            try:
                response = requests.get(url, timeout=15)
                if response.status_code == 200:
                    img_path = "temp_img.jpg"
                    with open(img_path, "wb") as f:
                        f.write(response.content)
                    st.session_state.img_path = img_path
                    st.success("फोटो तैयार!")
                else:
                    st.error("फोटो नहीं बन पाई, कृपया दोबारा प्रयास करें।")
            except Exception as e:
                st.error(f"नेटवर्क त्रुटि: {e}")
    else:
        st.warning("कृपया फोटो का विवरण लिखें")

if 'img_path' in st.session_state and st.session_state.img_path:
    st.image(st.session_state.img_path, use_container_width=True)

# ------------------- Voice Selection for TTS -------------------
voice_choice = st.selectbox("आवाज़ चुनें", ["Male (Hindi)", "Female (Hindi)"])

# ------------------- Final Video Generation -------------------
if st.button("🚀 VIDEO बनाएँ", type="primary"):
    if not story_text:
        st.error("❌ पहले कहानी लिखें या बोलें")
    elif 'img_path' not in st.session_state:
        st.error("❌ पहले फोटो जनरेट करें")
    else:
        with st.spinner("🎥 वीडियो बन रहा है... 1-2 मिनट लगेंगे"):
            try:
                # 1. Generate Audio using free TTS API (ttsmp3.com - no key)
                # Map voice choice to language code
                lang_code = "hi"  # Hindi
                # For ttsmp3, we need to send POST request
                tts_url = "https://api.ttsmp3.com/mp3"
                payload = {
                    "text": story_text,
                    "lang": "hi",
                    "voice": "male" if "Male" in voice_choice else "female"
                }
                headers = {"Content-Type": "application/json"}
                response = requests.post(tts_url, json=payload, headers=headers, timeout=30)
                if response.status_code == 200:
                    with open("audio.mp3", "wb") as f:
                        f.write(response.content)
                else:
                    # Fallback: use a different free TTS (voice RSS) or edge-tts via subprocess if installed
                    # Since edge-tts may not be installed, we use another free API
                    # Alternative: use translate.google.com TTS (unofficial)
                    st.warning("TTS API failed, trying alternative...")
                    # Use google translate TTS (no key required)
                    import urllib.parse
                    text_encoded = urllib.parse.quote(story_text)
                    tts_alt = f"https://translate.google.com/translate_tts?ie=UTF-8&q={text_encoded}&tl=hi&client=tw-ob"
                    alt_resp = requests.get(tts_alt, headers={"User-Agent": "Mozilla/5.0"})
                    if alt_resp.status_code == 200:
                        with open("audio.mp3", "wb") as f:
                            f.write(alt_resp.content)
                    else:
                        st.error("ऑडियो जनरेट नहीं हुआ। कृपया बाद में प्रयास करें।")
                        st.stop()
                
                # 2. Get audio duration using ffprobe
                dur_cmd = ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", "audio.mp3"]
                result = subprocess.run(dur_cmd, capture_output=True, text=True)
                duration = float(result.stdout.strip())
                
                # 3. Create SRT subtitles from story
                sentences = re.split(r'(?<=[।!?;]) +', story_text)
                if not sentences:
                    sentences = [story_text]
                seg_duration = duration / len(sentences)
                
                def format_srt_time(seconds):
                    h = int(seconds // 3600)
                    m = int((seconds % 3600) // 60)
                    s = int(seconds % 60)
                    ms = int((seconds % 1) * 1000)
                    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
                
                with open("subtitles.srt", "w", encoding="utf-8") as srt:
                    for i, line in enumerate(sentences):
                        start = i * seg_duration
                        end = (i+1) * seg_duration
                        srt.write(f"{i+1}\n")
                        srt.write(f"{format_srt_time(start)} --> {format_srt_time(end)}\n")
                        srt.write(f"{line.strip()}\n\n")
                
                # 4. Create video with ffmpeg
                cmd = [
                    "ffmpeg", "-y",
                    "-loop", "1",
                    "-i", st.session_state.img_path,
                    "-i", "audio.mp3",
                    "-vf", f"subtitles=subtitles.srt:force_style='FontName=Arial,FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Alignment=10'",
                    "-c:v", "libx264",
                    "-c:a", "aac",
                    "-pix_fmt", "yuv420p",
                    "-shortest",
                    "final_video.mp4"
                ]
                subprocess.run(cmd, check=True)
                
                # 5. Display and download
                with open("final_video.mp4", "rb") as f:
                    video_bytes = f.read()
                st.video(video_bytes)
                st.download_button("⬇️ वीडियो डाउनलोड करें", data=video_bytes, file_name="AASHIQ_AI_Video.mp4", mime="video/mp4")
                
                # Cleanup
                for f in ["audio.mp3", "subtitles.srt", "final_video.mp4"]:
                    if os.path.exists(f):
                        os.remove(f)
                
            except Exception as e:
                st.error(f"वीडियो बनाते समय त्रुटि: {e}")<button onclick="startRecording()" style="background-color:#ff4b4b; color:white; padding:10px; border:none; border-radius:5px;">🎙️ Start Speaking</button>
"""

st.components.v1.html(voice_js, height=80)

# Story input
st.subheader("📝 कहानी लिखें या ऊपर से बोलें")
story_text = st.text_area("कहानी", height=200, key="story")

# Topic and photo prompt
topic = st.text_input("Topic (AI story generation ke liye)")
if st.button("🤖 AI से कहानी बनाएँ"):
    response = requests.post(
        "https://api.openai.com/v1/completions",  # नहीं, बिना API key के काम नहीं करेगा
        headers={"Authorization": f"Bearer {st.secrets.get('OPENAI_API_KEY', '')}"},
        json={"model": "gpt-3.5-turbo-instruct", "prompt": f"Hindi mein {topic} ki kahani: ", "max_tokens": 150}
    )
    if response.status_code == 200:
        story_text = response.json()["choices"][0]["text"]
        st.session_state.story = story_text
        st.experimental_rerun()
    else:
        st.error("API key nahi hai, khud likho")

# Image generation
img_prompt = st.text_input("Photo description (English)")
if st.button("🖼️ AI Photo Generate"):
    url = f"https://image.pollinations.ai/prompt/{img_prompt.replace(' ', '%20')}?width=720&height=1280"
    response = requests.get(url)
    if response.status_code == 200:
        with open("temp_img.jpg", "wb") as f:
            f.write(response.content)
        st.session_state.img_path = "temp_img.jpg"
        st.image(st.session_state.img_path)

voice_choice = st.selectbox("Voice (TTS ke liye)", ["Male (Hindi)", "Female (Hindi)"])

if st.button("🚀 VIDEO BANAYEIN", type="primary"):
    if not story_text or 'img_path' not in st.session_state:
        st.error("Pehle kahani aur photo generate karein")
    else:
        with st.spinner("Video ban raha hai..."):
            try:
                # TTS using browser's speech synthesis? No, need server-side.
                # Use a free TTS API: ttsmp3.com (no key)
                tts_url = f"https://api.ttsmp3.com/mp3?text={story_text}&lang=hi&voice={voice_choice}"
                audio_resp = requests.get(tts_url)
                with open("voice.mp3", "wb") as f:
                    f.write(audio_resp.content)
                
                # Audio duration using ffprobe
                dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1","voice.mp3"], capture_output=True, text=True).stdout.strip())
                
                # SRT
                sents = re.split(r'(?<=[।!?;]) +', story_text)
                seg = dur / len(sents)
                with open("subs.srt", "w", encoding="utf-8") as f:
                    for i, line in enumerate(sents):
                        start = i * seg
                        end = (i+1) * seg
                        f.write(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{line}\n\n")
                
                # FFmpeg
                subprocess.run([
                    "ffmpeg","-y","-loop","1","-i",st.session_state.img_path,
                    "-i","voice.mp3","-vf",f"subtitles=subs.srt:force_style='FontSize=24,PrimaryColour=&H00FFFFFF'",
                    "-c:v","libx264","-c:a","aac","-shortest","final.mp4"
                ], check=True)
                
                with open("final.mp4", "rb") as f:
                    st.video(f.read())
                    st.download_button("Download", data=f.read(), file_name="AASHIQ.mp4")
            except Exception as e:
                st.error(f"Error: {e}")

def format_time(t):
    h = int(t//3600); m = int((t%3600)//60); s = int(t%60); ms = int((t%1)*1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"
