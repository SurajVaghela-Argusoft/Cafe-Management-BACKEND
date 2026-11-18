from datetime import datetime, date
from pydantic import BaseModel
from sqlalchemy import Column, Integer, String, Date, DateTime, Boolean, ForeignKey, CheckConstraint, UniqueConstraint, Enum, text

from app.core.enum import CartStatus, ItemStatus, EmployeeStatus, BranchStatus, LeaveType, LeaveStatus, OrderStatus, PaymentStatus, UserRole
from app.core.database import Base


# class Branch(Base):
#     __tablename__ = "branch"
#     __table_args__ = (
#         CheckConstraint("open_time < close_time", name="check_branch_timings"),
#     )

#     branch_id = Column(Integer, primary_key=True)
#     branch_name = Column(String(100), nullable=False, unique=True)
#     address = Column(String(250), nullable=False)
#     status = Column(Enum(BranchStatus, name="enum_branch_status"), nullable=False, default=BranchStatus.ACTIVE)
#     open_time = Column(DateTime, nullable=False)
#     close_time = Column(DateTime, nullable=False)
#     contact = Column(String(50), nullable=False, unique=True)
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    role = Column(Enum(UserRole), name = "user_role", nullable = False, default=UserRole.CUSTOMER)
    email = Column(String(100), nullable=False, unique=True)
    phone = Column(String(20), nullable=False, unique=True)
    password = Column(String(250), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Role(Base):
    __tablename__ = "role"

    role_id = Column(Integer, primary_key=True)
    role_name = Column(String(200), nullable=False, unique=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Employee(Base):
    __tablename__ = "employee"
    employee_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False, unique=True)
    # branch_id = Column(Integer, ForeignKey("branch.branch_id"), nullable=False)
    joining_date = Column(Date,default=datetime.utcnow, nullable=False)
    last_date = Column(Date, nullable=True)
    employee_status = Column(Enum(EmployeeStatus, name="enum_employee_status"), nullable=False, default=EmployeeStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EmployeeAttendance(Base):
    __tablename__ = "employee_attendance"
    __table_args__ = (
        CheckConstraint("out_time IS NULL OR out_time > in_time", name="check_attendance_timeline"),
    )

    attendance_id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employee.employee_id"), nullable=False)
    in_time = Column(DateTime, nullable=False)
    out_time = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class LeaveRequest(Base):
    __tablename__ = "leave_request"
    __table_args__ = (
        CheckConstraint("start_date <= end_date", name="check_leave_dates"),
    )

    leave_id = Column(Integer, primary_key=True)
    employee_id = Column(Integer, ForeignKey("employee.employee_id"), nullable=False)
    leave_type = Column(Enum(LeaveType, name="enum_leave_type"), nullable=False)
    start_date = Column(Date, nullable=False)
    end_date = Column(Date, nullable=False)
    status = Column(Enum(LeaveStatus, name="enum_leave_status"), nullable=False, default=LeaveStatus.PENDING)
    approved_by = Column(Integer, ForeignKey("employee.employee_id"), nullable=True)
    approved_at = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)




class MenuCategory(Base):
    __tablename__ = "menu_category"

    category_id = Column(Integer, primary_key=True)
    category_name = Column(String(50), nullable=False, unique=True)
    description = Column(String(100), nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_available = Column(Boolean, nullable=False, default=True, server_default=text("true"))  



class MenuItem(Base):
    __tablename__ = "menu_item"
    
    item_id = Column(Integer, primary_key=True)
    category_id = Column(Integer, ForeignKey("menu_category.category_id", ondelete="RESTRICT"), nullable=False)
    item_name = Column(String(50), nullable=False)
    item_size = Column(String(50), nullable=False)
    price = Column(Integer, CheckConstraint("price > 0"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_available = Column(Boolean, nullable=False, default=True, server_default=text("true"))   



# class BranchMenuItem(Base):
#     __tablename__ = "branch_menu_item"

#     branch_item_id = Column(Integer, primary_key=True)
#     branch_id = Column(Integer, ForeignKey("branch.branch_id", ondelete="CASCADE"), nullable=False)
#     item_id = Column(Integer, ForeignKey("menu_item.item_id"), nullable=False)
#     status = Column(Enum(ItemStatus, name="enum_item_status"), nullable=False, default=ItemStatus.AVAILABLE)
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# class BranchTable(Base):
#     __tablename__ = "branch_table"
#     __table_args__ = (
#         UniqueConstraint("branch_id", "table_number", name="unique_branch_table_number"),
#     )

#     branch_table_id = Column(Integer, primary_key=True)
#     branch_id = Column(Integer, ForeignKey("branch.branch_id"), nullable=False)
#     table_number = Column(Integer, nullable=False)
#     capacity = Column(Integer, CheckConstraint("capacity > 0"), nullable=False)
#     created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
#     updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Table(Base):
    __tablename__ = "table"

    table_id = Column(Integer, primary_key=True)
    table_number = Column(Integer, nullable=False)
    capacity = Column(Integer, CheckConstraint("capacity > 0"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class TableReservation(Base):
    __tablename__ = "table_reservation"
    __table_args__ = (
        CheckConstraint("reserved_for_time < end_time", name="check_reservation_timeline"),
    )

    reservation_id = Column(Integer, primary_key=True)
    table_id = Column(Integer, ForeignKey("table.table_id"), nullable=False)
    reserved_by = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    total_person = Column(Integer, CheckConstraint("total_person > 0"), nullable=False)
    reserved_for_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    reserved_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Cart(Base):
    __tablename__ = "cart"

    cart_id = Column(Integer, primary_key=True)
    customer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    status = Column(Enum(CartStatus, name="enum_cart_status"), nullable=False, default=CartStatus.ACTIVE)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class CartItem(Base):
    __tablename__ = "cart_item"
    __table_args__ = (
        UniqueConstraint("cart_id", "item_id", name="unique_cart_menu_item"),
    )

    cart_item_id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("cart.cart_id"), nullable=False)
    item_id = Column(Integer, ForeignKey("menu_item.item_id"), nullable=False)
    quantity = Column(Integer, CheckConstraint("quantity > 0"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Orders(Base):
    __tablename__ = "orders"
 

    order_id = Column(Integer, primary_key=True)
    cart_id = Column(Integer, ForeignKey("cart.cart_id"), nullable=False)
    customer_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)
    total_amount = Column(Integer, CheckConstraint("total_amount > 0"), nullable=False)
    order_status = Column(Enum(OrderStatus, name="enum_order_status"), nullable=False, default=OrderStatus.COOKING)
    payment = Column(Enum(PaymentStatus, name="enum_payment_status"), nullable=False, default=PaymentStatus.PENDING)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OrderItem(Base):
    __tablename__ = "order_item"
    __table_args__ = (
        UniqueConstraint("order_id", "item_id", name="unique_order_menu_item"),
    )

    ordr_item_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, ForeignKey("menu_item.item_id"), nullable=False)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    quantity = Column(Integer, CheckConstraint("quantity > 0"), nullable=False)
    price = Column(Integer, CheckConstraint("price > 0"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class Payment(Base):
    __tablename__ = "payment"
    payment_id = Column(Integer, primary_key=True)
    order_id = Column(Integer, ForeignKey("orders.order_id"), nullable=False)
    method = Column(String(50), nullable=False)
    status = Column(Enum(PaymentStatus, name="enum_payment_status"), nullable=False, default=PaymentStatus.PENDING)
    amount = Column(Integer, CheckConstraint("amount > 0"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)



class RefreshToken(Base):
    __tablename__ = "refresh_token"

    token_id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.user_id", ondelete="CASCADE"), nullable=False, index=True)
    token_hash = Column(String(64), nullable=False, unique=True, index=True)
    expires_at = Column(DateTime, nullable=False)
    revoked_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)