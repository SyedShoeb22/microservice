import os, datetime
from flask import Flask, request, jsonify
from sqlalchemy import Column, Integer, String, Float, DateTime, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.getenv("DB_PATH", "./order.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
Base = declarative_base()

class Order(Base):
    __tablename__ = "orders"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, nullable=False)
    items = Column(String(200), nullable=False)   # simple CSV JSON-ish store
    total = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

Base.metadata.create_all(engine)

app = Flask(__name__)

@app.post("/api/orders")
def create_order():
    data = request.get_json(force=True)
    user_id = data.get("user_id")
    items = data.get("items", [])
    if not user_id or not items:
        return jsonify(error="user_id and items required"), 400
    # compute price passed in payload? better ask product-service normally; for demo, 1 item = fetch price?: keep simple
    total = 0.0
    for it in items:
        # expecting {product_id, qty, price?}; demo: fixed qty=1 & mock price 10 if not present
        qty = it.get("qty", 1)
        price = float(it.get("price", 10.0))
        total += qty * price

    import json
    with SessionLocal() as db:
        o = Order(user_id=user_id, items=json.dumps(items), total=total)
        db.add(o); db.commit(); db.refresh(o)
        return jsonify(id=o.id, user_id=o.user_id, total=o.total, created_at=o.created_at.isoformat()), 201

@app.get("/api/orders/<int:user_id>")
def list_orders(user_id: int):
    with SessionLocal() as db:
        rows = db.execute(select(Order).where(Order.user_id == user_id)).scalars().all()
        return jsonify([{"id":o.id,"total":o.total,"created_at":o.created_at.isoformat()} for o in rows])

@app.get("/health")
def health():
    return {"status":"ok"}

if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_RUN_HOST","0.0.0.0"), port=5003)
