import datetime

from fastapi import FastAPI, Response, status, HTTPException, Depends, APIRouter
import pydantic
from sqlalchemy import and_
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timezone

from app.core import enum, oauth2, security
from app.core.database import get_db
from app.models import models
from app.schema import schemas

router = APIRouter(prefix='/customer', tags=['customer'])

def ensure_orderable(db: Session, menu_item: models.MenuItem):
    category = db.query(models.MenuCategory).filter(
        models.MenuCategory.category_id == menu_item.category_id
    ).first()
    if not menu_item.is_available or (category and not category.is_available):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"'{menu_item.item_name}' is currently unavailable.",
        )


@router.post("/createcart", response_model=schemas.APIResponse[schemas.CartCreatedResponse], status_code = status.HTTP_200_OK)
def create_cart(createcart : schemas.CreateCart, db:Session = Depends(get_db), current_user:int = Depends(oauth2.get_current_user)):
    cart = models.Cart(customer_id = current_user)
    db.add(cart)
    db.flush() 
    for item in createcart.items:
        db_menu_item = db.query(models.MenuItem).filter(models.MenuItem.item_id == item.item_id).first()
        if not db_menu_item:
            db.rollback() 
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item with id {item.item_id} does not exist."
            )
        ensure_orderable(db, db_menu_item)      
        cart_item = models.CartItem(cart_id=cart.cart_id, item_id=item.item_id, quantity=item.quantity)
        db.add(cart_item)
    
    db.commit()
    db.refresh(cart)
    return schemas.success_response(data={"cart_id" : cart.cart_id}, message="Cart created successfully ")

@router.get("/getallcarts", response_model=schemas.APIResponse[schemas.AllCartsResponse], status_code=status.HTTP_200_OK)
def get_cart(db: Session = Depends(get_db)):
    cart = db.query(models.Cart).all()
    cart_items = db.query(models.CartItem).all()
    return schemas.success_response(data={"cart" : cart, "cart_item" : cart_items})

@router.get("/getcartbyid/{id}", response_model=schemas.APIResponse[List[schemas.CartItemDetailResponse]], status_code = status.HTTP_200_OK)
def get_cart_by_id(id : int, db: Session = Depends(get_db), current_user : int = Depends(oauth2.get_current_user)):
    cart_query = db.query(models.Cart).filter(models.Cart.cart_id == id)
    if not cart_query.first():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart does not exists with id {id}")
    cart_item = db.query(models.CartItem).filter(models.CartItem.cart_id == id).all()
    return schemas.success_response(data=cart_item)

# @router.post("/placeorder/{cart_id}", status_code= status.HTTP_200_OK)
# def place_order(cart_id : int, db:Session = Depends(get_db), current_user:int = Depends(oauth2.get_current_user)):
#     cart_query = db.query(models.Cart).filter(cart_id == models.Cart.cart_id)
#     cart = cart_query.first()
#     if cart is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart with id: {cart_id} not found")

#     cart.status = enum.CartStatus.COMPLETED


#     # cart_id, customer_id, total_amount

#     # item_id, order_id, quantity, price
#     order = 
#     return


@router.get("/getallorder", response_model=schemas.APIResponse[List[schemas.OrderSummaryResponse]],  status_code=status.HTTP_200_OK)
def get_all_order(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    order = db.query(models.Orders).filter(models.Orders.customer_id == current_user).all()
    return schemas.success_response(data=order)

@router.get("/getorderitembyid/{id}", response_model=schemas.APIResponse[List[schemas.CustomerOrderItemResponse]], status_code=status.HTTP_200_OK)
def get_all_item_by_orderid(id:int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    orderItems = db.query(models.OrderItem).filter(models.OrderItem.order_id == id).all()
    return schemas.success_response(data=orderItems)

@router.post("/placeorder/{cart_id}", response_model=schemas.APIResponse[schemas.PlaceOrderResponse], status_code=status.HTTP_200_OK)
def place_order(cart_id: int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    cart = db.query(models.Cart).filter(models.Cart.cart_id == cart_id).first()
    if cart is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Cart with id: {cart_id} not found")

    if cart.status == enum.CartStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Order already placed for this cart")

    cart_items = db.query(models.CartItem).filter(models.CartItem.cart_id == cart_id).all()
    if not cart_items:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot place order for an empty cart")

    total_amount = 0
    order_items_to_create = []

    for item in cart_items:
        menu_item = db.query(models.MenuItem).filter(models.MenuItem.item_id == item.item_id).first()
        if not menu_item:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Menu item {item.item_id} no longer exists")
        
        ensure_orderable(db, menu_item)        
        item_total_price = menu_item.price * item.quantity
        total_amount += item_total_price

        order_items_to_create.append({
            "item_id": item.item_id,
            "quantity": item.quantity,
            "price": menu_item.price
        })

   
    order = models.Orders(cart_id=cart_id, customer_id=cart.customer_id, total_amount=int(total_amount),order_status=enum.OrderStatus.COOKING, payment=enum.PaymentStatus.PENDING)
    db.add(order)
    db.flush() 
    
    for item in order_items_to_create:
        db_order_item = models.OrderItem(order_id=order.order_id,item_id=item["item_id"],quantity=item["quantity"], price=item["price"])
        db.add(db_order_item)

    cart.status = enum.CartStatus.COMPLETED
    db.commit()

    return schemas.success_response(
        data={
            "order_id": order.order_id,
            "total_amount": order.total_amount,
            "order_status": order.order_status
        },
        message="Order placed successfully"
    )

# @router.get("/orderhistory",status_code = status.HTTP_200_OK)
# def order_history(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
#     order = db.query(models.Orders).filter(models.Orders.customer_id == current_user).all()
#     if order is None:
#         return "No order placed.."
#     order_items = db.query(models.OrderItem).filter(models.OrderItem.order_id == order.order_id).all()
#     return {"order" : order, "items" : order_items}


@router.get("/orderhistory", response_model=schemas.APIResponse[schemas.OrderHistoryResponse], status_code=status.HTTP_200_OK)
def order_history(db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
    orders = db.query(models.Orders).filter(models.Orders.customer_id == current_user).all()
    
    if not orders:
        return schemas.success_response(data={"history": []}, message="No order placed..")
    
    full_history = []
    
    for single_order in orders:
        items = db.query(models.OrderItem).filter(models.OrderItem.order_id == single_order.order_id).all()
        single_order.items = items
        
        full_history.append(single_order)

    return schemas.success_response(data={"history": full_history})




# @router.post("/reservetable/{table_id}", status_code = status.HTTP_201_CREATED)
# def reserve_table(table_id : int, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
#     table_query = db.query(models.Table).filter(models.Table.table_id == table_id)
#     if table_query.first() is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Table with id : {table_id} not found..")
#     table = table_query.first()

#     # table_id, reserved_by, total_person, reserved_for_time, end_time
#     return

# @router.post("/reservetable/{table_id}", response_model=schemas.APIResponse[schemas.ReservationResponse], status_code=status.HTTP_201_CREATED)
# def reserve_table(table_id: int, reservation_in: schemas.ReserveTableRequest, db: Session = Depends(get_db), current_user: models.User = Depends(oauth2.get_current_user)):
#     table = db.query(models.Table).filter(models.Table.table_id == table_id).first()
#     if table is None:
#         raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table with id: {table_id} not found.")

#     if reservation_in.reserved_for_time >= reservation_in.end_time:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation start time must be before the end time.")

#     if reservation_in.reserved_for_time < datetime.utcnow():
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot book a table reservation for a past time window.")

#     if reservation_in.total_person > table.capacity:
#         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"people count ({reservation_in.total_person}) exceeds table capacity ({table.capacity}).")


#     overlapping_reservation = db.query(models.TableReservation).filter(models.TableReservation.table_id == table_id, models.TableReservation.cancelled_at == None, reservation_in.reserved_for_time < models.TableReservation.end_time, reservation_in.end_time > models.TableReservation.reserved_for_time).first()

#     if overlapping_reservation:
#         raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This table is already reserved during the requested time slot.")

#     new_reservation = models.TableReservation(table_id=table_id, reserved_by=current_user, total_person=reservation_in.total_person, reserved_for_time=reservation_in.reserved_for_time, end_time=reservation_in.end_time)
    
#     db.add(new_reservation)
#     db.commit()
#     db.refresh(new_reservation)

#     return schemas.success_response(data=new_reservation, message="Table reserved successfully")


@router.get("/availabletables", response_model=schemas.APIResponse[List[schemas.TableResponse]], status_code=status.HTTP_200_OK)
def get_available_tables(start_time: datetime, end_time: datetime, persons: int = 1, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    if persons < 1:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Persons must be at least 1.")
    if start_time >= end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Start time must be before the end time.")
    if start_time < datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot check a past time slot.")

    # tables that already have an active reservation overlapping this slot
    booked_ids = [
        r[0] for r in db.query(models.TableReservation.table_id).filter(
            models.TableReservation.cancelled_at == None,
            start_time < models.TableReservation.end_time,
            end_time > models.TableReservation.reserved_for_time,
        ).all()
    ]

    free_tables = db.query(models.Table).filter(
        models.Table.capacity >= persons,
        ~models.Table.table_id.in_(booked_ids),
    ).order_by(models.Table.capacity, models.Table.table_number).all()

    return schemas.success_response(data=free_tables)


@router.post("/reservetable/{table_id}", response_model=schemas.APIResponse[schemas.ReservationResponse], status_code=status.HTTP_201_CREATED)
def reserve_table(table_id: int, reservation_in: schemas.ReserveTableRequest, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    # with_for_update() locks the table row, so two people booking at the same moment are handled one by one
    table = db.query(models.Table).filter(models.Table.table_id == table_id).with_for_update().first()
    if table is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Table with id: {table_id} not found.")

    if reservation_in.reserved_for_time >= reservation_in.end_time:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Reservation start time must be before the end time.")

    if reservation_in.reserved_for_time < datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot book a table reservation for a past time window.")

    if reservation_in.total_person > table.capacity:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"people count ({reservation_in.total_person}) exceeds table capacity ({table.capacity}).")

    overlapping = db.query(models.TableReservation).filter(
        models.TableReservation.table_id == table_id,
        models.TableReservation.cancelled_at == None,
        reservation_in.reserved_for_time < models.TableReservation.end_time,
        reservation_in.end_time > models.TableReservation.reserved_for_time,
    ).first()
    if overlapping:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="This table is already reserved during the requested time slot.")

    new_reservation = models.TableReservation(
        table_id=table_id, reserved_by=current_user,
        total_person=reservation_in.total_person,
        reserved_for_time=reservation_in.reserved_for_time,
        end_time=reservation_in.end_time,
    )
    db.add(new_reservation)
    db.commit()
    db.refresh(new_reservation)
    return schemas.success_response(data=new_reservation, message="Table reserved successfully")


@router.get("/myreservations", response_model=schemas.APIResponse[List[schemas.ReservationDetailResponse]], status_code=status.HTTP_200_OK)
def my_reservations(db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    rows = db.query(
        models.TableReservation.reservation_id,
        models.TableReservation.table_id,
        models.Table.table_number,
        models.TableReservation.reserved_by,
        models.TableReservation.total_person,
        models.TableReservation.reserved_for_time,
        models.TableReservation.end_time,
        models.TableReservation.cancelled_at,
    ).join(models.Table, models.TableReservation.table_id == models.Table.table_id
    ).filter(models.TableReservation.reserved_by == current_user
    ).order_by(models.TableReservation.reserved_for_time.desc()).all()

    return schemas.success_response(data=rows)


@router.patch("/cancelreservation/{reservation_id}", response_model=schemas.APIResponse[None], status_code=status.HTTP_200_OK)
def cancel_reservation(reservation_id: int, db: Session = Depends(get_db), current_user: int = Depends(oauth2.get_current_user)):
    reservation = db.query(models.TableReservation).filter(
        models.TableReservation.reservation_id == reservation_id,
        models.TableReservation.reserved_by == current_user,
    ).first()
    if reservation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Reservation not found.")

    if reservation.cancelled_at is not None:
        return schemas.success_response(message="Reservation already cancelled")

    if reservation.reserved_for_time <= datetime.now():
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel a reservation that has already started.")

    reservation.cancelled_at = datetime.now()
    db.commit()
    return schemas.success_response(message="Reservation cancelled successfully")