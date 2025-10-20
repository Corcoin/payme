import os
import logging
from flask import Flask, render_template, request, jsonify
import requests
from datetime import datetime

app = Flask(__name__)

# -------------------
# CONFIG
# -------------------
PAYPAL_CLIENT_ID = "AX9E5Vt7wXq7dvD-40MMIJkDy4NPNQ_R0nHclnYbJseg9rm_T71_kyDR0vZJcYOSTAY6CFUDqciocQ92"
PAYPAL_SECRET = "ECHvAzGMZtViddQBAl_rMAT42v6FMuYh8ogVBWxYWRyviAl6oOgG2IOGq6huOGb4fQ9mTA3b9a0Xfanz"
PAYPAL_API = "https://api-m.paypal.com" # change to live for production

# Enable logging
logging.basicConfig(level=logging.INFO)

# -------------------
# HELPERS
# -------------------
def get_access_token():
    """Get PayPal OAuth2 token."""
    res = requests.post(
        f"{PAYPAL_API}/v1/oauth2/token",
        auth=(PAYPAL_CLIENT_ID, PAYPAL_SECRET),
        headers={"Accept": "application/json"},
        data={"grant_type": "client_credentials"},
        timeout=10
    )
    res.raise_for_status()
    return res.json()["access_token"]

def send_payout(recipient_email, amount):
    """Send 90% of amount to recipient via PayPal Payouts."""
    token = get_access_token()
    payout_amount = round(float(amount) * 0.90, 2)  # keep 10% platform fee

    payload = {
        "sender_batch_header": {
            "sender_batch_id": os.urandom(8).hex(),
            "email_subject": "You received funds!",
            "email_message": "Payout from our platform"
        },
        "items": [{
            "recipient_type": "EMAIL",
            "amount": {"value": f"{payout_amount:.2f}", "currency": "USD"},
            "receiver": recipient_email,
            "note": "Payout after 10% platform fee deduction",
            "sender_item_id": os.urandom(6).hex()
        }]
    }

    res = requests.post(
        f"{PAYPAL_API}/v1/payments/payouts",
        headers={"Content-Type": "application/json", "Authorization": f"Bearer {token}"},
        json=payload,
        timeout=10
    )
    res.raise_for_status()
    return res.json()

# -------------------
# ROUTES
# -------------------
@app.route("/")
def home():
    return render_template("index.html", client_id=PAYPAL_CLIENT_ID)

@app.route("/log-payment", methods=["POST"])
def log_payment():
    """Logs payment and sends payout automatically."""
    data = request.get_json()
    recipient_email = data.get("recipient")
    amount = float(data.get("amount", 1.00))
    transaction_id = data.get("transaction_id", "N/A")

    logging.info(f"{datetime.now()} | Payment received: ${amount} | Transaction ID: {transaction_id} | Recipient: {recipient_email}")

    try:
        payout_result = send_payout(recipient_email, amount)
        logging.info(f"Payout sent: {payout_result}")
        return jsonify({"success": True, "payout": payout_result})
    except Exception as e:
        logging.error(f"Payout failed: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
