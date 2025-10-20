import streamlit as st
import requests
import os
from PIL import Image, ImageDraw, ImageFont
import textwrap
import sys
from datetime import datetime
import moviepy.editor as mp
from gtts import gTTS
import time
import re
import numpy as np
import random
import logging

# Basic logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - [%(funcName)s] %(message)s')


# Monkey patch for Pillow < 10.0.0
if not hasattr(Image, 'Resampling'):
    Image.Resampling = Image
if not hasattr(Image, 'ANTIALIAS'):
    Image.ANTIALIAS = Image.LANCZOS

# Add the directory of the current file to the system path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from database import init_db
from backend.config import GENERATED_VIDEOS_DIR, data_dir

# OpenAI client
from openai import OpenAI

# ===== Global output dir =====
VIDEO_DIR = GENERATED_VIDEOS_DIR

class VideoProducer:
    def __init__(self):
        self.api_key = os.environ.get("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable not set.")
        self.client = OpenAI(api_key=self.api_key)

        self.W, self.H = 1280, 720   # 16:9
        self.FPS = 30

    # -------------------------------
    # Public entry: 기사+스크립트 → 비디오 메타
    # -------------------------------
    def produce_video_content(self, article, script):
        """
        article: {'id': int/str, 'title': str, 'crawled_date': 'YYYY-MM-DD ...'}
        script:  str (나레이션 본문)
        """
        article_id   = article['id']
        title        = article['title']
        crawled_date = article['crawled_date']

        video_path = self.create_video_file(article_id, title, script)

        video_data = {
            'article_id': article_id,
            'video_title': title,
            'script': script,
            'thumbnail': None,
            'script_image': None,
            'video_path': video_path,
            'production_status': 'completed',
            'created_date': crawled_date,
            'view_count': 0
        }
        return video_data

    # -------------------------------
    # DB 저장
    # -------------------------------
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

    # -------------------------------
    # 폰트 경로 (한글 깨짐 방지: 나눔고딕/Noto 우선)
    # -------------------------------
    def get_font_path(self, bold=False):
        candidates = []
        if os.name == "nt":  # Windows
            candidates += [
                "C:/Windows/Fonts/NanumGothicBold.ttf" if bold else "C:/Windows/Fonts/NanumGothic.ttf",
                "C:/Windows/Fonts/malgunbd.ttf" if bold else "C:/Windows/Fonts/malgun.ttf",
            ]
        else:  # Linux/Mac
            candidates += [
                "/usr/share/fonts/truetype/nanum/NanumGothicBold.ttf" if bold else "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            ]

        for p in candidates:
            if p and os.path.exists(p):
                return p
        # 마지막 수단
        st.warning("한글 폰트를 찾지 못해 기본 폰트를 사용합니다. 자막 품질이 낮아질 수 있습니다.")
        return None

    # -------------------------------
    # 이미지 생성 (문장별 개별 생성)
    # -------------------------------
    def generate_ai_image(self, prompt_text, image_path):
        """
        DALL·E 3으로 프롬프트 기반 일러스트 생성.
        실패 시 False 반환.
        """
        logging.info(f"--- [AI Image] PROMPT: {prompt_text[:100]} ... ---")
        for i in range(3):
            try:
                prompt = (
                    "A clean, modern, and engaging illustration for a Korean news video. "
                    "Soft, friendly color palette. Absolutely no text in the image. "
                    "Style: Flat design, simple, clear, optimistic. "
                    f'Story focus: "{prompt_text}"'
                )
                resp = self.client.images.generate(
                    model="dall-e-3",
                    prompt=prompt,
                    size="1792x1024",
                    quality="standard",
                    n=1,
                )
                image_url = resp.data[0].url
                r = requests.get(image_url, timeout=60)
                r.raise_for_status()
                with open(image_path, "wb") as f:
                    f.write(r.content)
                logging.info(f"[AI Image] saved: {image_path}")
                return True
            except Exception as e:
                logging.warning(f"[AI Image] attempt {i+1} failed: {e}")
                time.sleep(3)
        return False

    def generate_scene_image(self, sentence, article_id, idx):
        out_path = os.path.join(VIDEO_DIR, f"scene_{article_id}_{idx:02d}.png")
        ok = self.generate_ai_image(sentence, out_path)
        if ok:
            return out_path
        # fallback 단색
        fallback = Image.new('RGB', (self.W, self.H), color=tuple(random.randint(0, 255) for _ in range(3)))
        fallback_path = os.path.join(VIDEO_DIR, f"scene_fallback_{article_id}_{idx:02d}.png")
        fallback.save(fallback_path)
        return fallback_path

    # -------------------------------
    # 캡션 이미지 렌더링 (반투명 박스 + 중앙 정렬)
    # -------------------------------
    def render_caption_image(self, text: str) -> np.ndarray:
        FONT_SIZE = 36
        MARGIN = 60
        LINE_SPACING = 12
        CAPTION_BOX_ALPHA = 180
        CAPTION_BOTTOM_PAD = 80
        CAPTION_MAX_CHARS = 30

        font_path_bold = self.get_font_path(bold=True)
        font = ImageFont.truetype(font_path_bold, FONT_SIZE) if font_path_bold else ImageFont.load_default()

        # 측정용
        dummy = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(dummy)

        wrapper = textwrap.TextWrapper(width=CAPTION_MAX_CHARS, break_long_words=True, replace_whitespace=False)
        lines = [line for para in text.split("\n") for line in (wrapper.wrap(para) if para else [""])]

        line_heights, max_line_w = [], 0
        for line in lines:
            bbox = draw.textbbox((0, 0), line, font=font)
            lw = bbox[2] - bbox[0]
            lh = bbox[3] - bbox[1]
            line_heights.append(lh)
            max_line_w = max(max_line_w, lw)

        text_block_h = sum(line_heights) + LINE_SPACING * max(0, len(lines) - 1)
        box_pad_x, box_pad_y = 28, 24
        box_w = min(max_line_w + box_pad_x * 2, self.W - MARGIN * 2)
        box_h = text_block_h + box_pad_y * 2

        box_x = (self.W - box_w) // 2
        box_y = self.H - CAPTION_BOTTOM_PAD - box_h

        img = Image.new("RGBA", (self.W, self.H), (0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        radius = 24
        draw.rounded_rectangle([(box_x, box_y), (box_x + box_w, box_y + box_h)],
                               radius=radius, fill=(0, 0, 0, CAPTION_BOX_ALPHA))
        # 텍스트
        cur_y = box_y + box_pad_y
        for i, line in enumerate(lines):
            lw = draw.textbbox((0, 0), line, font=font)[2] - draw.textbbox((0, 0), line, font=font)[0]
            tx = (self.W - lw) // 2
            draw.text((tx, cur_y), line, font=font, fill=(255, 255, 255, 255))
            cur_y += line_heights[i] + LINE_SPACING

        return np.array(img)

    # -------------------------------
    # Ken Burns (줌 + 약한 패닝 느낌)
    # -------------------------------
    def ken_burns(self, img_path, duration):
        base = mp.ImageClip(img_path).set_duration(duration)
        zoom_rate = random.uniform(0.015, 0.03)  # 1.5%~3%/sec
        scaled = base.fx(mp.vfx.resize, lambda t: 1 + zoom_rate * t)
        return scaled.resize((self.W, self.H))

    def _generate_intro_sentence(self, title: str) -> str:
        """Generates a friendly, natural-sounding intro sentence from a news title."""
        logging.info(f"--- [Intro Generation] Generating intro for title: {title} ---")
        try:
            system_prompt = "You are a friendly and engaging announcer for a senior health news video."
            user_prompt = f"""Based on the following news headline, create a warm and welcoming opening sentence for the video. The sentence should be concise, natural-sounding, and in Korean.

Headline: '{title}'

Example:
- If the headline is 'A new study finds apples are effective for heart health [Reporter Kim]', a good opening would be '안녕하세요! 오늘은 사과가 심장 건강에 어떤 도움을 주는지 함께 알아보겠습니다.'
- If the headline is 'The importance of regular check-ups for preventing diabetes', a good opening would be '안녕하세요, 건강에 관심 많은 시청자 여러분! 정기적인 건강검진이 당뇨 예방에 얼마나 중요한지 알고 계신가요?'

Now, create the opening sentence for the headline provided above."""

            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,
                max_tokens=100,
            )
            intro_sentence = response.choices[0].message.content.strip()
            logging.info(f"--- [Intro Generation] Generated intro: {intro_sentence} ---")
            return intro_sentence
        except Exception as e:
            logging.error(f"--- [Intro Generation] Failed, falling back to title. Error: {e} ---", exc_info=True)
            return title # Fallback to the original title on error

    # -------------------------------
    # 메인: 동기 합성 파이프라인
    # -------------------------------
    def create_video_file(self, article_id, title, script):
        logging.info("--- [SYNCHRONIZED VIDEO CREATION] START ---")
        temp_files = []
        video_clips = []
        audio_clips = []

        try:
            # 1) 문장 분할
            sentences = [s.strip() for s in re.split(r'[.!?…]+', script) if s.strip()]
            if not sentences:
                raise ValueError("Script could not be split into sentences.")

            # 2) 인트로: 자연스러운 인트로 문장 생성 + TTS + 이미지
            intro_text = self._generate_intro_sentence(title)
            clean_intro_text = re.sub(r'\*\*', '', intro_text)
            intro_audio_path = os.path.join(VIDEO_DIR, f"intro_audio_{article_id}.mp3")
            
            logging.info("--- [Video Gen] Generating intro TTS... ---")
            gTTS(text=clean_intro_text, lang='ko').save(intro_audio_path)
            temp_files.append(intro_audio_path)
            logging.info("--- [Video Gen] Intro TTS generated. ---")

            intro_audio = mp.AudioFileClip(intro_audio_path)
            logging.info("--- [Video Gen] Intro audio clip created. ---")

            intro_img_path = self.generate_scene_image(title, article_id, 999)
            logging.info(f"--- [Video Gen] Intro image generated at: {intro_img_path} ---")

            intro_bg = self.ken_burns(intro_img_path, intro_audio.duration)
            logging.info("--- [Video Gen] Ken Burns effect applied to intro. ---")

            intro_caption = mp.ImageClip(self.render_caption_image(clean_intro_text)).set_duration(intro_audio.duration)
            logging.info("--- [Video Gen] Intro caption rendered. ---")

            intro_scene = mp.CompositeVideoClip([intro_bg, intro_caption], size=(self.W, self.H)).fx(mp.vfx.fadein, 0.6)
            logging.info("--- [Video Gen] Intro scene composited. ---")

            video_clips.append(intro_scene)
            audio_clips.append(intro_audio)

            # 3) 본문: 3문장씩 묶어서 처리
            SCENE_CHUNK_SIZE = 3
            sentence_chunks = [sentences[i:i + SCENE_CHUNK_SIZE] for i in range(0, len(sentences), SCENE_CHUNK_SIZE)]

            for i, chunk in enumerate(sentence_chunks):
                # Concatenate sentences in the chunk for prompts and captions
                chunk_text = " ".join(chunk)
                clean_chunk_text = re.sub(r'\*\*', '', chunk_text)
                logging.info(f"[Scene {i+1}/{len(sentence_chunks)}] Processing chunk: {chunk_text[:70]}...")

                # --- Generate single image for the whole chunk ---
                img_path = self.generate_scene_image(chunk_text, article_id, i)
                logging.info(f"--- [Video Gen] Scene {i+1} image generated. ---")

                # --- Generate TTS for each sentence and combine them ---
                chunk_audio_clips = []
                for j, sentence in enumerate(chunk):
                    clean_sentence = re.sub(r'\*\*', '', sentence)
                    scene_audio_path = os.path.join(VIDEO_DIR, f"scene_audio_{article_id}_{i}_{j}.mp3")
                    gTTS(text=clean_sentence, lang='ko').save(scene_audio_path)
                    temp_files.append(scene_audio_path) # Add to main temp_files for cleanup
                    chunk_audio_clips.append(mp.AudioFileClip(scene_audio_path))
                
                if not chunk_audio_clips:
                    continue

                concatenated_audio = mp.concatenate_audioclips(chunk_audio_clips)
                duration = max(1.8 * len(chunk), concatenated_audio.duration) # Ensure minimum duration
                logging.info(f"--- [Video Gen] Scene {i+1} combined audio created with duration {duration}s. ---")

                # --- Create visuals for the chunk ---
                bg = self.ken_burns(img_path, duration)
                logging.info(f"--- [Video Gen] Scene {i+1} Ken Burns effect applied. ---")

                # Caption for the whole chunk
                caption = mp.ImageClip(self.render_caption_image(clean_chunk_text)).set_duration(duration)
                logging.info(f"--- [Video Gen] Scene {i+1} caption rendered. ---")

                scene = mp.CompositeVideoClip([bg, caption], size=(self.W, self.H)).fx(mp.vfx.fadein, 0.25)
                logging.info(f"--- [Video Gen] Scene {i+1} composited. ---")

                video_clips.append(scene)
                audio_clips.append(concatenated_audio)

            # 4) 연결 + 오디오 세팅 + 아웃로 페이드
            final_video = mp.concatenate_videoclips(video_clips, method="compose")
            final_audio = mp.concatenate_audioclips(audio_clips)
            final_video = final_video.set_audio(final_audio).fx(mp.vfx.fadeout, 0.5)

            # 5) 파일명(중괄호 버그 수정) + 저장
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            video_filename = f"video_{article_id}_{timestamp}.mp4"
            video_path = os.path.join(VIDEO_DIR, video_filename)

            logging.info(f"Writing final video to: {video_path} ...")
            logging.info(f"Value of VIDEO_DIR is: {VIDEO_DIR}")
            logging.info(f"Value of data_dir from config is: {data_dir}")
            
            final_video.write_videofile(
                video_path,
                codec='libx264',
                audio_codec="aac",
                fps=self.FPS,
                threads=4,
                preset="ultrafast",
                bitrate="3000k"
            )

            # flush 확인
            for _ in range(10):
                if os.path.exists(video_path) and os.path.getsize(video_path) > 0:
                    break
                time.sleep(0.5)

            # Add a definitive check
            if os.path.exists(video_path):
                logging.info(f"CONFIRMED: Video file exists at {video_path} after writing.")
            else:
                logging.warning(f"PROBLEM: Video file DOES NOT exist at {video_path} after writing.")

            logging.info("Final video written successfully.")

            # Return a path relative to the data_dir for database storage
            relative_video_path = os.path.join('generated_videos', video_filename)
            return relative_video_path

        except Exception as e:
            logging.error(f"--- [SYNCHRONIZED VIDEO CREATION] ERROR: {e} ---", exc_info=True)
            raise

        finally:
            logging.info("Cleaning up clips and temporary files...")
            # clip close
            for clip in video_clips:
                try:
                    if clip and hasattr(clip, 'close'): clip.close()
                except Exception:
                    pass
            for a in audio_clips:
                try:
                    if a and hasattr(a, 'close'): a.close()
                except Exception:
                    pass
            # temp remove
            for p in temp_files:
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception as ee:
                    logging.warning(f"Temp remove error {p}: {ee}")
            logging.info("--- [SYNCHRONIZED VIDEO CREATION] END ---")

# -------------------------------
# Streamlit 카드 표시 (KeyError 방지)
# -------------------------------

def display_video_card(video_data):
    st.markdown(f'''<div class="video-card">
        <div class="video-title">🎬 {video_data.get('video_title','')}
    ''', unsafe_allow_html=True)

    video_path_from_db = video_data.get('video_path')
    
    # video_path_from_db가 절대 경로가 아닐 수 있으므로, data_dir를 기준으로 절대 경로를 구성합니다.
    if video_path_from_db:
        if not os.path.isabs(video_path_from_db):
            video_path = os.path.join(data_dir, video_path_from_db)
        else:
            video_path = video_path_from_db

        logging.info(f"Attempting to display video. Checking for file at path: {video_path}")
        if os.path.exists(video_path):
            st.video(video_path)
        else:
            logging.warning(f"File check failed. os.path.exists returned False for path: {video_path}")
            st.warning(f"비디오 파일을 찾을 수 없습니다: {video_path}")
    else:
        st.warning("비디오 경로 정보가 없습니다.")


    st.markdown(f'''
        <div class="video-meta">
            <span>Production Date: {str(video_data.get('created_date',''))[:10]}</span>
            <span>Views: {video_data.get('view_count', 0)}</span>
            <span class="production-status status-completed">Production Complete</span>
        </div>
        <div class="script-preview">
            <p><strong>Script Preview:</strong> {video_data.get('script','')}</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)
