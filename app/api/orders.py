from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.core.deps import get_current_user, get_db
from app.models.order import Order, OrderItem
from app.models.product import Product
from app.models.user import User
from app.schemas.order import CheckoutRequest, OrderRead

router = APIRouter()


@router.post("/checkout", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def checkout(
    payload: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not payload.items:
        raise HTTPException(status_code=400, detail="Order must contain at least one item")

    product_ids = [item.product_id for item in payload.items]
    products = db.scalars(select(Product).where(Product.id.in_(product_ids))).all()
    product_map = {product.id: product for product in products}

    if len(product_map) != len(set(product_ids)):
        raise HTTPException(status_code=400, detail="Some products were not found")

    total = 0.0
    order_items: list[OrderItem] = []
    for item in payload.items:
        product = product_map[item.product_id]
        if product.stock < item.quantity:
            raise HTTPException(
                status_code=400,
                detail=f"Not enough stock for product id={item.product_id}",
            )
        product.stock -= item.quantity
        line_total = product.price * item.quantity
        total += line_total
        order_items.append(OrderItem(product_id=product.id, quantity=item.quantity, price=product.price))

    order = Order(
        user_id=current_user.id,
        customer_name=payload.customer_name,
        customer_phone=payload.customer_phone,
        location=payload.location,
        total_price=round(total, 2),
    )
    db.add(order)
    db.flush()

    for line in order_items:
        line.order_id = order.id
        db.add(line)

    db.commit()
    db.refresh(order)

    return db.scalar(select(Order).where(Order.id == order.id).options(joinedload(Order.items)))


@router.get("/my", response_model=list[OrderRead])
def my_orders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    stmt = (
        select(Order)
        .where(Order.user_id == current_user.id)
        .options(joinedload(Order.items))
        .order_by(Order.created_at.desc())
    )
    return db.scalars(stmt).unique().all()
