from datetime import date, datetime
from typing import List
import app.routers
from fastapi import FastAPI, Query, Response, status, HTTPException, Depends, APIRouter
import pydantic
from sqlalchemy.orm import Session, join
from typing import List

from app.core import enum, oauth2, security
from app.core.database import get_db
from app.models import models
from app.routers import customer
from app.schema import schemas
from app.schema.schemas import OrderResponse, APIResponse, success_response, error_response
from typing import List, Optional
from collections import defaultdict

router = APIRouter(prefix='/admin', tags=['Admin'])

def roleChecker(current_user: models.User = Depends(oauth2.get_user)):
    allowed_roles = [enum.UserRole.ADMIN] 
    if current_user.role not in allowed_roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to perform this action"
        )
    return current_user.user_id


# @router.post("/createrole", status_core = status.HTTP_201_CREATED)
# def create_role(role:schemas.CreateRole, db: Session = Depends(get_db), current_user : int = Depends(roleChecker)):
#     role_query = db.query(models.Role).filter(models.Role.name == role)
#     if role_query.first():
#         raise HTTPException(status_code=status.HTTP_208_ALREADY_REPORTED, detail = f"role: {role} already in the Database")
#     new_role = models.Role(role = role)
#     db.add(new_role)
#     db.commit()
#     db.refresh(new_role)
#     return role

@router.get("/getalluser", response_model=APIResponse[List[schemas.UserResponse]], status_code = status.HTTP_200_OK)
def get_all_user(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    users = db.query(models.User).all()
    return success_response(data=users)



@router.get("/getallemployee", response_model=APIResponse[List[schemas.EmployeeListResponse]], status_code = status.HTTP_200_OK)
def get_all_employee(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    # employee = db.query(models.Employee).all()
    employee = db.query(models.Employee.employee_id, models.Employee.joining_date, models.Employee.employee_status, models.Employee.last_date, models.User.name).join(models.User, models.Employee.user_id == models.User.user_id).all()
    
    return success_response(data=employee)

# @router.get("/getallcustomer", response_model=APIResponse[List[schemas.CustomerResponse]], status_code=status.HTTP_200_OK)
# def get_all_customer(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
#     customers = db.query(models.User).filter(models.User.role == enum.UserRole.CUSTOMER).all() 
    
#     for cust in customers:
#         customer_orders = db.query(models.Orders).filter(models.Orders.customer_id == cust.user_id).all()    
#         for ord in customer_orders:
#             order_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == ord.order_id).all()
#             ord.order_items = order_items       
            
#         cust.orders = customer_orders
        
#     return success_response(data=customers)



@router.get("/getallcustomer", response_model=APIResponse[List[schemas.CustomerResponse]], status_code=status.HTTP_200_OK)
def get_all_customer(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    customers = (db.query(models.User).filter(models.User.role == enum.UserRole.CUSTOMER).order_by(models.User.user_id).all())
    if not customers:
        return success_response(data=[])

    orders = db.query(models.Orders).filter(models.Orders.customer_id.in_([c.user_id for c in customers])).all()

    items = db.query(models.OrderItem).filter(models.OrderItem.order_id.in_([o.order_id for o in orders])).all() if orders else []

    items_by_order = defaultdict(list)
    for it in items:
        items_by_order[it.order_id].append(it)

    orders_by_customer = defaultdict(list)
    for o in orders:
        o.order_items = items_by_order.get(o.order_id, [])
        orders_by_customer[o.customer_id].append(o)

    for c in customers:
        c.orders = orders_by_customer.get(c.user_id, [])

    return success_response(data=customers)


@router.patch("/assignrole", response_model=APIResponse[None], status_code=status.HTTP_202_ACCEPTED)
def assign_role(assignrole: schemas.AssignRole, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    user_query = db.query(models.User).filter(models.User.user_id == assignrole.user_id)
    user = user_query.first()
    if user == None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"user with id: {assignrole.user_id} was not found")

    if user.role == assignrole.role:
        return success_response(message="Already having same role")

    if user.role != enum.UserRole.CUSTOMER and assignrole.role == enum.UserRole.CUSTOMER:
        employee = db.query(models.Employee).filter(models.Employee.user_id == user.user_id).first()
        if employee:
            employee.employee_status = enum.EmployeeStatus.INACTIVE
        
    if user.role == enum.UserRole.CUSTOMER and assignrole.role != enum.UserRole.CUSTOMER:
        employee = db.query(models.Employee).filter(models.Employee.user_id == user.user_id).first()
        
        if employee:
            employee.employee_status = enum.EmployeeStatus.ACTIVE
        else:
            new_employee = models.Employee(
                user_id=user.user_id, 
                employee_status=enum.EmployeeStatus.ACTIVE
            )
            db.add(new_employee)

    user.role = assignrole.role   

    db.commit()
    return success_response(message="Updated successfully")




@router.post("/createcategory", response_model=APIResponse[schemas.CategoryResponse], status_code= status.HTTP_201_CREATED)
def create_category(createcategory: schemas.CreateCategory, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    category_query = db.query(models.MenuCategory).filter(createcategory.category_name == models.MenuCategory.category_name)
    if category_query.first():
        return error_response(code=status.HTTP_400_BAD_REQUEST, message="already having same name category..")

    category_data = createcategory.model_dump()
    category = models.MenuCategory(**category_data)
    db.add(category)
    db.commit()
    db.refresh(category)
    return success_response(data=category, message="Category created successfully")


@router.post("/createitem", response_model=APIResponse[schemas.ItemResponse], status_code= status.HTTP_201_CREATED)
def create_item(createitem: schemas.CreateItem, db : Session = Depends(get_db), current_user : int = Depends(roleChecker)):
    existing_item = db.query(models.MenuItem).filter(models.MenuItem.item_name == createitem.item_name, models.MenuItem.item_size == createitem.item_size
    ).first()
    if existing_item:
        return error_response(code=status.HTTP_400_BAD_REQUEST, message="Already having same name item with same size")
    item_data = createitem.model_dump()
    item = models.MenuItem(**item_data)
    db.add(item)
    db.commit()
    db.refresh(item)
    return success_response(data=item, message="Item created successfully")


# @router.get("/allorder", status_code = status.HTTP_200_OK,   response_model=List[schemas.AllOrdersResponse])
# def get_all_pending_order(db: Session = Depends   (get_db), current_user: int = Depends(roleChecker)):
#     orders = db.query(models.Orders).all()
#     return orders


@router.post("/addtable", response_model=APIResponse[schemas.TableResponse], status_code=status.HTTP_201_CREATED)
def add_table(createtable : schemas.CreateTable, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    table_query = db.query(models.Table).filter(models.Table.table_number == createtable.table_number)
    if table_query.first():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Table already created for this..")
    table_data = createtable.model_dump()
    table = models.Table(**table_data)
    db.add(table)
    db.commit()
    db.refresh(table)
    return success_response(data=table, message="Table created successfully")


# @router.get("/getorders", response_model=APIResponse[List[OrderResponse]], status_code=status.HTTP_200_OK) 
# def get_orders(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
#     orders = db.query(models.Orders).all()
#     for o in orders:
#         user = db.query(models.User).filter(models.User.user_id == o.customer_id).first()
#         o.customer_name = user.name
#         oitem = db.query(models.OrderItem).filter(models.OrderItem.order_id == o.order_id).all()
#         o.items = oitem
#     return success_response(data=orders)
@router.get("/getorders", response_model=APIResponse[List[OrderResponse]], status_code=status.HTTP_200_OK)
def get_orders(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    rows = (db.query(models.Orders, models.User.name).join(models.User, models.Orders.customer_id == models.User.user_id).order_by(models.Orders.created_at.desc()).all())
    if not rows:
        return success_response(data=[])

    items = db.query(models.OrderItem).filter(models.OrderItem.order_id.in_([o.order_id for o, _ in rows])).all()

    items_by_order = defaultdict(list)
    for it in items:
        items_by_order[it.order_id].append(it)

    result = []
    for o, name in rows:
        o.customer_name = name
        o.items = items_by_order.get(o.order_id, [])
        result.append(o)
    return success_response(data=result)





@router.post("/markattendance", response_model=APIResponse[schemas.AttendanceResponse], status_code=status.HTTP_201_CREATED)
def mark_attendance(attendance_data: schemas.MarkAttendance, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    if attendance_data.out_time and attendance_data.out_time <= attendance_data.in_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Out-time must be strictly after In-time.")

    active_session = db.query(models.EmployeeAttendance).filter(models.EmployeeAttendance.employee_id == attendance_data.employee_id, models.EmployeeAttendance.out_time == None).first()

    if active_session:
        if attendance_data.out_time:
            active_session.out_time = attendance_data.out_time
            db.commit()
            db.refresh(active_session)
            return success_response(data=active_session, message="Attendance session closed")
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="Employee is already checked in. Close their current active session first."
            )

    new_attendance_dict = attendance_data.model_dump()
    attendance_record = models.EmployeeAttendance(**new_attendance_dict)
    
    db.add(attendance_record)
    db.commit()
    db.refresh(attendance_record)
    return success_response(data=attendance_record, message="Attendance marked successfully")




@router.patch("/updatecategory/{category_id}", response_model=APIResponse[schemas.CategoryResponse], status_code=status.HTTP_200_OK)
def update_category(category_id: int, update_data: schemas.UpdateCategory, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    
    category = db.query(models.MenuCategory).filter(models.MenuCategory.category_id == category_id).first()
    
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {category_id} does not exist.")

    dumped_data = update_data.model_dump(exclude_unset=True)

    if "category_name" in dumped_data and dumped_data["category_name"] != category.category_name:
        name_exists = db.query(models.MenuCategory).filter(
            models.MenuCategory.category_name == dumped_data["category_name"]
        ).first()
        
        if name_exists:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST,detail="A category with this name already exists.")

    for key, value in dumped_data.items():
        setattr(category, key, value)

    db.commit()
    db.refresh(category)
    
    return success_response(data=category, message="Category updated successfully")



@router.patch("/updateitem/{item_id}", response_model=APIResponse[schemas.ItemResponse], status_code=status.HTTP_200_OK)
def update_item(
    item_id: int, 
    updateitem: schemas.UpdateItem, 
    db: Session = Depends(get_db), 
    current_user: int = Depends(roleChecker)
):
    item = db.query(models.MenuItem).filter(models.MenuItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with id {item_id} does not exist.")

    item_data = updateitem.model_dump(exclude_unset=True)

    if "item_name" in item_data and item_data["item_name"] != item.item_name:
        item_query = db.query(models.MenuItem).filter(models.MenuItem.item_name == item_data["item_name"]).first()
        if item_query:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already having same name item")

    for key, value in item_data.items():
        setattr(item, key, value)

    db.commit()
    db.refresh(item)
    return success_response(data=item, message="Item updated successfully")



@router.patch("/toggleemployeestatus/{employee_id}", response_model=APIResponse[schemas.EmployeeStatusResponse], status_code=status.HTTP_200_OK)
def toggle_employee_status(employee_id: int, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    employee = db.query(models.Employee).filter(models.Employee.employee_id == employee_id).first()
    if not employee:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Employee with id {employee_id} does not exist.")

    if employee.employee_status == enum.EmployeeStatus.ACTIVE:
        employee.employee_status = enum.EmployeeStatus.INACTIVE
        employee.last_date = date.today()      # last working day
        msg = "Employee marked as inactive"
    else:
        employee.employee_status = enum.EmployeeStatus.ACTIVE
        employee.last_date = None
        msg = "Employee marked as active"

    db.commit()
    db.refresh(employee)
    return success_response(data=employee, message=msg)


@router.get("/getreservations", response_model=APIResponse[List[schemas.ReservationDetailResponse]], status_code=status.HTTP_200_OK)
def get_reservations(db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    rows = db.query(
        models.TableReservation.reservation_id,
        models.TableReservation.table_id,
        models.Table.table_number,
        models.TableReservation.reserved_by,
        models.User.name.label("customer_name"),
        models.TableReservation.total_person,
        models.TableReservation.reserved_for_time,
        models.TableReservation.end_time,
        models.TableReservation.cancelled_at,
    ).join(models.Table, models.TableReservation.table_id == models.Table.table_id
    ).join(models.User, models.TableReservation.reserved_by == models.User.user_id
    ).order_by(models.TableReservation.reserved_for_time.desc()).all()

    return success_response(data=rows)


@router.patch("/cancelreservation/{reservation_id}", response_model=APIResponse[None], status_code=status.HTTP_200_OK)
def admin_cancel_reservation(reservation_id: int, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    reservation = db.query(models.TableReservation).filter(models.TableReservation.reservation_id == reservation_id).first()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found.")

    if reservation.cancelled_at is not None:
        return success_response(message="Reservation already cancelled")

    reservation.cancelled_at = datetime.now()
    db.commit()
    return success_response(message="Reservation cancelled successfully")


@router.delete("/deleteitem/{item_id}", response_model=APIResponse[None], status_code=status.HTTP_200_OK)
def delete_item(item_id: int, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    item = db.query(models.MenuItem).filter(models.MenuItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with id {item_id} does not exist.")

    used_in_order = db.query(models.OrderItem).filter(models.OrderItem.item_id == item_id).first()
    if used_in_order:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This item is part of past orders, so it cannot be deleted."
        )

    db.query(models.CartItem).filter(models.CartItem.item_id == item_id).delete()
    db.delete(item)
    db.commit()
    return success_response(message="Item deleted successfully")


@router.delete("/deletetable/{table_id}", response_model=APIResponse[None], status_code=status.HTTP_200_OK)
def delete_table(table_id: int, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    table = db.query(models.Table).filter(models.Table.table_id == table_id).first()
    if not table:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table with id {table_id} does not exist.")

    active_reservation = db.query(models.TableReservation).filter(
        models.TableReservation.table_id == table_id,
        models.TableReservation.cancelled_at == None,
        models.TableReservation.end_time > datetime.now(),
    ).first()
    if active_reservation:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This table has upcoming reservations. Cancel them first."
        )
    db.query(models.TableReservation).filter(models.TableReservation.table_id == table_id).delete()
    db.delete(table)
    db.commit()
    return success_response(message="Table deleted successfully")

@router.get("/getattendance", response_model=APIResponse[List[schemas.AttendanceDetailResponse]], status_code=status.HTTP_200_OK)
def get_attendance(employee_id: Optional[int] = None, month: Optional[str] = None, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    query = db.query(
        models.EmployeeAttendance.attendance_id,
        models.EmployeeAttendance.employee_id,
        models.User.name.label("employee_name"),
        models.EmployeeAttendance.in_time,
        models.EmployeeAttendance.out_time,
    ).join(models.Employee, models.EmployeeAttendance.employee_id == models.Employee.employee_id
    ).join(models.User, models.Employee.user_id == models.User.user_id)

    if employee_id is not None:
        query = query.filter(models.EmployeeAttendance.employee_id == employee_id)

    if month:
        try:
            start = datetime.strptime(month, "%Y-%m")          # "2026-10" -> 2026-10-01
        except ValueError:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Month must be in YYYY-MM format.")
        end = datetime(start.year + (start.month // 12), (start.month % 12) + 1, 1)   # first day of next month
        query = query.filter(models.EmployeeAttendance.in_time >= start, models.EmployeeAttendance.in_time < end)

    records = query.order_by(models.EmployeeAttendance.in_time.desc()).all()
    return success_response(data=records)



 
@router.get("/getleaves", response_model=APIResponse[List[schemas.LeaveDetailResponse]], status_code=status.HTTP_200_OK)
def get_leaves(status_filter: Optional[enum.LeaveStatus] = Query(None, alias="status"), db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    query = db.query(models.LeaveRequest.leave_id,models.LeaveRequest.employee_id, models.User.name.label("employee_name"), models.LeaveRequest.leave_type, models.LeaveRequest.start_date, models.LeaveRequest.end_date, models.LeaveRequest.status, models.LeaveRequest.created_at, models.LeaveRequest.approved_at,).join(models.Employee, models.LeaveRequest.employee_id == models.Employee.employee_id).join(models.User, models.Employee.user_id == models.User.user_id)
 
    if status_filter is not None:
        query = query.filter(models.LeaveRequest.status == status_filter)
 
    if status_filter == enum.LeaveStatus.PENDING:
        query = query.order_by(models.LeaveRequest.created_at.asc())
    else:
        query = query.order_by(models.LeaveRequest.created_at.desc())
 
    return success_response(data=query.all())
 
 
@router.patch("/updateleavestatus/{leave_id}", response_model=APIResponse[schemas.LeaveResponse], status_code=status.HTTP_200_OK)
def update_leave_status(leave_id: int, data: schemas.UpdateLeaveStatus, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    if data.status not in (enum.LeaveStatus.APPROVED, enum.LeaveStatus.REJECTED):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Status must be approved or rejected.")
 
    leave = db.query(models.LeaveRequest).filter(models.LeaveRequest.leave_id == leave_id).first()
    if leave is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Leave request with id {leave_id} does not exist.")
 
    if leave.status != enum.LeaveStatus.PENDING:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=f"This leave request is already {leave.status.value}.")
 
    approver = db.query(models.Employee).filter(models.Employee.user_id == current_user).first()
 
    leave.status = data.status
    leave.approved_by = approver.employee_id if approver else None
    leave.approved_at = datetime.utcnow()
 
    db.commit()
    db.refresh(leave)
    return success_response(data=leave, message=f"Leave {data.status.value}")
 




@router.patch("/togglecategory/{category_id}", response_model=APIResponse[schemas.CategoryResponse], status_code=status.HTTP_200_OK)
def toggle_category(category_id: int, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    category = db.query(models.MenuCategory).filter(models.MenuCategory.category_id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category with id {category_id} does not exist.")

    category.is_available = not category.is_available
    db.commit()
    db.refresh(category)
    msg = "Category marked as available" if category.is_available else "Category marked as unavailable"
    return success_response(data=category, message=msg)


@router.patch("/toggleitem/{item_id}", response_model=APIResponse[schemas.ItemResponse], status_code=status.HTTP_200_OK)
def toggle_item(item_id: int, db: Session = Depends(get_db), current_user: int = Depends(roleChecker)):
    item = db.query(models.MenuItem).filter(models.MenuItem.item_id == item_id).first()
    if not item:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Item with id {item_id} does not exist.")

    item.is_available = not item.is_available
    db.commit()
    db.refresh(item)
    msg = "Item marked as available" if item.is_available else "Item marked as unavailable"
    return success_response(data=item, message=msg)