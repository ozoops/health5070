import streamlit as st
import requests
import openai
import os
from PIL import Image, ImageDraw, ImageFont
import io
import textwrap
import pandas as pd
import sys
from datetime import datetime
import moviepy.editor as mp
from gtts import gTTS
import time

# Add the directory of the current file to the system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database import init_db

# Define the directory to save generated video files
VIDEO_DIR = "generated_videos"
if not os.path.exists(VIDEO_DIR):
    os.makedirs(VIDEO_DIR)

class VideoProducer:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = openai.OpenAI(api_key=self.api_key)

    def produce_video_content(self, article, script):
        article_id = article['id']
        title = article['title']
        crawled_date = article['crawled_date']

        thumbnail_path = self.generate_thumbnail(article_id, title)
        script_image_path = self.generate_script_image(article_id, script)

        video_path = self.create_video_file(article_id, title, script, thumbnail_path, script_image_path)

        video_data = {
            'article_id': article_id,
            'video_title': title,
            'script': script,
            'thumbnail': thumbnail_path,
            'script_image': script_image_path,
            'video_path': video_path,
            'production_status': 'completed',
            'created_date': crawled_date
        }
        return video_data

    def save_video_data(self, video_data, conn):
        c = conn.cursor()
        c.execute("""
            INSERT INTO videos (article_id, video_title, script, thumbnail, script_image, video_path, production_status, created_date)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            video_data['article_id'],
            video_data['video_title'],
            video_data['script'],
            video_data['thumbnail'],
            video_data['script_image'],
            video_data['video_path'],
            video_data['production_status'],
            video_data['created_date']
        ))
        conn.commit()
        return c.lastrowid

    def get_font_path(self, bold=False):
        if bold:
            font_path = "C:/Windows/Fonts/malgunbd.ttf"
            if not os.path.exists(font_path):
                font_path = "C:/Windows/Fonts/nanumgothicbold.ttf"
        else:
            font_path = "C:/Windows/Fonts/malgun.ttf"
            if not os.path.exists(font_path):
                font_path = "C:/Windows/Fonts/nanumgothic.ttf"
        
        if not os.path.exists(font_path):
            st.warning("Could not find required fonts.")
            return None
        return font_path

    def generate_thumbnail(self, article_id, title):
        print("--- [THUMBNAIL GENERATION] START ---")
        for i in range(3): # Retry up to 3 times
            try:
                prompt = f"""
                A clean and modern illustration for a health article for seniors.
                The article title is: "{title}"
                The image should be visually appealing, with a soft and friendly color palette.
                Do not include any text in the image.
                Style: Flat design, simple, and clear.
                """
                
                response = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1024x1024",
                    quality="standard",
                    n=1,
                )

                image_url = response.data[0].url
                
                image_response = requests.get(image_url)
                image_response.raise_for_status()
                
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                thumbnail_filename = f"thumbnail_{{article_id}}_{timestamp}.png"
                thumbnail_path = os.path.join(VIDEO_DIR, thumbnail_filename)
                
                with open(thumbnail_path, "wb") as f:
                    f.write(image_response.content)
                
                print(f"Thumbnail saved to: {thumbnail_path}")
                print("--- [THUMBNAIL GENERATION] END ---")
                return thumbnail_path

            except Exception as e:
                print(f"Thumbnail generation failed on attempt {i+1}: {e}")
                if i < 2: # Don't wait on the last attempt
                    time.sleep(2) # Wait for 2 seconds before retrying

        print("Failed to generate thumbnail after 3 attempts. Falling back to fallback thumbnail.")
        return self.generate_fallback_thumbnail(article_id, title)

    def generate_fallback_thumbnail(self, article_id, title):
        print("--- [FALLBACK THUMBNAIL GENERATION] START ---")
        font_path = self.get_font_path(bold=True)
        if not font_path: return None
        try:
            font = ImageFont.truetype(font_path, 50)
        except IOError:
            st.error(f"Failed to load font: {font_path}")
            return None
        img = Image.new('RGB', (1280, 720), color='#f0f2f5')
        d = ImageDraw.Draw(img)
        wrapped_title = textwrap.wrap(title, width=25)
        text_to_draw = '\n'.join(wrapped_title)
        text_bbox = d.textbbox((0, 0), text_to_draw, font=font)
        text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
        x, y = (1280 - text_width) / 2, (720 - text_height) / 2
        d.text((x + 3, y + 3), text_to_draw, font=font, fill='gray')
        d.text((x, y), text_to_draw, font=font, fill='black')
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        thumbnail_filename = f"thumbnail_{{article_id}}_{timestamp}.png"
        thumbnail_path = os.path.join(VIDEO_DIR, thumbnail_filename)
        img.save(thumbnail_path)
        print("--- [FALLBACK THUMBNAIL GENERATION] END ---")
        return thumbnail_path

    def generate_script_image(self, article_id, script):
        print("--- [SCRIPT IMAGE GENERATION] START ---")
        try:
            font_path = self.get_font_path()
            if not font_path: return None
            font = ImageFont.truetype(font_path, 40)
            
            img = Image.new('RGB', (1280, 720), color='#f0f2f5')
            d = ImageDraw.Draw(img)
            
            wrapped_script = textwrap.wrap(script, width=60)
            text_to_draw = '\n'.join(wrapped_script)
            
            d.text((50, 50), text_to_draw, font=font, fill='black')
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            script_image_filename = f"script_{{article_id}}_{timestamp}.png"
            script_image_path = os.path.join(VIDEO_DIR, script_image_filename)
            img.save(script_image_path)
            
            print(f"Script image saved to: {script_image_path}")
            print("--- [SCRIPT IMAGE GENERATION] END ---")
            return script_image_path
        except Exception as e:
            print(f"--- [SCRIPT IMAGE GENERATION] ERROR: {e} ---")
            return None

    def generate_tts_audio(self, script, article_id):
        print("--- [TTS GENERATION] START ---")
        try:
            tts = gTTS(text=script, lang='ko')
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            audio_filename = f"tts_{{article_id}}_{timestamp}.mp3"
            audio_path = os.path.join(VIDEO_DIR, audio_filename)
            tts.save(audio_path)
            print(f"TTS audio saved to: {audio_path}")
            print("--- [TTS GENERATION] END ---")
            return audio_path
        except Exception as e:
            print(f"--- [TTS GENERATION] ERROR: {e} ---")
            raise

    def create_video_file(self, article_id, title, script, thumbnail_path, script_image_path):
        print("--- [VIDEO CREATION - WORKAROUND] START ---")
        audio_path = None
        narration_audio = None
        try:
            # 1. Generate TTS audio
            audio_path = self.generate_tts_audio(script, article_id)
            narration_audio = mp.AudioFileClip(audio_path)
            audio_duration = narration_audio.duration

            # 2. Create clips
            intro_duration = 5
            if audio_duration < intro_duration:
                intro_duration = audio_duration
            
            thumbnail_clip = mp.ImageClip(thumbnail_path).set_duration(intro_duration)
            
            script_duration = audio_duration - intro_duration
            if script_duration < 0:
                script_duration = 0
            
            script_clip = mp.ImageClip(script_image_path).set_duration(script_duration)

            # 3. Concatenate video clips
            final_video = mp.concatenate_videoclips([thumbnail_clip, script_clip])
            
            # 4. Set the audio for the entire video
            final_clip = final_video.set_audio(narration_audio)

            # 5. Define video output path and write file
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"video_{{article_id}}_{timestamp}.mp4"
            video_path = os.path.join(VIDEO_DIR, video_filename)
            
            print(f"Writing final video to: {video_path}...")
            final_clip.write_videofile(video_path, codec='libx264', fps=24, logger='bar')
            print("Final video written successfully.")
            
            return video_path

        except Exception as e:
            print(f"--- [VIDEO CREATION] ERROR: {e} ---")
            raise

        finally:
            if narration_audio:
                narration_audio.close()
            print("--- [VIDEO CREATION] END ---")

def display_video_card(video_data):
    st.markdown(f'''<div class="video-card">
        <div class="video-title">🎬 {video_data['video_title']}</div>
    ''', unsafe_allow_html=True)

    video_path = video_data.get('video_path')
    if video_path and os.path.exists(video_path):
        st.video(video_path)
    else:
        st.warning(f"비디오 파일을 찾을 수 없습니다: {video_path}")

    st.markdown(f'''
        <div class="video-meta">
            <span>Production Date: {str(video_data['created_date'])[:10]}</span>
            <span>Views: {video_data['view_count']}</span>
            <span class="production-status status-completed">Production Complete</span>
        </div>
        <div class="script-preview">
            <p><strong>Script Preview:</strong> {video_data['script']}</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
