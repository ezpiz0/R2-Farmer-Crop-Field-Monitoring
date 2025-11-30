"""
Pydantic schemas for authentication and user profile
"""

from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional, List
from datetime import datetime
from enum import Enum


class PreferredUnits(str, Enum):
    """Enum for preferred measurement units"""
    HECTARES = "hectares"
    ACRES = "acres"


class FarmingType(str, Enum):
    """Enum for farming type"""
    CONVENTIONAL = "conventional"
    ORGANIC = "organic"
    MIXED = "mixed"


class IrrigationMethod(str, Enum):
    """Enum for irrigation method"""
    RAINFED = "rainfed"
    IRRIGATED = "irrigated"
    MIXED = "mixed"


class UserRegister(BaseModel):
    """
    Schema for user registration
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, max_length=72, description="User password (6-72 characters)")
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v):
        if len(v) < 6:
            raise ValueError('Password must be at least 6 characters long')
        if len(v.encode('utf-8')) > 72:
            raise ValueError('Password is too long (max 72 bytes)')
        return v


class UserLogin(BaseModel):
    """
    Schema for user login
    """
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """
    Schema for JWT token response
    """
    status: str = "success"
    message: str = "Login successful"
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    """
    Schema for user data response
    """
    status: str = "success"
    id: int
    email: str
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class MessageResponse(BaseModel):
    """
    Schema for generic message responses
    """
    status: str
    message: str


class UserProfileUpdate(BaseModel):
    """
    Schema for updating user profile
    """
    full_name: Optional[str] = Field(None, max_length=255, description="Полное имя пользователя")
    farm_name: Optional[str] = Field(None, max_length=255, description="Название фермы/хозяйства")
    country: Optional[str] = Field(None, max_length=100, description="Страна")
    region: Optional[str] = Field(None, max_length=255, description="Регион/область")
    phone_number: Optional[str] = Field(None, max_length=20, description="Номер телефона")
    preferred_units: Optional[PreferredUnits] = Field(None, description="Предпочитаемые единицы измерения")
    primary_crops: Optional[List[str]] = Field(None, description="Основные культуры", max_length=20)
    farming_type: Optional[FarmingType] = Field(None, description="Тип земледелия")
    irrigation_method: Optional[IrrigationMethod] = Field(None, description="Метод орошения")
    
    @field_validator('phone_number')
    @classmethod
    def validate_phone(cls, v):
        if v is None:
            return v
        # Basic phone validation
        clean = ''.join(filter(str.isdigit, v))
        if len(clean) < 10:
            raise ValueError('Номер телефона должен содержать минимум 10 цифр')
        return v
    
    @field_validator('primary_crops')
    @classmethod
    def validate_crops(cls, v):
        if v is None:
            return v
        if len(v) > 20:
            raise ValueError('Максимум 20 культур')
        return v


class UserProfileResponse(BaseModel):
    """
    Schema for user profile response
    """
    id: int
    email: str
    full_name: Optional[str] = None
    farm_name: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    phone_number: Optional[str] = None
    preferred_units: str = "hectares"
    primary_crops: Optional[List[str]] = None
    farming_type: Optional[str] = None
    irrigation_method: Optional[str] = None
    created_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True

