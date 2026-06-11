import streamlit as st
import asyncio
import edge_tts
import requests
import os
from moviepy.editor import AudioFileClip, ImageClip

# 🎙️ Voice Setup
VOICES = {
    "Male (Madhur)": "hi-IN-MadhurNeural",
    "Female (Swara)": "hi-IN-SwaraNeural"
}

# Functions
def generate_ai_story(topic):
    if not topic:
        return "Pehle koi topic likhein!"
    try:
        url = f"https://text.pollinations.ai/prompt/Write%20a%20short%20Hindi%20story%20in%20Roman%20English%20(Hinglish)%20about%20{topic}.%20Make%20it%20interesting%20and%205-6%20lines%20long."
        response = requests.get(url)
        return response.text
    except:
        return "Story generate karne mein error aaya."

def generate_ai_image(prompt):
    if not prompt:
        return None
    try:
        url = f"https://image.pollinations.ai/prompt/{prompt}?width=720&height=1280"
        response = requests.get(url)
        img_path = "ai_generated_face.jpg"
        with open(img_path, "wb") as f:
            f.write(response.content)
        return img_path
    except:
        return None

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
