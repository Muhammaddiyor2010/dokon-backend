from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, get_db, get_optional_user
from app.models.category import Category
from app.models.product import Product, ProductComment, ProductLike
from app.models.user import User
from app.schemas.category import CategoryRead
from app.schemas.product import (
    ProductCommentCreate,
    ProductCommentRead,
    ProductEngagementRead,
    ProductRead,
)

router = APIRouter()


def _get_product_or_404(product_id: int, db: Session) -> Product:
    product = db.scalar(
        select(Product)
        .where(Product.id == product_id)
        .options(joinedload(Product.category), joinedload(Product.images))
    )
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


def _build_engagement(product_id: int, db: Session, current_user: User | None) -> ProductEngagementRead:
    likes_count = db.scalar(select(func.count(ProductLike.id)).where(ProductLike.product_id == product_id)) or 0
    comments_count = db.scalar(
        select(func.count(ProductComment.id)).where(ProductComment.product_id == product_id)
    ) or 0
    liked_by_me = False
    if current_user:
        liked_by_me = (
            db.scalar(
                select(ProductLike.id).where(
                    ProductLike.product_id == product_id,
                    ProductLike.user_id == current_user.id,
                )
            )
            is not None
        )
    return ProductEngagementRead(
        likes_count=int(likes_count),
        comments_count=int(comments_count),
        liked_by_me=liked_by_me,
    )


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
    stmt = (
        select(Product)
        .options(joinedload(Product.category), joinedload(Product.images))
        .order_by(Product.created_at.desc())
    )
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
    return _get_product_or_404(product_id, db)


@router.get("/products/{product_id}/engagement", response_model=ProductEngagementRead)
def product_engagement(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_optional_user),
):
    _get_product_or_404(product_id, db)
    return _build_engagement(product_id, db, current_user)


@router.post("/products/{product_id}/likes/toggle", response_model=ProductEngagementRead)
def toggle_like(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_product_or_404(product_id, db)

    existing_like = db.scalar(
        select(ProductLike).where(
            ProductLike.product_id == product_id,
            ProductLike.user_id == current_user.id,
        )
    )
    if existing_like is None:
        db.add(ProductLike(product_id=product_id, user_id=current_user.id))
    else:
        db.delete(existing_like)

    db.commit()
    return _build_engagement(product_id, db, current_user)


@router.get("/products/{product_id}/comments", response_model=list[ProductCommentRead])
def list_product_comments(product_id: int, db: Session = Depends(get_db)):
    _get_product_or_404(product_id, db)
    stmt = (
        select(ProductComment)
        .where(ProductComment.product_id == product_id)
        .options(joinedload(ProductComment.user))
        .order_by(ProductComment.created_at.desc())
    )
    return db.scalars(stmt).unique().all()


@router.post(
    "/products/{product_id}/comments",
    response_model=ProductCommentRead,
    status_code=status.HTTP_201_CREATED,
)
def create_product_comment(
    product_id: int,
    payload: ProductCommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_product_or_404(product_id, db)

    comment = ProductComment(
        product_id=product_id,
        user_id=current_user.id,
        content=payload.content.strip(),
    )
    db.add(comment)
    db.commit()
    return db.scalar(
        select(ProductComment)
        .where(ProductComment.id == comment.id)
        .options(joinedload(ProductComment.user))
    )
