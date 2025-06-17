import os
from flask import Flask, request, render_template_string, jsonify
import razorpay
import shortuuid # For generating unique receipt and token ids
import hmac
import hashlib

app = Flask(__name__)

# Replace with your actual Razorpay Key ID and Key Secret
RAZORPAY_KEY_ID = os.environ.get('RAZORPAY_KEY_ID', 'YOUR_KEY_ID')
RAZORPAY_KEY_SECRET = os.environ.get('RAZORPAY_KEY_SECRET', 'YOUR_KEY_SECRET')

# In-memory store for order IDs and payment status
# Structure: {order_id: {'status': 'created'/'successful'/'failed', 'payment_id': 'razorpay_pid', 'token': 'game_token', 'token_used': False}}
payment_orders = {}

# Initialize Razorpay client
client = razorpay.Client(auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET))

@app.route('/')
def hello():
    return "Payment service is running!"

@app.route('/pay', methods=['GET'])
def pay():
    amount_in_rs = 1
    amount_in_paise = amount_in_rs * 100
    currency = 'INR'
    receipt_id = f"receipt_{shortuuid.uuid()}"

    try:
        order_data = {
            'amount': amount_in_paise,
            'currency': currency,
            'receipt': receipt_id,
            'payment_capture': '1'
        }
        order = client.order.create(data=order_data)
        order_id = order['id']

        # Initialize token_used to False
        payment_orders[order_id] = {'status': 'created', 'payment_id': None, 'token': None, 'token_used': False}

        callback_url = request.url_root + "callback"

        checkout_html = f"""
        <html>
        <head>
            <title>Razorpay Payment</title>
            <script src="https://checkout.razorpay.com/v1/checkout.js"></script>
        </head>
        <body>
            <h1>Processing payment of {amount_in_rs} INR...</h1>
            <script>
            var options = {{
                "key": "{RAZORPAY_KEY_ID}",
                "amount": "{order['amount']}",
                "currency": "{order['currency']}",
                "name": "Guess The Number Game",
                "description": "Payment for playing the game",
                "image": "https://via.placeholder.com/150?text=Game+Logo",
                "order_id": "{order_id}",
                "callback_url": "{callback_url}",
                "prefill": {{
                    "name": "Test User",
                    "email": "test.user@example.com",
                    "contact": "9999999999"
                }},
                "notes": {{
                    "game_session_id": "SESSION12345"
                }},
                "theme": {{
                    "color": "#3399cc"
                }}
            }};
            var rzp1 = new Razorpay(options);
            rzp1.on('payment.failed', function (response){{
                alert("Payment Failed: " + response.error.description + ". Code: " + response.error.code + ". Source: " + response.error.source);
            }});
            rzp1.open();
            </script>
            <p>If the payment window doesn't open, please ensure pop-ups are enabled and refresh.</p>
        </body>
        </html>
        """
        return render_template_string(checkout_html)

    except Exception as e:
        app.logger.error(f"Error creating Razorpay order: {e}")
        return f"Error processing payment: {str(e)}", 500

@app.route('/callback', methods=['POST'])
def callback():
    try:
        data = request.form
        razorpay_payment_id = data.get('razorpay_payment_id')
        razorpay_order_id = data.get('razorpay_order_id')
        razorpay_signature = data.get('razorpay_signature')

        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return "Invalid callback: Missing data", 400

        if razorpay_order_id not in payment_orders:
            app.logger.error(f"Callback for unknown order_id: {razorpay_order_id}")
            return "Invalid order ID", 400

        msg = f"{razorpay_order_id}|{razorpay_payment_id}"
        expected_signature = hmac.new(
            bytes(RAZORPAY_KEY_SECRET, 'utf-8'),
            bytes(msg, 'utf-8'),
            hashlib.sha256
        ).hexdigest()

        if hmac.compare_digest(expected_signature, razorpay_signature):
            game_token = f"TOKEN_{shortuuid.uuid()}"
            payment_orders[razorpay_order_id].update({
                'status': 'successful',
                'payment_id': razorpay_payment_id,
                'token': game_token,
                'token_used': False # Explicitly set to False on successful payment
            })

            success_html = f"""
            <html>
            <head><title>Payment Successful</title></head>
            <body>
                <h1>Payment Successful!</h1>
                <p>Your Order ID: {razorpay_order_id}</p>
                <p>Your Payment ID: {razorpay_payment_id}</p>
                <p><strong>Use this token to start the game:</strong></p>
                <h2 style="color:green;">{game_token}</h2>
                <p>Please copy this token and paste it into the game.</p>
            </body>
            </html>
            """
            return render_template_string(success_html)
        else:
            payment_orders[razorpay_order_id].update({
                'status': 'failed',
                'payment_id': razorpay_payment_id
            })
            app.logger.error(f"Signature verification failed for order_id: {razorpay_order_id}")
            return "Payment verification failed. Signature mismatch.", 400

    except Exception as e:
        app.logger.error(f"Error in callback: {e}")
        return f"Error processing callback: {str(e)}", 500

@app.route('/verify_token', methods=['GET'])
def verify_token():
    token_to_verify = request.args.get('token')
    if not token_to_verify:
        return jsonify({'status': 'error', 'message': 'Token not provided'}), 400

    found_order_id = None
    for order_id, details in payment_orders.items():
        if details.get('token') == token_to_verify:
            found_order_id = order_id
            break

    if found_order_id:
        order_details = payment_orders[found_order_id]
        if order_details['status'] == 'successful':
            if not order_details.get('token_used', False): # Check if 'token_used' exists and is False
                order_details['token_used'] = True # Mark token as used
                return jsonify({'status': 'valid', 'order_id': found_order_id})
            else:
                return jsonify({'status': 'invalid', 'message': 'Token already used'}), 403
        else:
            return jsonify({'status': 'invalid', 'message': 'Token associated with a non-successful payment'}), 403
    else:
        return jsonify({'status': 'invalid', 'message': 'Token not found'}), 404


if __name__ == '__main__':
    try:
        import flask
        import razorpay
        import shortuuid
        # hmac and hashlib are standard, no need to pip install explicitly
    except ImportError:
        print("Attempting to install missing packages (Flask, razorpay, shortuuid)...")
        os.system("pip install Flask razorpay shortuuid")

    if RAZORPAY_KEY_ID == 'YOUR_KEY_ID' or RAZORPAY_KEY_SECRET == 'YOUR_KEY_SECRET':
        print("WARNING: Razorpay API keys are set to placeholders.")
        print("Please set RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET environment variables or update app.py.")

    app.run(debug=True, port=5001, host='0.0.0.0')
