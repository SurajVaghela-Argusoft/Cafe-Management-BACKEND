from datetime import date, datetime
from typing import Any, Generic, List, Optional, TypeVar

from pydantic import BaseModel, EmailStr
from app.core import enum


T = TypeVar("T")


class ErrorDetail(BaseModel):
    code: int
    message: str
    details: Optional[Any] = None


class APIResponse(BaseModel, Generic[T]):
    success: bool = True
    message: Optional[str] = None
    data: Optional[T] = None
    error: Optional[ErrorDetail] = None


def success_response(data: Any = None, message: Optional[str] = None) -> dict:
    return {"success": True, "message": message, "data": data, "error": None}


def error_response(code: int, message: str, details: Any = None) -> dict:
    return {
        "success": False,
        "message": None,
        "data": None,
        "error": {"code": code, "message": message, "details": details},
    }


class UserCreate(BaseModel):
    name : str
    email : EmailStr
    phone : str
    password : str
    role : Optional[enum.UserRole]
    

class Token(BaseModel):
    access_token : str
    token_type : str
    # role:str

class AssignRole(BaseModel):
    user_id : int
    role : enum.UserRole


class TokenData(BaseModel):
    id : Optional[str] = None


class CreateCategory(BaseModel):
    category_name : str
    description : str

class CreateItem(BaseModel):
    category_id : int
    item_name : str
    item_size : str
    price : float

class CartItemSchema(BaseModel):
    item_id : int
    quantity : int

    class Config:
        from_attributes = True


class CreateCart(BaseModel):
    items : List[CartItemSchema] 


class CreateTable(BaseModel):
    table_number : int
    capacity : int


class ReserveTableRequest(BaseModel):
    total_person: int
    reserved_for_time: datetime
    end_time: datetime       


class EmployeeListResponse(BaseModel):
    employee_id: int
    joining_date: date
    employee_status: str 
    last_date: Optional[date] = None
    name: str            
    class Config:
        from_attributes = True 


class MarkAttendance(BaseModel):
    employee_id: int
    in_time: datetime
    out_time: Optional[datetime] = None

    class Config:
        from_attributes = True

class UpdateCategory(BaseModel):
    category_name: Optional[str] = None
    description: Optional[str] = None


class UpdateItem(BaseModel):
    category_id: Optional[int] = None
    item_name: Optional[str] = None
    item_size: Optional[str] = None
    price: Optional[float] = None

class EmployeeListResponse(BaseModel):
    employee_id: int
    name: str
    joining_date: date 
    employee_status: str
    last_date: Optional[date] = None  
    class Config:
        from_attributes = True


class OrderItemResponse(BaseModel):
    order_item_id: Optional[int] = None  
    item_id: Optional[int] = None
    name: Optional[str] = None          
    price: float
    quantity: int

    class Config:
        from_attributes = True

class OrderResponse(BaseModel):
    order_id: int
    order_status: str
    created_at: datetime 
    total_amount: float
    payment: str
    customer_name: str
    items: List[OrderItemResponse] 

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: enum.UserRole

    class Config:
        from_attributes = True


class CustomerOrderItemResponse(BaseModel):
    order_item_id: Optional[int] = None
    order_id: Optional[int] = None
    item_id: Optional[int] = None
    quantity: int
    price: Optional[float] = None

    class Config:
        from_attributes = True


class CustomerOrderResponse(BaseModel):
    order_id: int
    order_status: Optional[str] = None
    created_at: Optional[datetime] = None
    total_amount: Optional[float] = None
    payment: Optional[str] = None
    order_items: List[CustomerOrderItemResponse] = []

    class Config:
        from_attributes = True


class CustomerResponse(BaseModel):
    user_id: int
    name: str
    email: EmailStr
    phone: Optional[str] = None
    role: enum.UserRole
    orders: List[CustomerOrderResponse] = []

    class Config:
        from_attributes = True


class CategoryResponse(BaseModel):
    category_id: int
    category_name: str
    description: Optional[str] = None
    is_available: bool = True          

    class Config:
        from_attributes = True


class ItemResponse(BaseModel):
    item_id: int
    category_id: int
    item_name: str
    item_size: Optional[str] = None
    price: float
    is_available: bool = True          


    class Config:
        from_attributes = True


class TableResponse(BaseModel):
    table_id: Optional[int] = None
    table_number: int
    capacity: int
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceResponse(BaseModel):
    attendance_id: Optional[int] = None
    employee_id: int
    in_time: datetime
    out_time: Optional[datetime] = None

    class Config:
        from_attributes = True



class CartCreatedResponse(BaseModel):
    cart_id: int


class CartResponse(BaseModel):
    cart_id: int
    customer_id: Optional[int] = None
    status: Optional[str] = None

    class Config:
        from_attributes = True


class CartItemDetailResponse(BaseModel):
    cart_item_id: Optional[int] = None
    cart_id: int
    item_id: int
    quantity: int

    class Config:
        from_attributes = True


class AllCartsResponse(BaseModel):
    cart: List[CartResponse] = []
    cart_item: List[CartItemDetailResponse] = []


class OrderSummaryResponse(BaseModel):
    order_id: int
    cart_id: Optional[int] = None
    customer_id: Optional[int] = None
    total_amount: Optional[float] = None
    order_status: Optional[str] = None
    payment: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True




class PlaceOrderResponse(BaseModel):
    order_id: int
    total_amount: float
    order_status: str

    class Config:
        from_attributes = True


class OrderHistoryItemResponse(OrderSummaryResponse):
    items: List[CustomerOrderItemResponse] = []


class OrderHistoryResponse(BaseModel):
    history: List[OrderHistoryItemResponse] = []


class ReservationResponse(BaseModel):
    reservation_id: Optional[int] = None
    table_id: int
    reserved_by: Optional[int] = None
    total_person: int
    reserved_for_time: datetime
    end_time: datetime
    class Config:
        from_attributes = True



class EmployeeStatusResponse(BaseModel):
    employee_id: int
    employee_status: str
    last_date: Optional[date] = None
    class Config:
        from_attributes = True

class ReservationDetailResponse(BaseModel):
    reservation_id: int
    table_id: int
    table_number: int
    reserved_by: int
    customer_name: Optional[str] = None    
    total_person: int
    reserved_for_time: datetime
    end_time: datetime
    cancelled_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class AttendanceDetailResponse(BaseModel):
    attendance_id: int
    employee_id: int
    employee_name: str
    in_time: datetime
    out_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class ApplyLeave(BaseModel):
    leave_type: enum.LeaveType
    start_date: date
    end_date: date


class LeaveResponse(BaseModel):
    leave_id: int
    leave_type: enum.LeaveType
    start_date: date
    end_date: date
    status: enum.LeaveStatus
    created_at: datetime

    class Config:
        from_attributes = True



class UpdateLeaveStatus(BaseModel):
    status: enum.LeaveStatus         
 
class LeaveDetailResponse(BaseModel):
    leave_id: int
    employee_id: int
    employee_name: str
    leave_type: enum.LeaveType
    start_date: date
    end_date: date
    status: enum.LeaveStatus
    created_at: datetime
    approved_at: Optional[datetime] = None
 
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str

class RefreshRequest(BaseModel):
    refresh_token: str


