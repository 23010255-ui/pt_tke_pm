"""
Tool tìm khách sạn gần vị trí hiện tại của người dùng.
Sử dụng công thức Haversine để tính khoảng cách giữa 2 tọa độ GPS.
"""
import sys
import os
import math

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy').setLevel(logging.WARNING)

from config import get_db
from models import Hotel, HotelLocation, Room


def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Tính khoảng cách (km) giữa 2 điểm trên Trái Đất bằng công thức Haversine.
    """
    R = 6371  # Bán kính Trái Đất (km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c


def find_nearest_hotels(user_lat: float, user_lng: float, top_n: int = 3) -> list[dict]:
    """
    Tìm top N khách sạn gần nhất với vị trí người dùng.
    
    Args:
        user_lat: Vĩ độ của người dùng.
        user_lng: Kinh độ của người dùng.
        top_n: Số lượng khách sạn trả về (mặc định 3).
    
    Returns:
        Danh sách dict chứa thông tin khách sạn + khoảng cách.
    """
    db = get_db()
    locations = db.query(HotelLocation).all()

    if not locations:
        return [{"error": "Chưa có dữ liệu vị trí khách sạn trong hệ thống."}]

    # Tính khoảng cách cho từng khách sạn
    hotels_with_distance = []
    for loc in locations:
        if loc.latitude is None or loc.longitude is None:
            continue

        distance = haversine(user_lat, user_lng, loc.latitude, loc.longitude)
        hotel = db.query(Hotel).filter(Hotel.hotel_id == loc.hotel_id).first()

        if not hotel:
            continue

        # Lấy giá phòng rẻ nhất
        min_room = db.query(Room).filter(
            Room.hotel_id == hotel.hotel_id,
            Room.availableRooms > 0
        ).order_by(Room.price.asc()).first()

        hotels_with_distance.append({
            "hotel_id": hotel.hotel_id,
            "hotel_name": hotel.hotel_name,
            "address": hotel.address_hotel,
            "phone": hotel.tel,
            "rating": hotel.rating,
            "description": hotel.descriptions,
            "latitude": loc.latitude,
            "longitude": loc.longitude,
            "distance_km": round(distance, 2),
            "min_price": min_room.price if min_room else None,
            "min_room_type": min_room.room_type if min_room else None,
        })

    # Sắp xếp theo khoảng cách tăng dần
    hotels_with_distance.sort(key=lambda x: x["distance_km"])

    return hotels_with_distance[:top_n]
