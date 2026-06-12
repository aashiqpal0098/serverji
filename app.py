import streamlit as st
import requests
import speech_recognition as sr
import subprocess
import os
import io
import re
import tempfile
import json

# ------------------- Page Config -------------------
st.set_page_config(page_title="AASHIQ AI VIDEO", page_icon="🎬", layout="wide")
st.title("💖 AASHIQ AI VIDEO")
st.markdown("#### आपकी कहानी, आपकी आवाज़, और ऑटो कैप्शन के साथ")

VOICES = {"Male (Madhur)": "hi-IN-MadhurNeural", "Female (Swara)": "hi-IN-SwaraNeural"}

# ------------------- Helper Functions -------------------
def generate_ai_image(prompt):
    if not prompt:
        return None
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=720&height=1280&seed=42"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            path = "temp_image.jpg"
            with open(path, "wb") as f:
                f.write(response.content)
            return path
    except:
        return None
    return None

def generate_ai_story(topic):
    return f"✨ {topic} की अद्भुत कहानी। एक दिन की शुरुआत हुई। फिर कुछ ऐसा हुआ कि सब हैरान रह गए। अंत में सबने खुशी मनाई।"

# ---------- Voice to Text ----------
def speech_to_text_from_audio_bytes(audio_bytes):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio, language="hi-IN")
        return text
    except sr.UnknownValueError:
        return "❌ आवाज़ समझ नहीं आई।"
    except sr.RequestError:
        return "❌ Google API से कनेक्ट नहीं हो पाए।"
    except Exception as e:
        return f"❌ गलती: {e}"

# ---------- Audio Generation ----------
def generate_audio_sync(text, voice, output_path):
    cmd = f"edge-tts --voice {VOICES[voice]} --text \"{text}\" --write-media {output_path}"
    subprocess.run(cmd, shell=True, check=True)

# ---------- Create SRT subtitles from story ----------
def create_srt_from_story(story_text, audio_duration, srt_path):
    sentences = re.split(r'(?<=[।!?;]) +', story_text)
    if not sentences:
        sentences = [story_text]
    seg_dur = audio_duration / len(sentences)
    
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, line in enumerate(sentences):
            start = i * seg_dur
            end = (i + 1) * seg_dur
            # SRT time format: HH:MM:SS,mmm
            start_str = f"{int(start//3600):02d}:{int((start%3600)//60):02d}:{int(start%60):02d},{int((start%1)*1000):03d}"
            end_str = f"{int(end//3600):02d}:{int((end%3600)//60):02d}:{int(end%60):02d},{int((end%1)*1000):03d}"
            f.write(f"{i+1}\n{start_str} --> {end_str}\n{line}\n\n")

# ---------- Create video using ffmpeg (image + audio + subtitles) ----------
def create_video_with_ffmpeg(image_path, audio_path, srt_path, output_path):
    # ffmpeg command: loop image, add audio, burn subtitles
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", image_path,
        "-i", audio_path,
        "-vf", f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Alignment=10'",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        output_path
    ]
    subprocess.run(cmd, check=True)

# ------------------- UI Layout -------------------
col1, col2 = st.columns(2)

with col1:
    st.markdown("### ✍️ Step 1: Kahani Banao")
    topic_input = st.text_input("Topic Dijiye (Jaise: Pyar aur dosti)")

    if 'story' not in st.session_state:
        st.session_state.story = ""

    if st.button("🤖 AI se Kahani Likhwao"):
        with st.spinner("Kahani likhi jaa rahi hai..."):
            st.session_state.story = generate_ai_story(topic_input)

    st.markdown("#### 🎤 बोलकर कहानी जोड़ें")
    audio_value = st.audio_input("रिकॉर्ड करें और अपनी कहानी बोलें")
    if audio_value:
        with st.spinner("आवाज़ को टेक्स्ट में बदल रहा हूँ..."):
            spoken_text = speech_to_text_from_audio_bytes(audio_value.getvalue())
            if "❌" not in spoken_text:
                st.session_state.story = st.session_state.story + "\n" + spoken_text
                st.success(f"✅ जोड़ा गया: {spoken_text}")
            else:
                st.error(spoken_text)

    story_text = st.text_area("Aapki Kahani (Edit kar sakte hain):", value=st.session_state.story, height=150)

    st.markdown("### 🎙️ Step 2: Aawaz Chunein")
    voice_choice = st.selectbox("Voice:", list(VOICES.keys()))

with col2:
    st.markdown("### 🎨 Step 3: Character Banao")
    img_prompt = st.text_input("Kaisi photo chahiye? (English mein)", placeholder="A realistic Indian couple...")

    if 'image_path' not in st.session_state:
        st.session_state.image_path = None

    if st.button("🖼️ AI se Photo Banao"):
        with st.spinner("Photo generate ho rahi hai..."):
            st.session_state.image_path = generate_ai_image(img_prompt)

    if st.session_state.image_path:
        st.image(st.session_state.image_path, caption="Generated Character", use_container_width=True)

st.markdown("---")

# ------------------- Final Video -------------------
if st.button("🚀 CREATE AASHIQ VIDEO (with auto captions)", type="primary", use_container_width=True):
    if not story_text or not st.session_state.image_path:
        st.error("⚠️ Kripya pehle kahani aur photo generate karein!")
    else:
        with st.spinner("🎥 Video ban raha hai... 1-2 minute lagega..."):
            try:
                audio_path = "voice.mp3"
                srt_path = "subtitles.srt"
                video_path = "final_output.mp4"

                # Generate audio
                generate_audio_sync(story_text, voice_choice, audio_path)

                # Get audio duration using ffprobe
                result = subprocess.run(
                    ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", audio_path],
                    capture_output=True, text=True
                )
                audio_duration = float(result.stdout.strip())

                # Create SRT subtitles
                create_srt_from_story(story_text, audio_duration, srt_path)

                # Create video with subtitles
                create_video_with_ffmpeg(st.session_state.image_path, audio_path, srt_path, video_path)

                st.success("✅ Video Taiyar Hai!")

                with open(video_path, "rb") as file:
                    video_bytes = file.read()
                st.video(video_bytes)
                st.download_button("⬇️ Download AASHIQ Video", data=video_bytes, file_name="AASHIQ_Video.mp4", mime="video/mp4")

                # Cleanup
                for f in [audio_path, srt_path, video_path]:
                    if os.path.exists(f):
                        os.remove(f)

            except subprocess.CalledProcessError as e:
                st.error(f"ffmpeg error: {e.stderr if e.stderr else e}")
            except Exception as e:
                st.error(f"Error: {e}")
