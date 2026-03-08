from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_db
from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryRead
from app.schemas.product import ProductRead

router = APIRouter()


@router.get("/categories", response_model=list[CategoryRead])
def list_categories(db: Session = Depends(get_db)):
    stmt = select(Category).order_by(Category.created_at.desc())
    return db.scalars(stmt).all()


@router.get("/products", response_model=list[ProductRead])
def list_products(
    category_id: int | None = Query(default=None),
    q: str | None = Query(default=None, min_length=1),
    db: Session = Depends(get_db),
):
    stmt = select(Product).options(joinedload(Product.category)).order_by(Product.created_at.desc())
    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)
    if q:
        query = f"%{q.lower()}%"
        stmt = stmt.where(
            Product.name_uz.ilike(query)
            | Product.name_en.ilike(query)
            | Product.name_ru.ilike(query)
            | Product.description_uz.ilike(query)
            | Product.description_en.ilike(query)
            | Product.description_ru.ilike(query)
        )
    return db.scalars(stmt).unique().all()


@router.get("/products/{product_id}", response_model=ProductRead)
def product_detail(product_id: int, db: Session = Depends(get_db)):
    product = db.scalar(
        select(Product).where(Product.id == product_id).options(joinedload(Product.category))
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product
