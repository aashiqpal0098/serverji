import streamlit as st
import asyncio
import edge_tts
import requests
import os
from PIL import Image
from moviepy.editor import AudioFileClip, ImageClip

# Voice setup
VOICES = {"Male (Madhur)": "hi-IN-MadhurNeural", "Female (Swara)": "hi-IN-SwaraNeural"}

def generate_ai_image(prompt):
    if not prompt: return None
    # Pollinations image API
    url = f"https://image.pollinations.ai/prompt/{prompt.replace(' ', '%20')}?width=720&height=1280&seed=42"
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            with open("temp_image.jpg", "wb") as f:
                f.write(response.content)
            return "temp_image.jpg"
    except:
        return None
    return None

st.set_page_config(page_title="AI Studio", layout="centered")
st.title("🌟 AI Video Studio")

# UI Components
topic = st.text_input("Topic likhein")
story = st.text_area("Kahani", height=150)
img_prompt = st.text_input("Photo ka description (English)")

if st.button("Generate"):
    with st.spinner("Processing..."):
        img_path = generate_ai_image(img_prompt)
        
        if img_path:
            st.image(img_path)
            # Audio aur Video processing yahan karein
            st.success("Image mil gayi! Ab audio generate kar rahe hain...")
        else:
            st.error("Image generate nahi ho saki, please fir se try karein.")

async def generate_audio(text, voice, output_path):
    communicate = edge_tts.Communicate(text, VOICES[voice])
    await communicate.save(output_path)

# UI Setup
st.set_page_config(page_title="Advanced AI Studio", page_icon="🌟", layout="wide")
st.title("🌟 Advanced AI Video Studio (Streamlit Version)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### ✍️ Step 1: Kahani Banao")
    topic_input = st.text_input("Topic Dijiye (Jaise: Bhoot aur kisan)")
    
    if 'story' not in st.session_state:
        st.session_state.story = ""
        
    if st.button("🤖 AI se Kahani Likhwao"):
        with st.spinner("Kahani likhi jaa rahi hai..."):
            st.session_state.story = generate_ai_story(topic_input)
            
    story_text = st.text_area("Aapki Kahani (Edit kar sakte hain):", value=st.session_state.story, height=150)
    
    st.markdown("### 🎙️ Step 2: Aawaz Chunein")
    voice_choice = st.selectbox("Voice:", list(VOICES.keys()))

with col2:
    st.markdown("### 🎨 Step 3: Character Banao")
    img_prompt = st.text_input("Kaisi photo chahiye? (English mein)", placeholder="A realistic Indian farmer...")
    
    if 'image_path' not in st.session_state:
        st.session_state.image_path = None
        
    if st.button("🖼️ AI se Photo Banao"):
        with st.spinner("Photo generate ho rahi hai..."):
            st.session_state.image_path = generate_ai_image(img_prompt)
            
    if st.session_state.image_path:
        st.image(st.session_state.image_path, caption="Generated Character", use_column_width=True)

st.markdown("---")

# Video Generation
if st.button("🚀 CREATE FINAL AI VIDEO", type="primary", use_container_width=True):
    if not story_text or not st.session_state.image_path:
        st.error("⚠️ Kripya pehle kahani aur photo generate karein!")
    else:
        with st.spinner("🎥 Video ban raha hai... Kripya 1-2 minute intezaar karein..."):
            try:
                audio_path = "voice.mp3"
                video_path = "final_output.mp4"
                
                # Generate Audio
                asyncio.run(generate_audio(story_text, voice_choice, audio_path))
                
                # Combine Image and Audio
                audio_clip = AudioFileClip(audio_path)
                img_clip = ImageClip(st.session_state.image_path).set_duration(audio_clip.duration)
                
                video = img_clip.set_audio(audio_clip)
                video.write_videofile(video_path, fps=24, codec="libx264", audio_codec="aac")
                
                st.success("✅ Video Taiyar Hai!")
                
                # Show Video and Download Button
                with open(video_path, "rb") as file:
                    video_bytes = file.read()
                    
                st.video(video_bytes)
                st.download_button("⬇️ Download Video", data=video_bytes, file_name="AI_Story_Video.mp4", mime="video/mp4")
                
                # Cleanup
                audio_clip.close()
                video.close()
                
            except Exception as e:
                st.error(f"Kuch galat ho gaya: {e}")
