"""
Authentication routes
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
import logging

from database import get_db
from database.models import User
from .schemas import (
    UserRegister, UserLogin, Token, UserResponse, MessageResponse,
    UserProfileUpdate, UserProfileResponse
)
from .utils import hash_password, verify_password, create_access_token, get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **email**: User email address (must be unique)
    - **password**: User password (min 8 characters, must contain letters and digits)
    
    Returns success message on successful registration
    """
    logger.info(f"Registration attempt for email: {user_data.email}")
    
    # Check if user already exists
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        logger.warning(f"Registration failed: User with email {user_data.email} already exists")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    
    # Create new user
    try:
        hashed_pwd = hash_password(user_data.password)
        new_user = User(
            email=user_data.email,
            hashed_password=hashed_pwd
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)
        
        logger.info(f"User registered successfully: {new_user.email} (ID: {new_user.id})")
        
        return MessageResponse(
            status="success",
            message="User registered successfully"
        )
    
    except IntegrityError as e:
        db.rollback()
        logger.error(f"Database integrity error during registration: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User with this email already exists"
        )
    except Exception as e:
        db.rollback()
        logger.error(f"Unexpected error during registration: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"An error occurred during registration: {str(e)}"
        )


@router.post("/login", response_model=Token)
async def login(user_data: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT token
    
    - **email**: User email address
    - **password**: User password
    
    Returns JWT access token on successful authentication
    """
    logger.info(f"Login attempt for email: {user_data.email}")
    
    # Find user by email
    user = db.query(User).filter(User.email == user_data.email).first()
    
    # Verify user exists and password is correct
    if not user or not verify_password(user_data.password, user.hashed_password):
        logger.warning(f"Login failed for email: {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = create_access_token(data={"user_id": user.id, "email": user.email})
    
    logger.info(f"Login successful for user: {user.email} (ID: {user.id})")
    
    return Token(
        status="success",
        message="Login successful",
        access_token=access_token,
        token_type="bearer"
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Get current authenticated user information
    
    Requires valid JWT token in Authorization header
    
    Returns current user data
    """
    logger.info(f"User info requested for: {current_user.email} (ID: {current_user.id})")
    
    return UserResponse(
        status="success",
        id=current_user.id,
        email=current_user.email,
        created_at=current_user.created_at
    )


@router.get("/me/profile", response_model=UserProfileResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    """
    Get full user profile with all details
    
    Requires valid JWT token in Authorization header
    
    Returns complete user profile including personal and farm information
    """
    logger.info(f"Profile requested for user: {current_user.email} (ID: {current_user.id})")
    
    return UserProfileResponse(
        id=current_user.id,
        email=current_user.email,
        full_name=current_user.full_name,
        farm_name=current_user.farm_name,
        country=current_user.country,
        region=current_user.region,
        phone_number=current_user.phone_number,
        preferred_units=current_user.preferred_units,
        primary_crops=current_user.primary_crops,
        farming_type=current_user.farming_type,
        irrigation_method=current_user.irrigation_method,
        created_at=current_user.created_at
    )


@router.put("/me/profile", response_model=UserProfileResponse)
async def update_user_profile(
    profile_data: UserProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    
    Requires valid JWT token in Authorization header
    
    Allows updating personal and farm-related information
    """
    logger.info(f"Profile update requested for user: {current_user.email} (ID: {current_user.id})")
    
    try:
        # Update only provided fields
        update_data = profile_data.model_dump(exclude_unset=True)
        
        for field, value in update_data.items():
            setattr(current_user, field, value)
        
        db.commit()
        db.refresh(current_user)
        
        logger.info(f"Profile successfully updated for user: {current_user.email}")
        
        return UserProfileResponse(
            id=current_user.id,
            email=current_user.email,
            full_name=current_user.full_name,
            farm_name=current_user.farm_name,
            country=current_user.country,
            region=current_user.region,
            phone_number=current_user.phone_number,
            preferred_units=current_user.preferred_units,
            primary_crops=current_user.primary_crops,
            farming_type=current_user.farming_type,
            irrigation_method=current_user.irrigation_method,
            created_at=current_user.created_at
        )
    
    except Exception as e:
        db.rollback()
        logger.error(f"Failed to update profile for user {current_user.email}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

