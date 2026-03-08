from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_admin, get_db
from app.models.category import Category
from app.models.order import Order
from app.models.product import Product
from app.models.user import User
from app.schemas.admin import AdminUserRead
from app.schemas.category import CategoryCreate, CategoryRead
from app.schemas.order import OrderRead
from app.schemas.product import ProductCreate, ProductRead

router = APIRouter()


@router.post("/categories", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
def create_category(
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    existing = db.scalar(select(Category).where(Category.slug == payload.slug))
    if existing:
        raise HTTPException(status_code=400, detail="Category slug already exists")
    category = Category(**payload.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    product = Product(**payload.model_dump())
    db.add(product)
    db.commit()
    db.refresh(product)
    return db.scalar(
        select(Product).where(Product.id == product.id).options(joinedload(Product.category))
    )


@router.put("/products/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int,
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    for key, value in payload.model_dump().items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return db.scalar(
        select(Product).where(Product.id == product.id).options(joinedload(Product.category))
    )


@router.get("/orders", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    stmt = select(Order).options(joinedload(Order.items)).order_by(Order.created_at.desc())
    return db.scalars(stmt).unique().all()


@router.get("/users", response_model=list[AdminUserRead])
def list_users(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    stmt = (
        select(User)
        .options(joinedload(User.orders))
        .order_by(User.created_at.desc())
    )
    users = db.scalars(stmt).unique().all()
    results: list[AdminUserRead] = []
    for user in users:
        order_totals = [float(order.total_price) for order in user.orders]
        last_order_at = max((order.created_at for order in user.orders), default=None)
        results.append(
            AdminUserRead(
                id=user.id,
                phone=user.phone,
                email=user.email,
                is_admin=user.is_admin,
                created_at=user.created_at,
                orders_count=len(user.orders),
                total_spent=round(sum(order_totals), 2),
                last_order_at=last_order_at,
            )
        )
    return results
