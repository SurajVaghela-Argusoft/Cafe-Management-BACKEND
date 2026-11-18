from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
import pydantic
from sqlalchemy.orm import Session
from typing import List

from app.core import enum, oauth2, security
from app.core.database import get_db
from app.models import models
from app.schema import schemas
from datetime import date
from collections import defaultdict

router = APIRouter(prefix='/employee', tags=['employee'])


def roleChecker(current_user: models.User = Depends(oauth2.get_user)):
    allowed_roles = [enum.UserRole.CUSTOMER] 
    if current_user.role  in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )
    return current_user.user_id

# @router.get("/allpendingorder", status_code = status.HTTP_200_OK)
# def get_all_pending_order(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
#     orders = db.query(models.Orders).filter(models.Orders.order_status == enum.OrderStatus.COOKING).all()
#     return orders

# @router.get("/allpendingorder", response_model=schemas.APIResponse[List[schemas.OrderResponse]], status_code=status.HTTP_200_OK)
# def get_all_pending_order(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
#     orders = db.query(models.Orders).filter(models.Orders.order_status == enum.OrderStatus.COOKING).all()
    
#     # SELECT name, FROM Orders JOIN user(user.user_id == Orders.customer_id) SELECT * FROM oderItems WHERE oders.order_id == orderItems.order_id; 

#     # SELECT name, FROM Orders   JOIN user(user.user_id == Orders.customer_id) JOIN oderItems ON oders.order_id == orderItems.order_id where Orders.order_status=="Cooking" ; 

#     for o in orders:
#         user = db.query(models.User).filter(models.User.user_id == o.customer_id).first()
#         o.customer_name = user.name if user else "Unknown Customer"
        
#         oitem = db.query(models.OrderItem).filter(models.OrderItem.order_id == o.order_id).all()
#         o.items = oitem
        
#     return schemas.success_response(data=orders)


@router.get("/allpendingorder", response_model=schemas.APIResponse[List[schemas.OrderResponse]], status_code=status.HTTP_200_OK)
def get_all_pending_order(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    # Fetch orders, customer names, and order items using explicit joins in a single query
    results = (db.query(models.Orders, models.User.name, models.OrderItem).outerjoin(models.User, models.Orders.customer_id == models.User.user_id).outerjoin(models.OrderItem, models.Orders.order_id == models.OrderItem.order_id).filter(models.Orders.order_status == enum.OrderStatus.COOKING).all())


    orders_dict = {}
    items_by_order = defaultdict(list)

    for order, customer_name, item in results:
        if order.order_id not in orders_dict:
            order.customer_name = customer_name if customer_name else "Unknown Customer"
            orders_dict[order.order_id] = order
            
        if item:  
            items_by_order[order.order_id].append(item)

    for order_id, order in orders_dict.items():
        order.items = items_by_order[order_id]

    return schemas.success_response(data=list(orders_dict.values()))


@router.patch("/successorder/{order_id}", response_model=schemas.APIResponse[schemas.OrderSummaryResponse], status_code = status.HTTP_200_OK)
def successorder(order_id : int, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    order = db.query(models.Orders).filter(order_id == models.Orders.order_id).first()
    if order is None:
         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order mwith id {order_id} does not exist.")
    if order.order_status == enum.OrderStatus.COMPLETED:
        return schemas.success_response(message="already completed")
    order.order_status = enum.OrderStatus.COMPLETED
    db.commit()
    db.refresh(order)
    return schemas.success_response(data=order, message="order status changes")


@router.get("/myattendance", response_model=schemas.APIResponse[List[schemas.AttendanceResponse]], status_code=status.HTTP_200_OK)
def my_attendance(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    employee = db.query(models.Employee).filter(models.Employee.user_id == current_user).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee record not found for this user.")

    records = db.query(models.EmployeeAttendance).filter(
        models.EmployeeAttendance.employee_id == employee.employee_id
    ).order_by(models.EmployeeAttendance.in_time.desc()).all()

    return schemas.success_response(data=records)


@router.post("/applyleave", response_model=schemas.APIResponse[schemas.LeaveResponse], status_code=status.HTTP_201_CREATED)
def apply_leave(leave_in: schemas.ApplyLeave, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    employee = db.query(models.Employee).filter(models.Employee.user_id == current_user).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee not found for this user.")

    if employee.employee_status != enum.EmployeeStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Inactive employees cannot apply for leave.")

    if leave_in.start_date > leave_in.end_date:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start date must be on or before the end date.")

    if leave_in.start_date < date.today():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot apply for leave in the past.")

    overlapping = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.employee_id == employee.employee_id,
        models.LeaveRequest.status != enum.LeaveStatus.REJECTED,
        models.LeaveRequest.start_date <= leave_in.end_date,
        models.LeaveRequest.end_date >= leave_in.start_date,
    ).first()
    if overlapping:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="You already have a leave request for these dates.")

    leave = models.LeaveRequest(
        employee_id=employee.employee_id,
        leave_type=leave_in.leave_type,
        start_date=leave_in.start_date,
        end_date=leave_in.end_date,
    )
    db.add(leave)
    db.flush()
    db.commit()
    db.refresh(leave)
    return schemas.success_response(data=leave, message="Leave request submitted")


@router.get("/myleaves", response_model=schemas.APIResponse[List[schemas.LeaveResponse]], status_code=status.HTTP_200_OK)
def my_leaves(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    employee = db.query(models.Employee).filter(models.Employee.user_id == current_user).first()
    if employee is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Employee record not found for this user.")

    leaves = db.query(models.LeaveRequest).filter(
        models.LeaveRequest.employee_id == employee.employee_id
    ).order_by(models.LeaveRequest.start_date.desc()).all()

    return schemas.success_response(data=leaves)    