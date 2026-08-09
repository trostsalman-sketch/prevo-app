from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from database import init_db, get_connection
from auth import get_current_user
import os
import uuid

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

os.makedirs("uploads", exist_ok=True)
os.makedirs("uploads/characters", exist_ok=True)
os.makedirs("uploads/posts", exist_ok=True)
os.makedirs("uploads/market", exist_ok=True)
os.makedirs("uploads/reports", exist_ok=True)

app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")

@app.on_event("startup")
def startup():
    init_db()

@app.get("/")
async def root():
    return {"status": "API работает"}

@app.post("/api/auth")
async def auth(user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id = ?", (user['id'],))
    existing = c.fetchone()
    
    if not existing:
        c.execute("""INSERT INTO users (telegram_id, username, first_name, avatar) 
                     VALUES (?, ?, ?, ?)""",
                  (user['id'], user.get('username', ''), 
                   user.get('first_name', ''), 
                   user.get('photo_url', '')))
        conn.commit()
    
    c.execute("SELECT role FROM admins WHERE telegram_id = ?", (user['id'],))
    admin = c.fetchone()
    role = admin['role'] if admin else 'user'
    
    conn.close()
    return {"status": "ok", "user": user, "role": role}

@app.post("/api/character")
async def create_character(
    photo: UploadFile = File(...),
    name: str = Form(...),
    age: int = Form(...),
    height: int = Form(...),
    weight: int = Form(...),
    bio: str = Form(...),
    user: dict = Depends(get_current_user)
):
    file_ext = photo.filename.split('.')[-1]
    filename = f"uploads/characters/{uuid.uuid4()}.{file_ext}"
    with open(filename, "wb") as f:
        f.write(await photo.read())
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO characters (telegram_id, photo, name, age, height, weight, bio)
                 VALUES (?, ?, ?, ?, ?, ?, ?)""",
              (user['id'], filename, name, age, height, weight, bio))
    conn.commit()
    conn.close()
    return {"status": "submitted"}

@app.post("/api/post")
async def create_post(
    photo: UploadFile = File(None),
    description: str = Form(...),
    hashtags: str = Form(""),
    user: dict = Depends(get_current_user)
):
    photo_path = ""
    if photo:
        file_ext = photo.filename.split('.')[-1]
        photo_path = f"uploads/posts/{uuid.uuid4()}.{file_ext}"
        with open(photo_path, "wb") as f:
            f.write(await photo.read())
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO posts (telegram_id, photo, description, hashtags)
                 VALUES (?, ?, ?, ?)""",
              (user['id'], photo_path, description, hashtags))
    post_id = c.lastrowid
    conn.commit()
    conn.close()
    return {"status": "created", "id": post_id}

@app.get("/api/posts")
async def get_posts():
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT p.*, u.first_name, u.username, u.avatar,
                 (SELECT COUNT(*) FROM likes WHERE post_id = p.id) as likes_count,
                 (SELECT COUNT(*) FROM comments WHERE post_id = p.id) as comments_count
                 FROM posts p LEFT JOIN users u ON p.telegram_id = u.telegram_id
                 ORDER BY p.created_at DESC""")
    posts = [dict(row) for row in c.fetchall()]
    conn.close()
    return posts

@app.post("/api/post/{post_id}/like")
async def like_post(post_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO likes (post_id, telegram_id) VALUES (?, ?)",
                  (post_id, user['id']))
    except:
        c.execute("DELETE FROM likes WHERE post_id = ? AND telegram_id = ?",
                  (post_id, user['id']))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.post("/api/post/{post_id}/comment")
async def comment_post(post_id: int, text: str = Form(...),
                       user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("INSERT INTO comments (post_id, telegram_id, text) VALUES (?, ?, ?)",
              (post_id, user['id'], text))
    conn.commit()
    conn.close()
    return {"status": "ok"}

@app.get("/api/post/{post_id}/comments")
async def get_comments(post_id: int):
    conn = get_connection()
    c = conn.cursor()
    c.execute("""SELECT c.*, u.first_name, u.avatar FROM comments c
                 LEFT JOIN users u ON c.telegram_id = u.telegram_id
                 WHERE c.post_id = ? ORDER BY c.created_at""", (post_id,))
    comments = [dict(row) for row in c.fetchall()]
    conn.close()
    return comments

@app.post("/api/report")
async def create_report(
    reporter: str = Form(...),
    violator: str = Form(...),
    reason: str = Form(...),
    evidence: UploadFile = File(None),
    user: dict = Depends(get_current_user)
):
    evidence_path = ""
    if evidence:
        file_ext = evidence.filename.split('.')[-1]
        evidence_path = f"uploads/reports/{uuid.uuid4()}.{file_ext}"
        with open(evidence_path, "wb") as f:
            f.write(await evidence.read())
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO reports (reporter, violator, reason, evidence)
                 VALUES (?, ?, ?, ?)""",
              (reporter, violator, reason, evidence_path))
    conn.commit()
    conn.close()
    return {"status": "submitted"}

@app.post("/api/market")
async def create_market_item(
    photo: UploadFile = File(...),
    description: str = Form(...),
    contact: str = Form(...)
):
    file_ext = photo.filename.split('.')[-1]
    photo_path = f"uploads/market/{uuid.uuid4()}.{file_ext}"
    with open(photo_path, "wb") as f:
        f.write(await photo.read())
    
    conn = get_connection()
    c = conn.cursor()
    c.execute("""INSERT INTO market (photo, description, contact)
                 VALUES (?, ?, ?)""",
              (photo_path, description, contact))
    conn.commit()
    conn.close()
    return {"status": "created"}

@app.get("/api/market")
async def get_market():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM market ORDER BY created_at DESC")
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    return items

@app.get("/api/irp")
async def get_irp():
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT * FROM reports WHERE status = 'approved' ORDER BY created_at DESC")
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    return items

@app.get("/api/admin/characters")
async def admin_characters(user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ?", (user['id'],))
    admin = c.fetchone()
    if not admin:
        raise HTTPException(status_code=403, detail="Access denied")
    
    c.execute("SELECT * FROM characters WHERE status = 'pending' ORDER BY created_at DESC")
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    return items

@app.post("/api/admin/character/{char_id}/approve")
async def approve_character(char_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ?", (user['id'],))
    if not c.fetchone():
        raise HTTPException(status_code=403)
    
    c.execute("UPDATE characters SET status = 'approved' WHERE id = ?", (char_id,))
    c.execute("SELECT telegram_id FROM characters WHERE id = ?", (char_id,))
    row = c.fetchone()
    conn.commit()
    conn.close()
    return {"status": "approved", "telegram_id": row['telegram_id'] if row else None}

@app.post("/api/admin/character/{char_id}/reject")
async def reject_character(char_id: int, reason: str = Form(...),
                           user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ?", (user['id'],))
    if not c.fetchone():
        raise HTTPException(status_code=403)
    
    c.execute("UPDATE characters SET status = 'rejected', reject_reason = ? WHERE id = ?",
              (reason, char_id))
    c.execute("SELECT telegram_id FROM characters WHERE id = ?", (char_id,))
    row = c.fetchone()
    conn.commit()
    conn.close()
    return {"status": "rejected", "telegram_id": row['telegram_id'] if row else None, "reason": reason}

@app.get("/api/admin/reports")
async def admin_reports(user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ?", (user['id'],))
    if not c.fetchone():
        raise HTTPException(status_code=403)
    
    c.execute("SELECT * FROM reports WHERE status = 'pending' ORDER BY created_at DESC")
    items = [dict(row) for row in c.fetchall()]
    conn.close()
    return items

@app.post("/api/admin/report/{report_id}/approve")
async def approve_report(report_id: int, user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ?", (user['id'],))
    if not c.fetchone():
        raise HTTPException(status_code=403)
    
    c.execute("UPDATE reports SET status = 'approved' WHERE id = ?", (report_id,))
    conn.commit()
    conn.close()
    return {"status": "approved"}

@app.post("/api/admin/report/{report_id}/reject")
async def reject_report(report_id: int, reason: str = Form(...),
                        user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ?", (user['id'],))
    if not c.fetchone():
        raise HTTPException(status_code=403)
    
    c.execute("UPDATE reports SET status = 'rejected', reject_reason = ? WHERE id = ?",
              (reason, report_id))
    conn.commit()
    conn.close()
    return {"status": "rejected"}

@app.get("/api/admin/stats")
async def admin_stats(user: dict = Depends(get_current_user)):
    conn = get_connection()
    c = conn.cursor()
    c.execute("SELECT role FROM admins WHERE telegram_id = ?", (user['id'],))
    if not c.fetchone():
        raise HTTPException(status_code=403)
    
    stats = {
        "users": c.execute("SELECT COUNT(*) FROM users").fetchone()[0],
        "characters_pending": c.execute("SELECT COUNT(*) FROM characters WHERE status='pending'").fetchone()[0],
        "characters_approved": c.execute("SELECT COUNT(*) FROM characters WHERE status='approved'").fetchone()[0],
        "posts": c.execute("SELECT COUNT(*) FROM posts").fetchone()[0],
        "reports_pending": c.execute("SELECT COUNT(*) FROM reports WHERE status='pending'").fetchone()[0],
        "reports_approved": c.execute("SELECT COUNT(*) FROM reports WHERE status='approved'").fetchone()[0],
        "market_items": c.execute("SELECT COUNT(*) FROM market").fetchone()[0],
        "admins": c.execute("SELECT COUNT(*) FROM admins").fetchone()[0]
    }
    conn.close()
    return stats
