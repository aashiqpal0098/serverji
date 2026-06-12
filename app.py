import streamlit as st
import subprocess
import os
import re
import requests
import json
import base64

st.set_page_config(page_title="AASHIQ AI VIDEO", layout="wide")
st.title("💖 AASHIQ AI VIDEO")

st.markdown("""
### 🎤 वॉइस इनपुट के लिए:
1. नीचे दिए बटन **"Start Speaking"** पर क्लिक करें  
2. माइक्रोफोन अनुमति दें  
3. बोलें – टेक्स्ट अपने आप भर जाएगा  
""")

# JavaScript for voice recognition
voice_js = """
<script>
const recognition = new (window.SpeechRecognition || window.webkitSpeechRecognition)();
recognition.lang = 'hi-IN';
recognition.interimResults = false;
recognition.onresult = (event) => {
    const text = event.results[0][0].transcript;
    const textarea = parent.document.querySelector('textarea[data-testid="stMarkdown"] textarea');
    if (textarea) {
        textarea.value += text + " ";
        textarea.dispatchEvent(new Event('input', {bubbles: true}));
    }
};
function startRecording() {
    recognition.start();
}
</script>
<button onclick="startRecording()" style="background-color:#ff4b4b; color:white; padding:10px; border:none; border-radius:5px;">🎙️ Start Speaking</button>
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
