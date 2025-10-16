import sqlite3
import pandas as pd
import os
from datetime import datetime
from passlib.context import CryptContext
from backend.config import DB_PATH

DB_FILE = DB_PATH

# --- Password Hashing ---
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_password(password: str):
    """Hashes the password using argon2."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str):
    """Verifies a stored password against one provided by the user."""
    return pwd_context.verify(plain_password, hashed_password)

# --- DB Initialization ---
def update_schema(conn):
    c = conn.cursor()
    try:
        c.execute("PRAGMA table_info(videos)")
        columns = [info[1] for info in c.fetchall()]
        if 'script_image' not in columns:
            try:
                c.execute("ALTER TABLE videos ADD COLUMN script_image TEXT")
                conn.commit()
            except sqlite3.OperationalError:
                pass
    except sqlite3.OperationalError as e:
        if "no such table" not in str(e):
            raise e
    
    try:
        c.execute("PRAGMA table_info(view_history)")
        columns = [info[1] for info in c.fetchall()]
        if 'is_favorite' not in columns:
            try:
                c.execute("ALTER TABLE view_history ADD COLUMN is_favorite BOOLEAN DEFAULT 0")
                conn.commit()
            except sqlite3.OperationalError:
                pass
    except sqlite3.OperationalError as e:
        if "no such table" not in str(e):
            raise e

def init_db():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    c = conn.cursor()
    
    # --- Table Creation ---
    c.execute("""
    CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT,
        url TEXT UNIQUE,
        summary TEXT,
        content TEXT,
        keywords TEXT,
        is_age_relevant BOOLEAN,
        crawled_date TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS videos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        video_title TEXT,
        script TEXT,
        thumbnail TEXT,
        script_image TEXT,
        video_path TEXT,
        production_status TEXT,
        view_count INTEGER DEFAULT 0,
        created_date TIMESTAMP,
        FOREIGN KEY(article_id) REFERENCES articles(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS generated_articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER,
        generated_title TEXT,
        generated_content TEXT,
        created_date TIMESTAMP,
        FOREIGN KEY(article_id) REFERENCES articles(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS view_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        content_id INTEGER NOT NULL,
        content_type TEXT NOT NULL, -- 'article' or 'video'
        viewed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        is_favorite BOOLEAN DEFAULT 0,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)

    c.execute("""
    CREATE TABLE IF NOT EXISTS chat_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(user_id) REFERENCES users(id)
    )
    """)
    
    update_schema(conn)
    conn.commit()
    return conn

# --- User Management Functions ---
def add_user(conn, email, password):
    """Adds a new user to the database with a hashed password."""
    c = conn.cursor()
    hashed_password = hash_password(password)
    try:
        c.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        # Email already exists
        return False

def get_user(conn, email):
    """Retrieves a user by email."""
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE email = ?", (email,))
    user = c.fetchone()
    if user:
        # Return as a dictionary
        return {'id': user[0], 'email': user[1], 'password': user[2]}
    return None

# --- Chat History Functions ---
def save_chat_message(conn, user_id, role, content):
    """Saves a chat message to the database."""
    c = conn.cursor()
    c.execute("INSERT INTO chat_history (user_id, role, content) VALUES (?, ?, ?)", (user_id, role, content))
    conn.commit()

def get_chat_history(conn, user_id):
    """Retrieves the chat history for a user."""
    c = conn.cursor()
    c.execute("SELECT id, role, content, timestamp FROM chat_history WHERE user_id = ? ORDER BY timestamp ASC", (user_id,))
    history = c.fetchall()
    return [{"id": id, "role": role, "content": content, "timestamp": timestamp} for id, role, content, timestamp in history]

def delete_chat_history_item(conn, message_id):
    """Deletes a single chat message."""
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE id = ?", (message_id,))
    conn.commit()

def delete_all_chat_history(conn, user_id):
    """Deletes all chat history for a user."""
    c = conn.cursor()
    c.execute("DELETE FROM chat_history WHERE user_id = ?", (user_id,))
    conn.commit()

# --- View History Functions ---
def add_view_history(conn, user_id, content_id, content_type):
    """Adds a view history record for a user."""
    c = conn.cursor()
    c.execute("INSERT INTO view_history (user_id, content_id, content_type) VALUES (?, ?, ?)", (user_id, content_id, content_type))
    conn.commit()

def get_view_history(conn, user_id):
    """Retrieves the view history for a user."""
    query = """
        SELECT 
            vh.id,
            vh.content_type, 
            vh.viewed_at, 
            vh.is_favorite,
            CASE 
                WHEN vh.content_type = 'article' THEN a.title
                WHEN vh.content_type = 'video' THEN v.video_title
            END as title
        FROM view_history vh
        LEFT JOIN articles a ON vh.content_id = a.id AND vh.content_type = 'article'
        LEFT JOIN videos v ON vh.content_id = v.id AND vh.content_type = 'video'
        WHERE vh.user_id = ?
        ORDER BY vh.viewed_at DESC
    """
    return pd.read_sql_query(query, conn, params=(user_id,))

def toggle_favorite(conn, history_id):
    """Toggles the favorite status of a history item."""
    c = conn.cursor()
    c.execute("UPDATE view_history SET is_favorite = NOT IS_FAVORITE WHERE id = ?", (history_id,))
    conn.commit()

def delete_history_item(conn, history_id):
    """Deletes a history item."""
    c = conn.cursor()
    c.execute("DELETE FROM view_history WHERE id = ?", (history_id,))
    conn.commit()

def delete_all_history(conn, user_id):
    """Deletes all view history for a user."""
    c = conn.cursor()
    c.execute("DELETE FROM view_history WHERE user_id = ?", (user_id,))
    conn.commit()

# --- Article and Video Functions ---
def get_articles_with_filter(conn, status='전체', sort_order='최신순', limit=20):
    base_query = """
        SELECT a.* 
        FROM articles a
        LEFT JOIN generated_articles g ON a.id = g.article_id
        LEFT JOIN videos v ON a.id = v.article_id
        WHERE a.is_age_relevant = 1
    """
    
    filter_conditions = ""
    if status == 'AI 기사 생성 대기':
        filter_conditions = "AND g.id IS NULL"
    elif status == '영상 제작 대기':
        filter_conditions = "AND g.id IS NOT NULL AND v.id IS NULL"
    elif status == '제작 완료':
        filter_conditions = "AND v.id IS NOT NULL"

    order_clause = "ORDER BY a.crawled_date DESC" if sort_order == '최신순' else "ORDER BY a.crawled_date ASC"
    
    limit_clause = f"LIMIT {limit}"

    query = f"{base_query} {filter_conditions} {order_clause} {limit_clause}"
    
    return pd.read_sql_query(query, conn)

def get_produced_videos(conn):
    conn.row_factory = sqlite3.Row
    return pd.read_sql_query("""
    SELECT v.*, a.title AS article_title
    FROM videos v
    JOIN articles a ON v.article_id = a.id
    ORDER BY v.created_date DESC
    """, conn)

def get_crawl_stats(conn):
    return pd.read_sql_query("SELECT crawled_date, COUNT(*) as count FROM articles GROUP BY DATE(crawled_date)", conn)

def get_stored_articles(conn, age_relevant_only=True, limit=20):
    query = "SELECT * FROM articles WHERE 1=1 "
    params = []
    if age_relevant_only:
        query += "AND is_age_relevant = 1 "
    
    query += "ORDER BY crawled_date DESC LIMIT ?"
    params.append(limit)
    
    return pd.read_sql_query(query, conn, params=params)

def get_article_and_video(conn, article_id):
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
    article_data = c.fetchone()

    c.execute("SELECT * FROM videos WHERE article_id = ?", (article_id,))
    video_data = c.fetchone()
    
    c.execute("SELECT * FROM generated_articles WHERE article_id = ? ORDER BY created_date DESC LIMIT 1", (article_id,))
    generated_article_data = c.fetchone()

    return dict(article_data) if article_data else None, dict(video_data) if video_data else None, dict(generated_article_data) if generated_article_data else None

def add_view_count(conn, article_id):
    conn.execute("UPDATE videos SET view_count = view_count + 1 WHERE article_id = ?", (article_id,))
    conn.commit()

def save_generated_article(conn, article_data):
    c = conn.cursor()
    c.execute("""
        INSERT INTO generated_articles (article_id, generated_title, generated_content, created_date)
        VALUES (?, ?, ?, ?)
    """, (
        article_data['article_id'],
        article_data['generated_title'],
        article_data['generated_content'],
        datetime.now()
    ))
    conn.commit()
    return c.lastrowid

def get_generated_article(conn, article_id):
    query = "SELECT * FROM generated_articles WHERE article_id = ? ORDER BY created_date DESC LIMIT 1"
    df = pd.read_sql_query(query, conn, params=[article_id])
    return df.iloc[0].to_dict() if not df.empty else None

def delete_video(conn, video_id):
    """Deletes a video record from the database and returns its file path."""
    c = conn.cursor()
    
    # First, get the path of the video file to delete it from the filesystem
    c.execute("SELECT video_path FROM videos WHERE id = ?", (video_id,))
    result = c.fetchone()
    video_path = result[0] if result else None
    
    if video_path:
        # Delete the record from the database
        c.execute("DELETE FROM videos WHERE id = ?", (video_id,))
        conn.commit()
        return video_path
    return None
