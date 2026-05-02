from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import google.generativeai as genai
from typing import List, Optional
import os
import random

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./expenses.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Expense(Base):
    __tablename__ = "expenses"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    cost = Column(Float)
    gst_percentage = Column(Float)
    category = Column(String)  # 'Subscription', 'Rent', 'Utility', etc.
    billing_cycle = Column(String, default='Monthly')

Base.metadata.create_all(bind=engine)

# Pydantic Models
class ExpenseBase(BaseModel):
    name: str
    cost: float
    gst_percentage: float
    category: str
    billing_cycle: str = "Monthly"

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    model_config = {"from_attributes": True}

class AIChatRequest(BaseModel):
    message: str

class AIChatResponse(BaseModel):
    reply: str

class DiscountResponse(BaseModel):
    platform: str
    item_name: str
    original_price: float
    discounted_price: float
    discount_percentage: int
    delivery_time: str
    badge_color: str
    currency_symbol: str
    currency: str

class IngredientsRequest(BaseModel):
    product_name: str
    ingredients: str
    base_cost: float
    gst: float
    shipping: float
    quantity: float
    unit: str

class IngredientsResponse(BaseModel):
    analysis: str

# FastAPI App
app = FastAPI(title="AI Manager & Grocery Discounts API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/api/expenses", response_model=ExpenseResponse)
def create_expense(expense: ExpenseCreate, db: Session = Depends(get_db)):
    db_expense = Expense(**expense.model_dump())
    db.add(db_expense)
    db.commit()
    db.refresh(db_expense)
    return db_expense

@app.get("/api/expenses", response_model=List[ExpenseResponse])
def read_expenses(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    expenses = db.query(Expense).offset(skip).limit(limit).all()
    return expenses

@app.delete("/api/expenses/{expense_id}")
def delete_expense(expense_id: int, db: Session = Depends(get_db)):
    db_expense = db.query(Expense).filter(Expense.id == expense_id).first()
    if not db_expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    db.delete(db_expense)
    db.commit()
    return {"message": "Expense deleted successfully"}

@app.post("/api/chat", response_model=AIChatResponse)
def chat_with_ai(request: AIChatRequest, db: Session = Depends(get_db)):
    try:
        # USER: Put your API key below!
        api_key = "AIzaSyBWINXh7y1nXAthFXSMXZeHJwRqPPzwccA"
        
        if api_key == "YOUR_API_KEY_HERE":
            # Fallback to environment variable if they haven't filled it in yet, just in case
            api_key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # Get user context
        expenses = db.query(Expense).all()
        context = "Here are my current expenses and subscriptions:\n"
        if not expenses:
            context += "None yet.\n"
        for exp in expenses:
            context += f"- {exp.name} ({exp.category}): ${exp.cost} with {exp.gst_percentage}% GST.\n"
            
        system_prompt = f"""You are a helpful AI financial assistant. 
        The user wants to manage their subscriptions, rent, and other expenses.
        Use their financial context to answer their question. Keep it concise, helpful, and friendly.
        
        Context:
        {context}
        """
        
        response = model.generate_content(system_prompt + "\nUser Question: " + request.message)
        return {"reply": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/grocery/discounts", response_model=List[DiscountResponse])
async def get_grocery_discounts(item: str, currency: str = "INR"):
    from scrapers import perform_live_search
    # Defaulting location to 500001 as requested
    results = await perform_live_search(item, pincode="500001", currency=currency)
    return results

@app.post("/api/analyze-product", response_model=IngredientsResponse)
def analyze_product(request: IngredientsRequest):
    try:
        api_key = "AIzaSyBWINXh7y1nXAthFXSMXZeHJwRqPPzwccA"
        if api_key == "YOUR_API_KEY_HERE":
            api_key = os.environ.get("GEMINI_API_KEY", "YOUR_API_KEY_HERE")
            
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        system_prompt = """You are a health and financial expert assistant.
        The user will provide a product name, its ingredients/materials, base cost, GST tax %, shipping fees, and net quantity.
        
        Your job is to do TWO things:
        1. FINANCIAL BREAKDOWN: Calculate the True Landed Cost (Base Cost + (Base Cost * GST%) + Shipping) and the Price Per Unit (e.g., price per 100g, or price per 1 piece based on the quantity). Show the math clearly.
        2. HEALTH ANALYSIS: If the product is clearly NOT edible (e.g., electronics like an iPhone, furniture), playfully tell them it's not edible and skip the health analysis! (e.g. "iPhones aren't edible! 😂🤣"). If it IS edible, briefly analyze the ingredients for healthiness (hidden sugars, harmful additives, or good nutrition).
        
        Format your response cleanly. Keep it friendly and concise.
        """
        
        prompt = f"Product Name: {request.product_name}\nIngredients: {request.ingredients}\nBase Cost: {request.base_cost}\nGST: {request.gst}%\nShipping: {request.shipping}\nQuantity: {request.quantity} {request.unit}"
        response = model.generate_content(system_prompt + "\n\n" + prompt)
        
        return {"analysis": response.text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
