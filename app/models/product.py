from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    name_uz: Mapped[str] = mapped_column(String(150))
    name_en: Mapped[str] = mapped_column(String(150))
    name_ru: Mapped[str] = mapped_column(String(150))
    description_uz: Mapped[str] = mapped_column(Text)
    description_en: Mapped[str] = mapped_column(Text)
    description_ru: Mapped[str] = mapped_column(Text)
    price: Mapped[float] = mapped_column(Float)
    image_url: Mapped[str] = mapped_column(String(500))
    stock: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
