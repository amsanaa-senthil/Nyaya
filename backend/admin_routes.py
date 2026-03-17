from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session
from backend.database import SessionLocal
from backend.models import Admin
from backend.admin_schemas import AdminLogin, AdminRegister, AdminResponse, AdminLoginResponse
from backend.admin_utils import hash_password, verify_password, create_token, decode_token
import jwt

router = APIRouter(prefix="/api/admin", tags=["admin"])
security = HTTPBearer()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_admin(credentials: HTTPAuthCredentials = Depends(security), db: Session = Depends(get_db)) -> Admin:
    """Extract and verify current admin from JWT token"""
    try:
        payload = decode_token(credentials.credentials)
        admin_id = payload.get("sub")
        if not admin_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        admin = db.query(Admin).filter(Admin.id == admin_id).first()
        if not admin or not admin.is_active:
            raise HTTPException(status_code=401, detail="Admin not found or inactive")
        return admin
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

@router.post("/register", response_model=AdminLoginResponse)
def register_admin(data: AdminRegister, db: Session = Depends(get_db)):
    """Register a new admin user"""
    if db.query(Admin).filter(Admin.email == data.email).first():
        raise HTTPException(status_code=400, detail="Email already registered")
    
    admin = Admin(
        email=data.email,
        password_hash=hash_password(data.password),
        full_name=data.full_name
    )
    db.add(admin)
    db.commit()
    db.refresh(admin)
    
    return {
        "id": admin.id,
        "email": admin.email,
        "full_name": admin.full_name,
        "token": create_token(admin.id)
    }

@router.post("/login", response_model=AdminLoginResponse)
def login_admin(data: AdminLogin, db: Session = Depends(get_db)):
    """Login admin user"""
    admin = db.query(Admin).filter(Admin.email == data.email).first()
    
    if not admin or not verify_password(data.password, admin.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    
    if not admin.is_active:
        raise HTTPException(status_code=403, detail="Admin account is disabled")
    
    return {
        "id": admin.id,
        "email": admin.email,
        "full_name": admin.full_name,
        "token": create_token(admin.id)
    }

@router.get("/me", response_model=AdminResponse)
def get_admin_profile(admin: Admin = Depends(get_current_admin)):
    """Get current admin profile"""
    return admin