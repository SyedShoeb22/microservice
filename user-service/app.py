import os
from flask import Flask, request, jsonify
from sqlalchemy import Column, Integer, String, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker
from passlib.hash import bcrypt

DB_PATH = os.getenv("DB_PATH", "./user.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False)
    email = Column(String(128), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)

Base.metadata.create_all(engine)

app = Flask(__name__)

@app.post("/api/user/register")
def register():
    data = request.get_json(force=True)
    username = data.get("username","").strip()
    email = data.get("email","").strip()
    password = data.get("password","")
    if not (username and email and password):
        return jsonify(error="Missing fields"), 400

    with SessionLocal() as db:
        if db.scalar(select(User).where(User.username == username)):
            return jsonify(error="Username already exists"), 409
        if db.scalar(select(User).where(User.email == email)):
            return jsonify(error="Email already exists"), 409
        u = User(username=username, email=email, password_hash=bcrypt.hash(password))
        db.add(u); db.commit(); db.refresh(u)
        return jsonify(id=u.id, username=u.username, email=u.email), 201

@app.post("/api/user/login")
def login():
    data = request.get_json(force=True)
    username = data.get("username","").strip()
    password = data.get("password","")
    with SessionLocal() as db:
        u = db.scalar(select(User).where(User.username == username))
        if not u or not bcrypt.verify(password, u.password_hash):
            return jsonify(error="Invalid credentials"), 401
        return jsonify(id=u.id, username=u.username)

@app.get("/api/user/<username>/exists")
def exists(username):
    with SessionLocal() as db:
        present = db.scalar(select(User).where(User.username == username)) is not None
        return ("", 200) if present else ("", 404)

@app.get("/health")
def health():
    return {"status":"ok"}

if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_RUN_HOST","0.0.0.0"), port=5001)
