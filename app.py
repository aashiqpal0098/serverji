import streamlit as st
import requests
import speech_recognition as sr
import subprocess
import os
import io
import re
import tempfile

st.set_page_config(page_title="AASHIQ AI VIDEO", page_icon="🎬", layout="wide")
st.title("💖 AASHIQ AI VIDEO")
st.markdown("#### आपकी कहानी, आपकी आवाज़, और ऑटो कैप्शन के साथ")

VOICES = {"Male (Madhur)": "hi-IN-MadhurNeural", "Female (Swara)": "hi-IN-SwaraNeural"}

def generate_ai_image(prompt):
    if not prompt: return None
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=720&height=1280&seed=42"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            path = "temp_image.jpg"
            with open(path, "wb") as f: f.write(response.content)
            return path
    except: return None

def generate_ai_story(topic):
    return f"✨ {topic} की अद्भुत कहानी। एक दिन की शुरुआत हुई। फिर कुछ ऐसा हुआ कि सब हैरान रह गए। अंत में सबने खुशी मनाई।"

def speech_to_text_from_audio_bytes(audio_bytes):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
            audio = recognizer.record(source)
        return recognizer.recognize_google(audio, language="hi-IN")
    except: return "❌ समझ नहीं आया"

def generate_audio_sync(text, voice, output_path):
    subprocess.run(f"edge-tts --voice {VOICES[voice]} --text \"{text}\" --write-media {output_path}", shell=True, check=True)

def create_srt_from_story(story_text, audio_duration, srt_path):
    sentences = re.split(r'(?<=[।!?;]) +', story_text)
    if not sentences: sentences = [story_text]
    seg_dur = audio_duration / len(sentences)
    with open(srt_path, 'w', encoding='utf-8') as f:
        for i, line in enumerate(sentences):
            start = i * seg_dur
            end = (i + 1) * seg_dur
            f.write(f"{i+1}\n{int(start//3600):02d}:{int((start%3600)//60):02d}:{int(start%60):02d},{int((start%1)*1000):03d} --> {int(end//3600):02d}:{int((end%3600)//60):02d}:{int(end%60):02d},{int((end%1)*1000):03d}\n{line}\n\n")

def create_video_with_ffmpeg(image_path, audio_path, srt_path, output_path):
    subprocess.run(["ffmpeg","-y","-loop","1","-i",image_path,"-i",audio_path,"-vf",f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Alignment=10'","-c:v","libx264","-c:a","aac","-pix_fmt","yuv420p","-shortest",output_path], check=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("### ✍️ Step 1: Kahani Banao")
    topic_input = st.text_input("Topic Dijiye")
    if 'story' not in st.session_state: st.session_state.story = ""
    if st.button("🤖 AI se Kahani Likhwao"):
        with st.spinner("..."): st.session_state.story = generate_ai_story(topic_input)
    audio_value = st.audio_input("🎤 बोलकर कहानी जोड़ें")
    if audio_value:
        with st.spinner("..."):
            spoken = speech_to_text_from_audio_bytes(audio_value.getvalue())
            if "❌" not in spoken:
                st.session_state.story += "\n" + spoken
                st.success(f"✅ {spoken}")
    story_text = st.text_area("Aapki Kahani", value=st.session_state.story, height=150)
    voice_choice = st.selectbox("Voice:", list(VOICES.keys()))
with col2:
    st.markdown("### 🎨 Step 3: Character Banao")
    img_prompt = st.text_input("Photo description (English)")
    if 'image_path' not in st.session_state: st.session_state.image_path = None
    if st.button("🖼️ AI se Photo Banao"):
        with st.spinner("..."): st.session_state.image_path = generate_ai_image(img_prompt)
    if st.session_state.image_path: st.image(st.session_state.image_path, use_container_width=True)

if st.button("🚀 CREATE AASHIQ VIDEO", type="primary", use_container_width=True):
    if not story_text or not st.session_state.image_path:
        st.error("⚠️ Pehle kahani aur photo banao")
    else:
        with st.spinner("Video ban raha hai..."):
            try:
                audio_path = "voice.mp3"
                srt_path = "subtitles.srt"
                video_path = "final_output.mp4"
                generate_audio_sync(story_text, voice_choice, audio_path)
                dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",audio_path], capture_output=True, text=True).stdout.strip())
                create_srt_from_story(story_text, dur, srt_path)
                create_video_with_ffmpeg(st.session_state.image_path, audio_path, srt_path, video_path)
                with open(video_path, "rb") as f: st.download_button("⬇️ Download", data=f.read(), file_name="AASHIQ_Video.mp4", mime="video/mp4")
                st.video(video_path)
                for f in [audio_path, srt_path, video_path]:
                    if os.path.exists(f): os.remove(f)
            except Exception as e: st.error(f"Error: {e}")
