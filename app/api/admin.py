from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_admin, get_db
from app.models.category import Category
from app.models.order import Order, OrderItem
from app.models.product import Product, ProductImage
from app.models.user import User
from app.schemas.admin import AdminUserRead
from app.schemas.category import CategoryCreate, CategoryRead
from app.schemas.order import OrderRead, OrderStatusUpdate
from app.schemas.product import ProductCreate, ProductRead

router = APIRouter()


def _resolve_image_urls(payload: ProductCreate) -> list[str]:
    urls = payload.image_urls.copy()
    if payload.image_url and payload.image_url not in urls:
        urls.insert(0, payload.image_url.strip())
    if not urls:
        raise HTTPException(status_code=400, detail="At least one image URL is required")
    return urls[:10]


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


@router.put("/categories/{category_id}", response_model=CategoryRead)
def update_category(
    category_id: int,
    payload: CategoryCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    existing = db.scalar(
        select(Category).where(Category.slug == payload.slug, Category.id != category_id)
    )
    if existing:
        raise HTTPException(status_code=400, detail="Category slug already exists")

    for key, value in payload.model_dump().items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    return category


@router.delete("/categories/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category = db.get(Category, category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    has_products = (
        db.scalar(select(Product.id).where(Product.category_id == category_id).limit(1)) is not None
    )
    if has_products:
        raise HTTPException(
            status_code=400,
            detail="Category has products. Delete or move products first.",
        )

    db.delete(category)
    db.commit()


@router.post("/products", response_model=ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    category = db.get(Category, payload.category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Category not found")

    image_urls = _resolve_image_urls(payload)
    payload_data = payload.model_dump(exclude={"image_urls"})
    payload_data["image_url"] = image_urls[0]

    product = Product(**payload_data)
    db.add(product)
    db.flush()
    for index, image_url in enumerate(image_urls):
        db.add(ProductImage(product_id=product.id, url=image_url, sort_order=index))
    db.commit()
    db.refresh(product)
    return db.scalar(
        select(Product)
        .where(Product.id == product.id)
        .options(joinedload(Product.category), joinedload(Product.images))
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

    image_urls = _resolve_image_urls(payload)
    payload_data = payload.model_dump(exclude={"image_urls"})
    payload_data["image_url"] = image_urls[0]

    for key, value in payload_data.items():
        setattr(product, key, value)

    product.images.clear()
    for index, image_url in enumerate(image_urls):
        product.images.append(ProductImage(url=image_url, sort_order=index))

    db.commit()
    db.refresh(product)
    return db.scalar(
        select(Product)
        .where(Product.id == product.id)
        .options(joinedload(Product.category), joinedload(Product.images))
    )


@router.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(
    product_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    product = db.get(Product, product_id)
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    has_orders = (
        db.scalar(select(OrderItem.id).where(OrderItem.product_id == product_id).limit(1)) is not None
    )
    if has_orders:
        raise HTTPException(
            status_code=400,
            detail="Product already exists in orders and cannot be deleted.",
        )

    db.delete(product)
    db.commit()


@router.get("/orders", response_model=list[OrderRead])
def list_orders(db: Session = Depends(get_db), _admin=Depends(get_current_admin)):
    stmt = select(Order).options(joinedload(Order.items)).order_by(Order.created_at.desc())
    return db.scalars(stmt).unique().all()


@router.patch("/orders/{order_id}/status", response_model=OrderRead)
def update_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _admin=Depends(get_current_admin),
):
    order = db.scalar(select(Order).where(Order.id == order_id).options(joinedload(Order.items)))
    if order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    order.status = payload.status
    db.commit()
    db.refresh(order)
    return order


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
