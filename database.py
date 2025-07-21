import os
import sqlite3
from utils import config

DB_PATH = "database.sqlite"

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    is_new_db = not os.path.exists(DB_PATH)
    conn = get_db_connection()
    cur = conn.cursor()

    # Always ensure core tables exist
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
            isRandom BOOLEAN DEFAULT 0,
            use_quiet_hours BOOLEAN DEFAULT 0,
            quiet_start INTEGER DEFAULT 22,
            quiet_end INTEGER DEFAULT 7
        )
    ''')

    cur.execute('''
        CREATE UNIQUE INDEX IF NOT EXISTS unique_active_movie
        ON Movie (isActive)
        WHERE isActive = 1
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS NowPlaying (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            movie_id INTEGER NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS SchemaVersion (
            version INTEGER
        )
    ''')

    # If brand new DB, initialize schema version
    if is_new_db:
        cur.execute("INSERT INTO SchemaVersion (version) VALUES (2)")

    conn.commit()
    conn.close()

    # Apply migrations for older DBs
    run_migrations()


def get_settings():
    conn = get_db_connection()
    settings = conn.execute("SELECT * FROM Settings LIMIT 1").fetchone()
    conn.close()
    return settings

def insert_default_settings():
    config_data = config.read_toml_file("config.toml")
    video_root = config_data.get("VIDEO_DIRECTORY", "videos")
    width = config_data.get("TARGET_WIDTH", 800)
    height = config_data.get("TARGET_HEIGHT", 480)
    resolution = f"{width},{height}"

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("INSERT INTO Settings (VideoRootPath, Resolution) VALUES (?, ?)", (video_root, resolution))
    conn.commit()
    conn.close()

def update_video_root_path():
    config_data = config.read_toml_file("config.toml")
    new_path = config_data.get("VIDEO_DIRECTORY")
    if new_path:
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE Settings SET VideoRootPath = ? WHERE id = 1", (new_path,))
        conn.commit()
        conn.close()

def update_current_frame(movie_id, current_frame):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Movie SET current_frame = ? WHERE id = ?", (current_frame, movie_id))
    conn.commit()
    conn.close()

def check_config_against_settings():
    config_data = config.read_toml_file("config.toml")
    config_path = config_data.get("VIDEO_DIRECTORY")
    width = config_data.get("TARGET_WIDTH")
    height = config_data.get("TARGET_HEIGHT")
    config_res = f"{width},{height}"

    settings = get_settings()
    db_path = settings['VideoRootPath']
    db_res = settings['Resolution']

    if config_path != db_path or config_res != db_res:
        print("\n[CONFIG CHECK] Your config.toml values differ from what's stored in the database:")
        if config_path != db_path:
            print(f" - VIDEO_DIRECTORY: database = '{db_path}', config = '{config_path}'")
        if config_res != db_res:
            print(f" - RESOLUTION: database = '{db_res}', config = '{config_res}'")

        choice = input("\nWould you like to update the database settings to match config.toml? (y/n): ").strip().lower()
        if choice == 'y':
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute("UPDATE Settings SET VideoRootPath = ?, Resolution = ? WHERE id = 1", (config_path, config_res))
            conn.commit()
            conn.close()
            print("[CONFIG UPDATED] Database settings updated to match config.toml.\n")
        else:
            print("[CONFIG SKIPPED] Database settings were not changed.\n")


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
            isRandom = ?,
            total_frames = ?
        WHERE id = ?
    ''', (
        int(payload['time_per_frame']),
        int(payload['skip_frames']),
        int(payload['current_frame']),
        int(payload.get('isRandom', 0)),
        int(payload['total_frames']),
        int(payload['id'])
    ))
    conn.commit()
    updated_movie = conn.execute('SELECT * FROM Movie WHERE id = ?', (payload['id'],)).fetchone()
    conn.close()
    return updated_movie


def get_active_movie():
    conn = get_db_connection()
    movie = conn.execute("SELECT * FROM Movie WHERE isActive = 1 LIMIT 1").fetchone()
    conn.close()
    return movie

def set_now_playing(movie_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("DELETE FROM NowPlaying")  # always just one
    cur.execute("INSERT INTO NowPlaying (movie_id) VALUES (?)", (movie_id,))
    conn.commit()
    conn.close()

def get_now_playing():
    conn = get_db_connection()
    result = conn.execute("SELECT movie_id FROM NowPlaying LIMIT 1").fetchone()
    conn.close()
    return result['movie_id'] if result else None


def set_active_movie(movie_id):
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Movie SET isActive = 0")
    cur.execute("UPDATE Movie SET isActive = 1 WHERE id = ?", (movie_id,))
    conn.commit()
    conn.close()

def clear_active_movie():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("UPDATE Movie SET isActive = 0")
    conn.commit()
    conn.close()


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

def get_schema_version():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        # Try to fetch the version
        version = cur.execute("SELECT version FROM SchemaVersion").fetchone()
        if version:
            return version['version']
        else:
            # Table exists but no row yet
            cur.execute("INSERT INTO SchemaVersion (version) VALUES (1)")
            conn.commit()
            return 1
    except sqlite3.OperationalError:
        # Table doesn't exist — create it and initialize
        cur.execute('''
            CREATE TABLE IF NOT EXISTS SchemaVersion (
                version INTEGER
            )
        ''')
        cur.execute("INSERT INTO SchemaVersion (version) VALUES (1)")
        conn.commit()
        return 1
    finally:
        conn.close()


def run_migrations():
    current_version = get_schema_version()
    conn = get_db_connection()
    cur = conn.cursor()

    if current_version < 2:
        print("🔧 Applying schema migration to version 2...")
        cur.execute("ALTER TABLE Movie ADD COLUMN use_quiet_hours BOOLEAN DEFAULT 0")
        cur.execute("ALTER TABLE Movie ADD COLUMN quiet_start INTEGER DEFAULT 22")
        cur.execute("ALTER TABLE Movie ADD COLUMN quiet_end INTEGER DEFAULT 7")
        cur.execute("UPDATE SchemaVersion SET version = 2")
        conn.commit()

    # Future migrations:
    # if current_version < 3:
    #     cur.execute(...)
    #     cur.execute("UPDATE SchemaVersion SET version = 3")

    conn.close()
