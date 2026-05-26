"""
Tools truy vấn cơ sở dữ liệu.
Tái sử dụng SQLAlchemy session từ config.py và models từ models.py.
"""
import sys
import os

# Thêm thư mục gốc của dự án vào sys.path để import được models, config, utils
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# Tắt SQL log output để không spam terminal khi chatbot chạy
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

from datetime import datetime
from config import get_db
from models import Hotel, Room, Booking, Payment, Service


def search_available_rooms(check_in: str, check_out: str, guests: int = 1,
                           room_type: str = None, hotel_name: str = None) -> list[dict]:
    """
    Tìm phòng trống dựa trên ngày check-in/out, số khách, loại phòng, tên khách sạn.
    Trả về danh sách dict chứa thông tin phòng.
    """
    db = get_db()
    try:
        check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return [{"error": "Định dạng ngày không hợp lệ. Vui lòng dùng YYYY-MM-DD."}]

    if check_in_dt >= check_out_dt:
        return [{"error": "Ngày check-out phải sau ngày check-in."}]

    # Query phòng có số phòng trống > 0
    query = db.query(Room).join(Hotel).filter(Room.availableRooms > 0)

    if room_type:
        query = query.filter(Room.room_type.ilike(f"%{room_type}%"))
    if hotel_name:
        query = query.filter(Hotel.hotel_name.ilike(f"%{hotel_name}%"))

    rooms = query.all()

    # Lọc bỏ các phòng đã bị booking trùng ngày
    available = []
    for room in rooms:
        conflicting = db.query(Booking).filter(
            Booking.room_id == room.room_id,
            Booking.status != 'failed',
            Booking.check_in < check_out_dt,
            Booking.check_out > check_in_dt
        ).count()

        # Nếu số booking trùng lịch ít hơn số phòng trống thì vẫn còn chỗ
        if conflicting < (room.availableRooms or 0):
            # Lấy danh sách dịch vụ
            services = db.query(Service).filter(Service.room_id == room.room_id).all()
            service_names = [s.serviceName for s in services]

            nights = (check_out_dt - check_in_dt).days
            total_price = room.price * nights

            available.append({
                "room_id": room.room_id,
                "room_type": room.room_type,
                "hotel_name": room.hotel.hotel_name,
                "hotel_address": room.hotel.address_hotel,
                "hotel_rating": room.hotel.rating,
                "price_per_night": room.price,
                "total_price": total_price,
                "nights": nights,
                "available_rooms": room.availableRooms - conflicting,
                "services": service_names
            })

    if not available:
        return [{"error": "Không tìm thấy phòng trống phù hợp với yêu cầu của bạn."}]

    return available


def create_booking_record(user_id: int, room_id: int, check_in: str,
                          check_out: str, num_rooms: int = 1) -> dict:
    """
    Tạo bản ghi Booking mới trong cơ sở dữ liệu.
    Trả về dict chứa thông tin booking đã tạo.
    """
    db = get_db()
    try:
        check_in_dt = datetime.strptime(check_in, "%Y-%m-%d")
        check_out_dt = datetime.strptime(check_out, "%Y-%m-%d")
    except ValueError:
        return {"error": "Định dạng ngày không hợp lệ."}

    room = db.query(Room).filter(Room.room_id == room_id).first()
    if not room:
        return {"error": f"Không tìm thấy phòng với ID {room_id}."}

    if room.availableRooms is None or room.availableRooms < num_rooms:
        return {"error": "Phòng này không còn đủ chỗ."}

    nights = (check_out_dt - check_in_dt).days
    total_price = room.price * nights * num_rooms

    booking = Booking(
        user_id=user_id,
        room_id=room_id,
        check_in=check_in_dt,
        check_out=check_out_dt,
        total_price=total_price,
        num_rooms=num_rooms,
        status='pending'
    )
    db.add(booking)
    room.availableRooms -= num_rooms
    db.commit()
    db.refresh(booking)

    return {
        "booking_id": booking.booking_id,
        "room_type": room.room_type,
        "hotel_name": room.hotel.hotel_name,
        "check_in": check_in,
        "check_out": check_out,
        "nights": nights,
        "total_price": total_price,
        "status": booking.status
    }


def get_booking_info(booking_id: int) -> dict:
    """Tra cứu thông tin booking theo ID."""
    db = get_db()
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        return {"error": f"Không tìm thấy booking với mã #{booking_id}."}

    result = {
        "booking_id": booking.booking_id,
        "room_type": booking.room.room_type,
        "hotel_name": booking.room.hotel.hotel_name,
        "check_in": booking.check_in.strftime("%Y-%m-%d"),
        "check_out": booking.check_out.strftime("%Y-%m-%d"),
        "total_price": booking.total_price,
        "num_rooms": booking.num_rooms,
        "status": booking.status,
        "created_at": booking.created_at.strftime("%Y-%m-%d %H:%M")
    }

    # Nếu có thanh toán
    if booking.payment:
        result["payment_status"] = booking.payment.payment_status
        result["payment_method"] = booking.payment.payment_method

    return result


def cancel_booking(booking_id: int, user_id: int) -> dict:
    """Hủy booking nếu trạng thái là pending và thuộc về đúng user."""
    db = get_db()
    booking = db.query(Booking).filter(Booking.booking_id == booking_id).first()
    if not booking:
        return {"error": f"Không tìm thấy booking với mã #{booking_id}."}

    if booking.user_id != user_id:
        return {"error": "Bạn không có quyền hủy booking này."}

    if booking.status != 'pending':
        return {"error": f"Không thể hủy booking ở trạng thái '{booking.status}'. Chỉ có thể hủy khi đang 'pending'."}

    booking.status = 'failed'
    # Trả lại phòng
    room = db.query(Room).filter(Room.room_id == booking.room_id).first()
    if room:
        room.availableRooms += booking.num_rooms
    db.commit()

    return {
        "message": f"Đã hủy thành công booking #{booking_id}.",
        "booking_id": booking_id,
        "status": "failed"
    }
