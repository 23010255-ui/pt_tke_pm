"""
Booking Node: Xử lý logic đặt phòng khách sạn.
- Thu thập thông tin (check-in, check-out, guests...)
- Truy vấn DB tìm phòng trống
- Tạo booking + sinh link thanh toán VNPay
"""
import os
import re
import json
from google import genai
from langchain_core.messages import AIMessage
from ai_agent.state import BookingState
from ai_agent.prompts import BOOKING_PROMPT
from ai_agent.tools.db_tools import search_available_rooms, create_booking_record
from ai_agent.tools.payment_tools import generate_payment_url


def _extract_booking_info(state: BookingState, api_key: str) -> dict:
    """
    Dùng LLM để trích xuất thông tin đặt phòng từ toàn bộ lịch sử hội thoại.
    Trả về dict với các key: check_in, check_out, guests, room_type, hotel_name.
    """
    client = genai.Client(api_key=api_key)

    # Gom lịch sử hội thoại thành chuỗi
    history = "\n".join([
        f"{'User' if msg.type == 'human' else 'Bot'}: {msg.content}"
        for msg in state["messages"]
    ])

    extract_prompt = f"""Bạn là bộ trích xuất thông tin đặt phòng khách sạn.

HÃY ĐỌC KỸ lịch sử hội thoại bên dưới và trích xuất thông tin theo quy tắc:
1. Khi Bot HỎI về ngày check-in và User TRẢ LỜI một ngày → đó là check_in
2. Khi Bot HỎI về ngày check-out và User TRẢ LỜI một ngày → đó là check_out  
3. Ngày có thể ở dạng DD/MM/YYYY hoặc YYYY-MM-DD → luôn chuyển về YYYY-MM-DD
4. Nếu thông tin chưa được cung cấp, trả về null

Trả về JSON thuần túy (không markdown, không giải thích):
{{"check_in": "YYYY-MM-DD hoặc null", "check_out": "YYYY-MM-DD hoặc null", "guests": "số nguyên hoặc null", "room_type": "chuỗi hoặc null", "hotel_name": "chuỗi hoặc null"}}

Lịch sử hội thoại:
{history}"""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=extract_prompt
    )

    # Parse JSON từ response
    text = response.text.strip()
    # Loại bỏ markdown code block nếu có
    text = re.sub(r'^```json\s*', '', text)
    text = re.sub(r'\s*```$', '', text)

    try:
        info = json.loads(text)
    except json.JSONDecodeError:
        info = {}

    return info


def booking_node(state: BookingState) -> dict:
    """
    Node chính xử lý luồng đặt phòng.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    # Bước 1: Trích xuất thông tin từ hội thoại
    info = _extract_booking_info(state, api_key)
    check_in = info.get("check_in") or state.get("check_in")
    check_out = info.get("check_out") or state.get("check_out")
    guests = info.get("guests") or state.get("guests")
    room_type = info.get("room_type") or state.get("room_type")
    hotel_name = info.get("hotel_name") or state.get("hotel_name")

    updates = {
        "check_in": check_in,
        "check_out": check_out,
        "guests": guests,
        "room_type": room_type,
        "hotel_name": hotel_name,
    }

    # Bước 2: Kiểm tra đủ thông tin tối thiểu (check_in + check_out) chưa
    if not check_in or not check_out:
        # Chưa đủ → gọi LLM hỏi lại
        prompt = BOOKING_PROMPT.format(
            check_in=check_in or "chưa có",
            check_out=check_out or "chưa có",
            guests=guests or "chưa có",
            room_type=room_type or "chưa có",
            hotel_name=hotel_name or "chưa có"
        )
        history = "\n".join([f"{'User' if m.type == 'human' else 'Bot'}: {m.content}" for m in state["messages"]])
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=f"{prompt}\n\nLịch sử:\n{history}"
        )
        updates["messages"] = [AIMessage(content=response.text)]
        return updates

    # Bước 3: Đủ thông tin → Tìm phòng trống
    rooms = search_available_rooms(
        check_in=check_in,
        check_out=check_out,
        guests=guests or 1,
        room_type=room_type,
        hotel_name=hotel_name
    )

    if rooms and "error" in rooms[0]:
        updates["messages"] = [AIMessage(content=f"❌ {rooms[0]['error']}")]
        return updates

    updates["suggested_rooms"] = rooms

    # Bước 4: Hiển thị danh sách phòng cho khách
    rooms_text = "🏨 **Các phòng trống phù hợp:**\n\n"
    for i, r in enumerate(rooms[:5], 1):  # Giới hạn 5 kết quả
        services = ", ".join(r["services"]) if r["services"] else "Không có"
        rooms_text += (
            f"**{i}. {r['hotel_name']}** - {r['room_type']}\n"
            f"   📍 {r['hotel_address']}\n"
            f"   ⭐ {r['hotel_rating'] or 'N/A'} | "
            f"💰 {r['price_per_night']:,} VND/đêm × {r['nights']} đêm = **{r['total_price']:,} VND**\n"
            f"   🛎️ Dịch vụ: {services}\n"
            f"   🔑 Còn {r['available_rooms']} phòng trống (Room ID: {r['room_id']})\n\n"
        )
    rooms_text += "Bạn muốn đặt phòng nào? Hãy cho tôi biết **Room ID** hoặc **số thứ tự**."

    updates["messages"] = [AIMessage(content=rooms_text)]
    return updates


def confirm_booking_node(state: BookingState) -> dict:
    """
    Node xác nhận và tạo booking khi người dùng chọn phòng.
    Được gọi khi đã có suggested_rooms và người dùng xác nhận.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    user_id = state.get("user_id")
    if not user_id:
        return {"messages": [AIMessage(content="⚠️ Bạn cần đăng nhập để đặt phòng.")]}

    last_message = state["messages"][-1].content
    suggested = state.get("suggested_rooms", [])

    if not suggested:
        return {"messages": [AIMessage(content="Chưa có phòng nào được gợi ý. Hãy cho tôi biết ngày bạn muốn đặt.")]}

    # Dùng LLM để trích xuất room_id từ lựa chọn của người dùng
    room_ids = [str(r["room_id"]) for r in suggested]
    extract_prompt = f"""Người dùng nói: "{last_message}"
Danh sách Room ID hợp lệ: {room_ids}
Hãy trả về CHỈ DUY NHẤT room_id mà người dùng muốn chọn. Nếu không rõ, trả về "unclear"."""

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=extract_prompt
    )
    chosen = response.text.strip()

    if chosen == "unclear" or chosen not in room_ids:
        return {"messages": [AIMessage(content="Tôi chưa hiểu bạn chọn phòng nào. Vui lòng cho biết **Room ID** hoặc **số thứ tự** phòng bạn muốn đặt.")]}

    room_id = int(chosen)
    check_in = state["check_in"]
    check_out = state["check_out"]

    # Tạo booking
    result = create_booking_record(
        user_id=user_id,
        room_id=room_id,
        check_in=check_in,
        check_out=check_out
    )

    if "error" in result:
        return {"messages": [AIMessage(content=f"❌ {result['error']}")]}

    # Sinh link thanh toán VNPay
    payment_url = generate_payment_url(
        booking_id=result["booking_id"],
        amount=int(result["total_price"])
    )

    msg = (
        f"✅ **Đặt phòng thành công!**\n\n"
        f"📋 Mã booking: **#{result['booking_id']}**\n"
        f"🏨 {result['hotel_name']} - {result['room_type']}\n"
        f"📅 {result['check_in']} → {result['check_out']} ({result['nights']} đêm)\n"
        f"💰 Tổng tiền: **{result['total_price']:,} VND**\n\n"
        f"💳 [Thanh toán qua VNPay]({payment_url})\n\n"
        f"Vui lòng thanh toán trong vòng 15 phút để giữ phòng."
    )

    return {
        "messages": [AIMessage(content=msg)],
        "booking_id": result["booking_id"],
        "payment_url": payment_url,
        "suggested_rooms": None  # Reset
    }
