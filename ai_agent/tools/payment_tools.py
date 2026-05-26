"""
Tool sinh link thanh toán VNPay.
Tái sử dụng logic VNPay từ app.py.
"""
import hashlib
import hmac
import urllib.parse
from datetime import datetime


# Cấu hình VNPay Sandbox (lấy từ app.py)
VNPAY_URL = 'https://sandbox.vnpayment.vn/paymentv2/vpcpay.html'
VNP_TMN_CODE = 'LO7SVBM7'
VNP_HASH_SECRET = 'VTPFHSF8FKMT1YBIPR8SWTNB3FLQNRVP'


def build_vnpay_query_and_hash(vnp_params: dict, secret_key: str) -> tuple[str, str]:
    """Tạo chuỗi query và hash cho VNPay."""
    sorted_params = sorted(vnp_params.items())
    query_string = urllib.parse.urlencode(sorted_params)
    hash_data = '&'.join([f"{k}={urllib.parse.quote_plus(str(v))}" for k, v in sorted_params])
    vnp_secure_hash = hmac.new(
        secret_key.encode('utf-8'),
        hash_data.encode('utf-8'),
        hashlib.sha512
    ).hexdigest()
    return query_string, vnp_secure_hash


def generate_payment_url(booking_id: int, amount: int, 
                         return_url: str = "http://127.0.0.1:5000/vnpay_return") -> str:
    """
    Sinh URL thanh toán VNPay cho một booking.
    
    Args:
        booking_id: ID booking cần thanh toán.
        amount: Số tiền (VND).
        return_url: URL callback sau khi thanh toán.
    
    Returns:
        URL thanh toán VNPay đầy đủ.
    """
    now = datetime.now()
    txn_ref = f"{booking_id}_{now.strftime('%Y%m%d%H%M%S')}"

    vnp_params = {
        'vnp_Version': '2.1.0',
        'vnp_Command': 'pay',
        'vnp_TmnCode': VNP_TMN_CODE,
        'vnp_Amount': str(int(amount) * 100),  # VNPay yêu cầu nhân 100
        'vnp_CurrCode': 'VND',
        'vnp_TxnRef': txn_ref,
        'vnp_OrderInfo': f'Thanh toan dat phong #{booking_id}',
        'vnp_OrderType': 'billpayment',
        'vnp_Locale': 'vn',
        'vnp_ReturnUrl': return_url,
        'vnp_IpAddr': '127.0.0.1',
        'vnp_CreateDate': now.strftime('%Y%m%d%H%M%S'),
    }

    query_string, vnp_secure_hash = build_vnpay_query_and_hash(vnp_params, VNP_HASH_SECRET)
    payment_url = f"{VNPAY_URL}?{query_string}&vnp_SecureHash={vnp_secure_hash}"

    return payment_url
