"""
MegaCommerce Authentication & User Management Service
"""

from typing import Dict, Any, Optional, List
from sqlalchemy.orm import Session
from database.models.user import User, Address, SellerProfile, AuditLog
from database.repositories.domain_repositories import UserRepository, BaseRepository
from shared.enums import UserRole, UserStatus, AuditAction
from shared.exceptions import (
    AuthenticationError, AuthorizationError, UserAlreadyExistsError, ResourceNotFoundError
)
from shared.security import hash_password, verify_password, create_access_token
from shared.dtos import UserRegisterRequest, UserLoginRequest, AuthTokenResponse, AddressCreateRequest


class AuthService:
    """Core domain service for User lifecycle, Authentication, RBAC, and Address Management."""

    def __init__(self, db: Session):
        self.db = db
        self.user_repo = UserRepository(db)
        self.address_repo = BaseRepository(Address, db)
        self.seller_repo = BaseRepository(SellerProfile, db)
        self.audit_repo = BaseRepository(AuditLog, db)

    def register_user(self, req: UserRegisterRequest, ip_address: Optional[str] = None) -> AuthTokenResponse:
        """Registers a new user (Customer or Seller) and creates appropriate profile."""
        existing = self.user_repo.get_by_email(req.email)
        if existing:
            raise UserAlreadyExistsError(f"Account with email '{req.email}' already exists.")

        user = User(
            email=req.email,
            hashed_password=hash_password(req.password),
            first_name=req.first_name,
            last_name=req.last_name,
            phone_number=req.phone_number,
            role=req.role.value if isinstance(req.role, UserRole) else str(req.role),
            status=UserStatus.ACTIVE.value
        )
        self.db.add(user)
        self.db.flush()

        # If registering as SELLER, create SellerProfile
        if req.role == UserRole.SELLER or str(req.role) == UserRole.SELLER.value:
            company = req.company_name or f"{req.first_name}'s Store"
            seller = SellerProfile(
                user_id=user.id,
                company_name=company,
                store_name=company,
                support_email=req.email,
                support_phone=req.phone_number
            )
            self.db.add(seller)

        # Record Audit Log
        audit = AuditLog(
            user_id=user.id,
            action=AuditAction.USER_REGISTER.value,
            entity_name="User",
            entity_id=user.id,
            details={"email": user.email, "role": user.role},
            ip_address=ip_address
        )
        self.db.add(audit)
        self.db.commit()

        # Generate JWT Token
        token_str = create_access_token(
            user_id=user.id,
            email=user.email,
            role=UserRole(user.role)
        )

        return AuthTokenResponse(
            access_token=token_str,
            user_id=user.id,
            email=user.email,
            role=user.role,
            expires_in_seconds=86400
        )

    def authenticate_user(self, req: UserLoginRequest, ip_address: Optional[str] = None) -> AuthTokenResponse:
        """Validates credentials and generates access token."""
        user = self.user_repo.get_by_email(req.email)
        if not user or not verify_password(req.password, user.hashed_password):
            raise AuthenticationError("Invalid email or password.")

        if user.status != UserStatus.ACTIVE.value:
            raise AuthenticationError(f"User account is currently '{user.status}'.")

        # Record Audit Log
        audit = AuditLog(
            user_id=user.id,
            action=AuditAction.USER_LOGIN.value,
            entity_name="User",
            entity_id=user.id,
            ip_address=ip_address
        )
        self.db.add(audit)
        self.db.commit()

        token_str = create_access_token(
            user_id=user.id,
            email=user.email,
            role=UserRole(user.role)
        )

        return AuthTokenResponse(
            access_token=token_str,
            user_id=user.id,
            email=user.email,
            role=user.role,
            expires_in_seconds=86400
        )

    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Fetches full user profile including seller profile if applicable."""
        user = self.user_repo.get_by_id_or_raise(user_id)
        profile_data = {
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "phone_number": user.phone_number,
            "role": user.role,
            "status": user.status,
            "created_at": user.created_at.isoformat(),
            "addresses": [
                {
                    "id": a.id,
                    "title": a.title,
                    "street_address": a.street_address,
                    "city": a.city,
                    "state_province": a.state_province,
                    "postal_code": a.postal_code,
                    "country": a.country,
                    "is_default": a.is_default
                } for a in user.addresses
            ]
        }
        if user.seller_profile:
            profile_data["seller_profile"] = {
                "id": user.seller_profile.id,
                "company_name": user.seller_profile.company_name,
                "store_name": user.seller_profile.store_name,
                "rating_average": user.seller_profile.rating_average,
                "total_sales_count": user.seller_profile.total_sales_count
            }
        return profile_data

    def add_address(self, user_id: str, req: AddressCreateRequest) -> Address:
        """Adds a new delivery/billing address for a user."""
        user = self.user_repo.get_by_id_or_raise(user_id)
        if req.is_default:
            for addr in user.addresses:
                addr.is_default = False

        new_addr = Address(
            user_id=user_id,
            title=req.title,
            street_address=req.street_address,
            apartment_unit=req.apartment_unit,
            city=req.city,
            state_province=req.state_province,
            postal_code=req.postal_code,
            country=req.country,
            is_default=req.is_default or len(user.addresses) == 0
        )
        self.db.add(new_addr)
        self.db.commit()
        return new_addr
