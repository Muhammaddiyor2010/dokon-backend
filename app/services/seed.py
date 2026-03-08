from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import get_password_hash, verify_password
from app.models.category import Category
from app.models.product import Product
from app.models.user import User

settings = get_settings()


def _resolve_admin_email(db: Session, exclude_user_id: int | None = None) -> str:
    provided = settings.admin_email.strip().lower()
    if provided:
        return provided

    digits = "".join(ch for ch in settings.admin_phone if ch.isdigit()) or "main"
    base = f"admin{digits}@market.uz"
    stmt = select(User).where(User.email == base)
    if exclude_user_id is not None:
        stmt = stmt.where(User.id != exclude_user_id)
    existing = db.scalar(stmt)
    if existing is None:
        return base

    suffix = 1
    while True:
        candidate = f"admin{digits}_{suffix}@market.uz"
        stmt = select(User).where(User.email == candidate)
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        taken = db.scalar(stmt)
        if taken is None:
            return candidate
        suffix += 1


def seed_admin(db: Session) -> None:
    other_admins = db.scalars(
        select(User).where(User.is_admin.is_(True), User.phone != settings.admin_phone)
    ).all()
    for user in other_admins:
        user.is_admin = False

    admin = db.scalar(select(User).where(User.phone == settings.admin_phone))
    if admin:
        should_update = False
        target_email = _resolve_admin_email(db, exclude_user_id=admin.id)
        if admin.email != target_email:
            admin.email = target_email
            should_update = True
        if not admin.is_admin:
            admin.is_admin = True
            should_update = True
        if not verify_password(settings.admin_password, admin.password_hash):
            admin.password_hash = get_password_hash(settings.admin_password)
            should_update = True
        if other_admins:
            should_update = True
        if should_update:
            db.commit()
        return

    admin = User(
        phone=settings.admin_phone,
        email=_resolve_admin_email(db),
        password_hash=get_password_hash(settings.admin_password),
        is_admin=True,
    )
    db.add(admin)
    db.commit()


def seed_catalog(db: Session) -> None:
    if db.scalar(select(Category.id).limit(1)):
        return

    categories = [
        Category(
            slug="bahorgi-kolleksiya",
            name_uz="Bahorgi kolleksiya",
            name_en="Spring Collection",
            name_ru="Весенняя коллекция",
            description_uz="Yangi mavsum uchun zamonaviy kiyimlar.",
            description_en="Modern outfits for the new season.",
            description_ru="Современная одежда для нового сезона.",
        ),
        Category(
            slug="atirlar",
            name_uz="Atirlar",
            name_en="Perfumes",
            name_ru="Парфюмерия",
            description_uz="Ayollar va erkaklar uchun premium atirlar.",
            description_en="Premium fragrances for women and men.",
            description_ru="Премиальные ароматы для женщин и мужчин.",
        ),
    ]
    db.add_all(categories)
    db.flush()

    products = [
        Product(
            category_id=categories[0].id,
            name_uz="Classic Beige Trenç",
            name_en="Classic Beige Trench",
            name_ru="Классический бежевый тренч",
            description_uz="Yengil matodan tikilgan, bahor uchun ideal trench palto.",
            description_en="Light fabric trench coat, perfect for spring weather.",
            description_ru="Легкий тренч из ткани, идеально для весны.",
            price=89.99,
            image_url="https://images.unsplash.com/photo-1521572163474-6864f9cf17ab",
            stock=30,
        ),
        Product(
            category_id=categories[0].id,
            name_uz="Minimal White Shirt",
            name_en="Minimal White Shirt",
            name_ru="Минималистичная белая рубашка",
            description_uz="Uniseks, yumshoq paxtali, kundalik uslub uchun.",
            description_en="Unisex soft cotton shirt for everyday style.",
            description_ru="Унисекс рубашка из мягкого хлопка на каждый день.",
            price=34.5,
            image_url="https://images.unsplash.com/photo-1603252109303-2751441dd157",
            stock=50,
        ),
        Product(
            category_id=categories[1].id,
            name_uz="Noir Night 50ml",
            name_en="Noir Night 50ml",
            name_ru="Noir Night 50мл",
            description_uz="Qora rezavor va yog'och notalari bilan chuqur hid.",
            description_en="Deep scent with black berry and woody notes.",
            description_ru="Глубокий аромат с ягодными и древесными нотами.",
            price=55.0,
            image_url="https://images.unsplash.com/photo-1594035910387-fea47794261f",
            stock=40,
        ),
        Product(
            category_id=categories[1].id,
            name_uz="Flora Bloom 30ml",
            name_en="Flora Bloom 30ml",
            name_ru="Flora Bloom 30мл",
            description_uz="Yengil gullar aromati, kundalik foydalanish uchun.",
            description_en="Fresh floral fragrance for daily wear.",
            description_ru="Легкий цветочный аромат для ежедневного использования.",
            price=42.0,
            image_url="https://images.unsplash.com/photo-1541643600914-78b084683601",
            stock=35,
        ),
    ]
    db.add_all(products)
    db.commit()


def seed_all(db: Session, include_catalog: bool = True) -> None:
    seed_admin(db)
    if include_catalog:
        seed_catalog(db)
