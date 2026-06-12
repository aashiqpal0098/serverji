import streamlit as st
import asyncio
import edge_tts
import requests
import speech_recognition as sr
from moviepy.editor import AudioFileClip, ImageClip, TextClip, CompositeVideoClip
from moviepy.video.fx import resize
import io
import re

# ------------------- Config -------------------
st.set_page_config(page_title="AASHIQ AI VIDEO", page_icon="🎬", layout="wide")
st.title("💖 AASHIQ AI VIDEO")
st.markdown("#### आपकी कहानी, आपकी आवाज़, और ऑटो कैप्शन के साथ सुपरहिट वीडियो")

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
    # डेमो स्टोरी – आप चाहें तो किसी API से भी ला सकते हैं
    return f"✨ {topic} की अद्भुत कहानी। एक दिन की शुरुआत हुई। फिर कुछ ऐसा हुआ कि सब हैरान रह गए। अंत में सबने खुशी मनाई।"

async def generate_audio(text, voice, output_path):
    communicate = edge_tts.Communicate(text, VOICES[voice])
    await communicate.save(output_path)

def split_into_sentences(text):
    """हिंदी/अंग्रेजी वाक्यों में तोड़ना"""
    sentences = re.split(r'(?<=[।!?;]) +', text)
    return [s.strip() for s in sentences if s.strip()]

def add_captions_to_video(image_path, audio_path, story_text, output_path):
    """
    image_path: static image
    audio_path: generated speech mp3
    story_text: full story
    output_path: final video with captions
    """
    # Audio Clip
    audio_clip = AudioFileClip(audio_path)
    duration = audio_clip.duration

    # Background Image Clip
    img_clip = ImageClip(image_path).set_duration(duration).resize(height=720)
    
    # Sentences with rough timing (equal distribution)
    sentences = split_into_sentences(story_text)
    if not sentences:
        sentences = [story_text]
    
    segment_duration = duration / len(sentences)
    
    # Create text clips for each sentence
    text_clips = []
    for i, line in enumerate(sentences):
        start_time = i * segment_duration
        end_time = (i + 1) * segment_duration
        
        txt_clip = (TextClip(line, fontsize=40, font='Arial', color='white', stroke_color='black', stroke_width=2)
                    .set_position(('center', 'center'))
                    .set_start(start_time)
                    .set_duration(segment_duration))
        text_clips.append(txt_clip)
    
    # Composite all
    video = CompositeVideoClip([img_clip, *text_clips]).set_audio(audio_clip)
    video.write_videofile(output_path, fps=24, codec="libx264", audio_codec="aac")
    
    video.close()
    audio_clip.close()

# ------------------- Voice to Text -------------------
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
    
    # Voice input for story
    st.markdown("#### 🎤 बोलकर कहानी जोड़ें")
    audio_value = st.audio_input("रिकॉर्ड करें और अपनी कहानी बोलें")
    if audio_value:
        with st.spinner("आपकी आवाज़ को टेक्स्ट में बदल रहा हूँ..."):
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

# ------------------- Final Video with Auto Captions -------------------
if st.button("🚀 CREATE AASHIQ VIDEO (with auto captions)", type="primary", use_container_width=True):
    if not story_text or not st.session_state.image_path:
        st.error("⚠️ Kripya pehle kahani aur photo generate karein!")
    else:
        with st.spinner("🎥 Video ban raha hai... Kripya 1-2 minute intezaar karein..."):
            try:
                audio_path = "voice.mp3"
                video_path = "final_output_with_captions.mp4"
                
                # Generate Audio from story
                asyncio.run(generate_audio(story_text, voice_choice, audio_path))
                
                # Create video with auto captions
                add_captions_to_video(st.session_state.image_path, audio_path, story_text, video_path)
                
                st.success("✅ Superhit Video Taiyar Hai! ✨")
                
                with open(video_path, "rb") as file:
                    video_bytes = file.read()
                st.video(video_bytes)
                st.download_button("⬇️ Download AASHIQ Video", data=video_bytes, file_name="AASHIQ_AI_Video.mp4", mime="video/mp4")
                
                # Cleanup temporary files (optional)
                os.remove(audio_path)
                os.remove(video_path)
                
            except Exception as e:
                st.error(f"Kuch galat ho gaya: {e}")
