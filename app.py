import streamlit as st
import requests
import speech_recognition as sr
import subprocess
import os
import io
import re

st.set_page_config(page_title="AASHIQ AI VIDEO", layout="wide")
st.title("💖 AASHIQ AI VIDEO")

VOICES = {"Male (Madhur)": "hi-IN-MadhurNeural", "Female (Swara)": "hi-IN-SwaraNeural"}

def generate_ai_image(prompt):
    if not prompt:
        return None
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=720&height=1280&seed=42"
    try:
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            path = "temp_img.jpg"
            with open(path, "wb") as f:
                f.write(r.content)
            return path
    except:
        return None
    return None

def speech_to_text(audio_bytes):
    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(audio_bytes)) as src:
            audio = recognizer.record(src)
        return recognizer.recognize_google(audio, language="hi-IN")
    except:
        return None

def generate_audio(text, voice, out_path):
    cmd = f"edge-tts --voice {VOICES[voice]} --text \"{text}\" --write-media {out_path}"
    subprocess.run(cmd, shell=True, check=True)

def make_srt(story, duration, srt_path):
    sents = [s.strip() for s in re.split(r'(?<=[।!?;]) +', story) if s.strip()]
    if not sents:
        sents = [story]
    seg = duration / len(sents)
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(sents):
            start = i * seg
            end = (i+1) * seg
            f.write(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{line}\n\n")

def format_time(t):
    h = int(t//3600)
    m = int((t%3600)//60)
    s = int(t%60)
    ms = int((t%1)*1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def make_video(img_path, audio_path, srt_path, out_path):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", img_path,
        "-i", audio_path,
        "-vf", f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Alignment=10'",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out_path
    ]
    subprocess.run(cmd, check=True)

# UI
col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 कहानी")
    topic = st.text_input("Topic")
    if 'story' not in st.session_state:
        st.session_state.story = ""
    if st.button("🤖 AI Story"):
        st.session_state.story = f"✨ {topic} की कहानी। एक दिन की शुरुआत हुई। फिर कुछ हुआ। सब खुश हो गए।"
    audio_val = st.audio_input("🎤 बोलकर कहानी जोड़ें")
    if audio_val:
        txt = speech_to_text(audio_val.getvalue())
        if txt:
            st.session_state.story += "\n" + txt
            st.success(f"✅ {txt}")
    story_text = st.text_area("कहानी लिखें / एडिट करें", st.session_state.story, height=150)
    voice_choice = st.selectbox("आवाज़", list(VOICES.keys()))

with col2:
    st.subheader("🎨 फोटो")
    img_prompt = st.text_input("फोटो का विवरण (English)")
    if 'img_path' not in st.session_state:
        st.session_state.img_path = None
    if st.button("🖼️ AI फोटो बनाएँ"):
        st.session_state.img_path = generate_ai_image(img_prompt)
    if st.session_state.img_path:
        st.image(st.session_state.img_path, use_container_width=True)

if st.button("🚀 VIDEO बनाएँ", type="primary"):
    if not story_text or not st.session_state.img_path:
        st.error("पहले कहानी और फोटो बनाएँ")
    else:
        with st.spinner("वीडियो बन रहा है... 1-2 मिनट"):
            try:
                audio_file = "voice.mp3"
                srt_file = "caps.srt"
                out_file = "final.mp4"

                generate_audio(story_text, voice_choice, audio_file)
                dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",audio_file], capture_output=True, text=True).stdout.strip())
                make_srt(story_text, dur, srt_file)
                make_video(st.session_state.img_path, audio_file, srt_file, out_file)

                with open(out_file, "rb") as f:
                    st.video(f.read())
                    st.download_button("⬇️ डाउनलोड", data=f.read(), file_name="AASHIQ_Video.mp4")
                for f in [audio_file, srt_file, out_file]:
                    if os.path.exists(f): os.remove(f)
            except Exception as e:
                st.error(f"गलती: {e}")
def generate_audio(text, voice, out_path):
    cmd = f"edge-tts --voice {VOICES[voice]} --text \"{text}\" --write-media {out_path}"
    subprocess.run(cmd, shell=True, check=True)

def make_srt(story, duration, srt_path):
    sents = [s.strip() for s in re.split(r'(?<=[।!?;]) +', story) if s.strip()]
    if not sents:
        sents = [story]
    seg = duration / len(sents)
    with open(srt_path, "w", encoding="utf-8") as f:
        for i, line in enumerate(sents):
            start = i * seg
            end = (i+1) * seg
            f.write(f"{i+1}\n{format_time(start)} --> {format_time(end)}\n{line}\n\n")

def format_time(t):
    h = int(t//3600)
    m = int((t%3600)//60)
    s = int(t%60)
    ms = int((t%1)*1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def make_video(img_path, audio_path, srt_path, out_path):
    cmd = [
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", img_path,
        "-i", audio_path,
        "-vf", f"subtitles={srt_path}:force_style='FontSize=24,PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BackColour=&H80000000,Alignment=10'",
        "-c:v", "libx264",
        "-c:a", "aac",
        "-pix_fmt", "yuv420p",
        "-shortest",
        out_path
    ]
    subprocess.run(cmd, check=True)

# UI
col1, col2 = st.columns(2)
with col1:
    st.subheader("📝 कहानी")
    topic = st.text_input("Topic")
    if 'story' not in st.session_state:
        st.session_state.story = ""
    if st.button("🤖 AI Story"):
        st.session_state.story = f"✨ {topic} की कहानी। एक दिन की शुरुआत हुई। फिर कुछ हुआ। सब खुश हो गए।"
    audio_val = st.audio_input("🎤 बोलकर कहानी जोड़ें")
    if audio_val:
        txt = speech_to_text(audio_val.getvalue())
        if txt:
            st.session_state.story += "\n" + txt
            st.success(f"✅ {txt}")
    story_text = st.text_area("कहानी लिखें / एडिट करें", st.session_state.story, height=150)
    voice_choice = st.selectbox("आवाज़", list(VOICES.keys()))

with col2:
    st.subheader("🎨 फोटो")
    img_prompt = st.text_input("फोटो का विवरण (English)")
    if 'img_path' not in st.session_state:
        st.session_state.img_path = None
    if st.button("🖼️ AI फोटो बनाएँ"):
        st.session_state.img_path = generate_ai_image(img_prompt)
    if st.session_state.img_path:
        st.image(st.session_state.img_path, use_container_width=True)

if st.button("🚀 VIDEO बनाएँ", type="primary"):
    if not story_text or not st.session_state.img_path:
        st.error("पहले कहानी और फोटो बनाएँ")
    else:
        with st.spinner("वीडियो बन रहा है... 1-2 मिनट"):
            try:
                audio_file = "voice.mp3"
                srt_file = "caps.srt"
                out_file = "final.mp4"

                generate_audio(story_text, voice_choice, audio_file)
                dur = float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",audio_file], capture_output=True, text=True).stdout.strip())
                make_srt(story_text, dur, srt_file)
                make_video(st.session_state.img_path, audio_file, srt_file, out_file)

                with open(out_file, "rb") as f:
                    st.video(f.read())
                    st.download_button("⬇️ डाउनलोड", data=f.read(), file_name="AASHIQ_Video.mp4")
                for f in [audio_file, srt_file, out_file]:
                    if os.path.exists(f): os.remove(f)
            except Exception as e:
                st.error(f"गलती: {e}")
