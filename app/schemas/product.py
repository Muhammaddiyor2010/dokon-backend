from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.schemas.category import CategoryRead


class ProductBase(BaseModel):
    category_id: int
    name_uz: str = Field(min_length=2, max_length=150)
    name_en: str = Field(min_length=2, max_length=150)
    name_ru: str = Field(min_length=2, max_length=150)
    description_uz: str = Field(min_length=3)
    description_en: str = Field(min_length=3)
    description_ru: str = Field(min_length=3)
    price: float = Field(gt=0)
    image_url: str | None = Field(default=None, min_length=5, max_length=500)
    image_urls: list[str] = Field(default_factory=list, max_length=10)
    stock: int = Field(ge=0)

    @field_validator("image_urls")
    @classmethod
    def validate_image_urls(cls, value: list[str]) -> list[str]:
        cleaned = [url.strip() for url in value if url.strip()]
        if len(cleaned) > 10:
            raise ValueError("Maksimum 10 ta rasm qo'shish mumkin")
        for url in cleaned:
            if len(url) < 5 or len(url) > 500:
                raise ValueError("Har bir rasm URL 5-500 oralig'ida bo'lishi kerak")
        return cleaned

    @model_validator(mode="after")
    def validate_primary_image(self) -> "ProductBase":
        if not self.image_url and not self.image_urls:
            raise ValueError("Kamida 1 ta rasm URL kiritilishi kerak")
        return self


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int
    image_url: str
    created_at: datetime
    category: CategoryRead

    model_config = ConfigDict(from_attributes=True)


class ProductEngagementRead(BaseModel):
    likes_count: int
    comments_count: int
    liked_by_me: bool


class ProductCommentUserRead(BaseModel):
    id: int
    phone: str

    model_config = ConfigDict(from_attributes=True)


class ProductCommentCreate(BaseModel):
    content: str = Field(min_length=2, max_length=1000)


class ProductCommentRead(BaseModel):
    id: int
    product_id: int
    user_id: int
    content: str
    created_at: datetime
    user: ProductCommentUserRead

    model_config = ConfigDict(from_attributes=True)
