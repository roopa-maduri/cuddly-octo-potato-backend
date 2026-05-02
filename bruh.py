from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
import google.generativeai as genai
from typing import List, Optional
import os

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

Base.metadata.create_all(bind=engine)

# Pydantic Models
class ExpenseBase(BaseModel):
    name: str
    cost: float
    gst_percentage: float
    category: str

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseResponse(ExpenseBase):
    id: int
    model_config = {"from_attributes": True}

class AIChatRequest(BaseModel):
    message: str
    api_key: str

class AIChatResponse(BaseModel):
    reply: str

# FastAPI App
app = FastAPI(title="AI Subscription Manager API")

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
        genai.configure(api_key=request.api_key)
        model = genai.GenerativeModel('gemini-1.5-flash')
        
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
