from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from typing import Optional, Literal, List
# import math
import os
import httpx

# Config
SECRET_KEY = os.getenv("JWT_SECRET", "change_me_in_prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
SCORE_AGENT_URL = os.getenv("SCORE_AGENT_URL", "http://localhost:8001/score")

# Allow local dev frontends
origins_env = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:3000")
CORS_ORIGINS = [o.strip() for o in origins_env.split(",") if o.strip()]

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Test user store – replace with DB 
fake_users_db = {
    "member1": {
        "username": "member1",
        "full_name": "Loan Officer",
        "hashed_password": pwd_context.hash("password123"),
    }
}

# App
app = FastAPI(title="Applicant Evaluator Agent", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Auth models
class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    username: Optional[str] = None

class User(BaseModel):
    username: str
    full_name: Optional[str] = None

class UserInDB(User):
    hashed_password: str

class LoginRequest(BaseModel):
    username: str
    password: str

# Auth helpers
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_user(db, username: str) -> Optional[UserInDB]:
    if username in db:
        data = db[username].copy()
        return UserInDB(**data)

def authenticate_user(username: str, password: str):
    user = get_user(fake_users_db, username)
    if not user or not verify_password(password, user.hashed_password):
        return None
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    cred_exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise cred_exc
    except JWTError:
        raise cred_exc
    user = get_user(fake_users_db, username=username)
    if user is None:
        raise cred_exc
    return User(username=user.username, full_name=user.full_name)

# Domain models
# Must change according to dataset
EmploymentType = Literal["FULL_TIME", "PART_TIME", "SELF_EMPLOYED", "GOVERNMENT", "STUDENT", "RETIRED"]

class Applicant(BaseModel):
    name: str = Field(..., min_length=2, max_length=80)
    age: int = Field(..., ge=18, le=70)
    income: float = Field(..., gt=0, description="Net monthly income")
    expenses: float = Field(..., ge=0, description="Monthly fixed expenses")
    loan_amount: float = Field(..., gt=0)
    tenure_months: int = Field(..., ge=6, le=84)
    employment_type: EmploymentType
    past_defaults: int = Field(0, ge=0, le=10)
    card_utilization: float = Field(0.0, ge=0.0, le=1.0)
    inquiries_last6m: int = Field(0, ge=0, le=20)
    interest_rate_annual: float = Field(18.0, gt=0, lt=100, description="Annual %")

    @field_validator("expenses")
    @classmethod
    def expenses_not_exceed_income(cls, v, info):
        income = info.data.get("income")
        if income is not None and v >= income:
            raise ValueError("Expenses must be less than income")
        return v

class EvaluateResponse(BaseModel):
    valid: bool
    message: Optional[str] = None
    features: Optional[dict] = None
    score: Optional[int] = None
    band: Optional[str] = None
    factors: Optional[List[str]] = None

# Utilities
def monthly_emi(principal: float, annual_rate_percent: float, months: int) -> float:
    r = (annual_rate_percent / 100.0) / 12.0
    if r == 0:
        return principal / months
    num = principal * r * (1 + r) ** months
    den = (1 + r) ** months - 1
    return num / den

def clamp(val, lo, hi):
    return max(lo, min(hi, val))

def band_for(score: int) -> str:
    if score >= 720: return "A"
    if score >= 660: return "B"
    if score >= 600: return "C"
    return "D"

# Endpoints
@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/login", response_model=Token)
def login(form_data: LoginRequest):
    user = authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token({"sub": form_data.username}, timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    return Token(access_token=token)

@app.post("/evaluate", response_model=EvaluateResponse)
async def evaluate(applicant: Applicant, user: User = Depends(get_current_user)):
    """
    1) Validate + engineer features
    2) Try Score Agent; if unavailable, compute local rule-based score
    """
    emi = monthly_emi(applicant.loan_amount, applicant.interest_rate_annual, applicant.tenure_months)
    net_income = applicant.income - applicant.expenses
    dti = emi / applicant.income
    burden = emi / max(1.0, net_income)

    if dti > 0.8:
        return EvaluateResponse(valid=False, message="EMI to income ratio is too high.")

    # Have to change this according to dataset
    features = {
        "age": applicant.age,
        "income": applicant.income,
        "expenses": applicant.expenses,
        "net_income": round(net_income, 2),
        "loan_amount": applicant.loan_amount,
        "tenure_months": applicant.tenure_months,
        "employment_type": applicant.employment_type,
        "emi": round(emi, 2),
        "dti": round(dti, 3),
        "burden": round(burden, 3),
        "past_defaults": applicant.past_defaults,
        "card_utilization": applicant.card_utilization,
        "inquiries_last6m": applicant.inquiries_last6m,
    }

    score: Optional[int] = None
    band: Optional[str] = None
    factors: List[str] = []

    # External Score Agent
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.post(SCORE_AGENT_URL, json=features)
        if resp.status_code == 200:
            data = resp.json()
            score = int(data.get("score"))
            band = str(data.get("band"))
            factors = list(data.get("factors", []))
    except Exception:
        pass  # fall back

    # Local rule-based fallback
    if score is None:
        s = 700
        if dti <= 0.30:
            s += 60; factors.append("LOW_DTI")
        elif dti <= 0.40:
            s += 20; factors.append("MODERATE_DTI")
        else:
            s -= 80; factors.append("HIGH_DTI")

        if applicant.past_defaults > 0:
            s -= 120 * applicant.past_defaults; factors.append("PAST_DEFAULTS")

        if applicant.card_utilization > 0.8:
            s -= 60; factors.append("HIGH_UTILIZATION")
        elif applicant.card_utilization > 0.5:
            s -= 20; factors.append("MID_UTILIZATION")

        if applicant.inquiries_last6m > 0:
            s -= 15 * applicant.inquiries_last6m; factors.append("RECENT_INQUIRIES")

        score = clamp(int(round(s)), 300, 850)
        band = band_for(score)

    return EvaluateResponse(valid=True, features=features, score=score, band=band, factors=factors)
