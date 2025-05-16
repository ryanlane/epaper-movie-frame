import os
import sqlite3

DB_PATH = "database.sqlite"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    if not os.path.exists(DB_PATH):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                VideoRootPath TEXT,
                Resolution TEXT
            )
        ''')

        cur.execute('''
            CREATE TABLE IF NOT EXISTS Movie (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                video_path TEXT,
                total_frames INTEGER,
                time_per_frame INTEGER,
                skip_frames INTEGER,
                current_frame INTEGER,
                isActive BOOLEAN DEFAULT 0,
                isRandom BOOLEAN DEFAULT 0
            )
        ''')

        conn.commit()
        conn.close()

def get_settings():
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM Settings LIMIT 1").fetchone()
    conn.close()
    return settings

def insert_default_settings():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Settings (VideoRootPath, Resolution) VALUES (?, ?)", ("videos", "800,480"))
    conn.commit()
    conn.close()

def get_all_movies():
    conn = get_db_connection()
    movies = conn.execute('SELECT * FROM Movie').fetchall()
    conn.close()
    return movies

def get_movie_by_id(movie_id):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM Movie WHERE id = ?', (movie_id,)).fetchone()
    conn.close()
    return movie

def get_movie_by_path(video_path):
    conn = get_db_connection()
    movie = conn.execute('SELECT * FROM Movie WHERE video_path = ?', (video_path,)).fetchone()
    conn.close()
    return movie

def insert_movie(video_path, total_frames):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO Movie (video_path, total_frames, time_per_frame, skip_frames, current_frame, isActive, isRandom)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (video_path, total_frames, 60, 1, 1, 0, 0))
    conn.commit()
    movie_id = cur.lastrowid
    movie = conn.execute('SELECT * FROM Movie WHERE id = ?', (movie_id,)).fetchone()
    conn.close()
    return movie

def update_movie(payload):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('''
        UPDATE Movie SET
            time_per_frame = ?,
            skip_frames = ?,
            current_frame = ?,
            isRandom = ?
        WHERE id = ?
    ''', (
        int(payload['time_per_frame']),
        int(payload['skip_frames']),
        int(payload['current_frame']),
        int(payload.get('isRandom', 0)),
        int(payload['id'])
    ))
    conn.commit()
    updated_movie = conn.execute('SELECT * FROM Movie WHERE id = ?', (payload['id'],)).fetchone()
    conn.close()
    return updated_movie

def delete_movie(movie_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute('SELECT * FROM Movie WHERE id = ?', (movie_id,))
    movie = cur.fetchone()
    if movie:
        cur.execute('DELETE FROM Movie WHERE id = ?', (movie_id,))
        conn.commit()
    conn.close()
    return movie
