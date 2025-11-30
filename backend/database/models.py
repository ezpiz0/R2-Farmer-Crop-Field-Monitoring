"""
Database models
"""

from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from .database import Base


class User(Base):
    """
    User model for authentication and profile
    """
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Profile fields
    full_name = Column(String, nullable=True)
    farm_name = Column(String, nullable=True)
    country = Column(String, nullable=True)
    region = Column(String, nullable=True)
    phone_number = Column(String, nullable=True)
    preferred_units = Column(String, default="hectares", nullable=False)  # hectares, acres
    primary_crops = Column(JSON, nullable=True)  # ["wheat", "corn", "sunflower"]
    farming_type = Column(String, nullable=True)  # conventional, organic, mixed
    irrigation_method = Column(String, nullable=True)  # rainfed, irrigated, mixed
    
    # Relationships
    fields = relationship("Field", back_populates="user", cascade="all, delete-orphan")
    dashboard_items = relationship("DashboardItem", back_populates="user", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, name={self.full_name})>"


class Field(Base):
    """
    Field model for storing user's agricultural fields
    """
    __tablename__ = "fields"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String, nullable=False)
    geometry_geojson = Column(JSON, nullable=False)  # Store GeoJSON geometry
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="fields")
    dashboard_items = relationship("DashboardItem", back_populates="field", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Field(id={self.id}, name={self.name}, user_id={self.user_id})>"


class DashboardItem(Base):
    """
    Dashboard item model for storing saved analyses
    """
    __tablename__ = "dashboard_items"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    field_id = Column(Integer, ForeignKey("fields.id", ondelete="CASCADE"), nullable=False, index=True)
    item_type = Column(String, nullable=False)  # "time_series_chart", "latest_ndvi_map", "field_stats"
    start_date = Column(String, nullable=True)  # For time series
    end_date = Column(String, nullable=True)  # For time series
    index_type = Column(String, nullable=True)  # "NDVI", "EVI", "PSRI", "NBR", "NDSI"
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    user = relationship("User", back_populates="dashboard_items")
    field = relationship("Field", back_populates="dashboard_items")

    def __repr__(self):
        return f"<DashboardItem(id={self.id}, type={self.item_type}, field_id={self.field_id})>"

