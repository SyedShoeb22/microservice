import os
from flask import Flask, jsonify
from sqlalchemy import Column, Integer, String, Float, create_engine, select
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = os.getenv("DB_PATH", "./product.db")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(f"sqlite:///{DB_PATH}", echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False, future=True)
Base = declarative_base()

class Product(Base):
    __tablename__ = "products"
    id = Column(Integer, primary_key=True)
    name = Column(String(120), nullable=False)
    description = Column(String(255), nullable=False)
    price = Column(Float, nullable=False)

Base.metadata.create_all(engine)

# seed data
with SessionLocal() as db:
    if not db.scalar(select(Product).limit(1)):
        db.add_all([
            Product(name="Coffee Mug", description="Ceramic mug 350ml", price=9.99),
            Product(name="Notebook", description="A5 dotted notebook", price=6.49),
            Product(name="T-Shirt", description="100% cotton, black", price=14.99),
        ])
        db.commit()

app = Flask(__name__)

@app.get("/api/products")
def list_products():
    with SessionLocal() as db:
        items = db.execute(select(Product)).scalars().all()
        return jsonify([{"id":p.id,"name":p.name,"description":p.description,"price":p.price} for p in items])

@app.get("/health")
def health():
    return {"status":"ok"}

if __name__ == "__main__":
    app.run(host=os.getenv("FLASK_RUN_HOST","0.0.0.0"), port=5002)
