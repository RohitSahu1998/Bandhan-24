# app.py
import os, json, base64
import streamlit as st
import pandas as pd
import uuid
from datetime import datetime
import urllib.parse

from dotenv import load_dotenv; load_dotenv()

import gspread
from oauth2client.service_account import ServiceAccountCredentials

# -------------------------------
# Config / Secrets
# -------------------------------
SCOPE = [
    "https://spreadsheets.google.com/feeds",
    "https://www.googleapis.com/auth/drive",
]

def _get_service_account_info() -> dict:
    """Resolve Google service-account JSON from Streamlit Secrets or env."""
    # 1) Preferred: TOML table in Streamlit secrets
    if "google_credentials" in st.secrets:
        return dict(st.secrets["google_credentials"])

    # 2) Base64 single-line secret (works in Streamlit or locally via .env)
    b64 = st.secrets.get("GOOGLE_CREDS_B64", None) if hasattr(st, "secrets") else None
    b64 = b64 or os.getenv("GOOGLE_CREDS_B64")
    if b64:
        return json.loads(base64.b64decode(b64).decode("utf-8"))

    # 3) Raw JSON string in env (local only)
    raw = os.getenv("GOOGLE_CREDS_JSON")
    if raw:
        return json.loads(raw)

    # 4) Final fallback: local file (dev only)
    if os.path.exists("google-creds.json"):
        with open("google-creds.json", "r", encoding="utf-8") as f:
            return json.load(f)

    raise RuntimeError(
        "No Google credentials found. Add [google_credentials] in Streamlit secrets "
        "or set GOOGLE_CREDS_B64 / GOOGLE_CREDS_JSON / google-creds.json."
        )

def _get_gspread_client():
    info = _get_service_account_info()
    creds = ServiceAccountCredentials.from_json_keyfile_dict(info, SCOPE)
    return gspread.authorize(creds)

def _get_worksheet(client, sheet_id: str, sheet_name: str):
    """Open worksheet by name; create if missing."""
    sh = client.open_by_key(sheet_id)
    try:
        ws = sh.worksheet(sheet_name)
    except gspread.WorksheetNotFound:
        ws = sh.add_worksheet(title=sheet_name, rows=100, cols=20)
    return ws

# Read simple config from secrets/env (with sensible defaults)
YOUR_PHONE = st.secrets.get("YOUR_PHONE", os.getenv("YOUR_PHONE", "9140939949"))
SHEET_ID = st.secrets.get("SHEET_ID", os.getenv("SHEET_ID"))
SHEET_NAME = st.secrets.get("SHEET_NAME", os.getenv("SHEET_NAME", "Orders"))

if not SHEET_ID:
    st.error("SHEET_ID is missing. Add it to Streamlit secrets or .env.")
    st.stop()

# -------------------------------
# Google Sheets helpers
# -------------------------------
def save_orders_to_sheet(order_rows):
    client = _get_gspread_client()
    sheet = _get_worksheet(client, SHEET_ID, SHEET_NAME)

    # Add header if empty
    if not sheet.get_all_values():
        sheet.append_row(list(order_rows[0].keys()))

    # Append rows
    for row in order_rows:
        sheet.append_row(list(row.values()))

def get_user_orders(phone_number):
    client = _get_gspread_client()
    sheet = _get_worksheet(client, SHEET_ID, SHEET_NAME)
    data = sheet.get_all_records()
    if not data:
        return pd.DataFrame(columns=["Order ID","Product","Quantity","Unit Price","Subtotal","Name","Phone","Address","Pincode","Reference By","Timestamp"])
    df = pd.DataFrame(data)
    df["Phone"] = df["Phone"].astype(str).str.strip()
    return df[df["Phone"] == str(phone_number).strip()]

# -------------------------------
# Product Catalog (unchanged)
# -------------------------------
rakhi_catalog = {
    # Previous products
    "IMG_20250707_221915": {
        "title": "Elegant Thread Rakhi",
        "price": 120,
        "discount": 40,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753726754/IMG_20250707_221915.jpg"
    },
    "IMG_20250707_222238": {
        "title": "Traditional Beads Rakhi",
        "price": 120,
        "discount": 40,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753726756/IMG_20250707_222238.jpg"
    },
    "IMG_20250707_222103": {
        "title": "Simple Grace Rakhi",
        "price": 80,
        "discount": 20,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753726757/IMG_20250707_222103.jpg"
    },
    "IMG_20250707_222735": {
        "title": "Royal Red Rakhi",
        "price": 80,
        "discount": 20,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753726761/IMG_20250707_222735.jpg"
    },
    "IMG_20250707_222554": {
        "title": "Pearl Designer Rakhi",
        "price": 120,
        "discount": 40,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753726762/IMG_20250707_222554.jpg"
    },

    # New uploads (dated 2025-07-29)
    "IMG_20250729_114338_1": {
        "title": "Golden Stone Rakhi",
        "price": 150,
        "discount": 45,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777815/WhatsApp%20Image%202025-07-29%20at%2011.43.38_6a4f12e0.jpg"
    },
    "IMG_20250729_114339_1": {
        "title": "Rustic Charm Rakhi",
        "price": 130,
        "discount": 40,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777816/WhatsApp%20Image%202025-07-29%20at%2011.43.39_2f92630f.jpg"
    },
    "IMG_20250729_114339_2": {
        "title": "Twin Pearl Rakhi",
        "price": 110,
        "discount": 30,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777817/WhatsApp%20Image%202025-07-29%20at%2011.43.39_032298f3.jpg"
    },
    "IMG_20250729_114338_2": {
        "title": "Red Feather Rakhi",
        "price": 140,
        "discount": 40,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777818/WhatsApp%20Image%202025-07-29%20at%2011.43.38_a3cbeee5.jpg"
    },
    "IMG_20250729_114339_3": {
        "title": "Antique Emblem Rakhi",
        "price": 135,
        "discount": 40,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777819/WhatsApp%20Image%202025-07-29%20at%2011.43.39_a760ab12.jpg"
    },
    "IMG_20250729_114340_1": {
        "title": "Threaded Diamond Rakhi",
        "price": 160,
        "discount": 50,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777820/WhatsApp%20Image%202025-07-29%20at%2011.43.40_5451bc86.jpg"
    },
    "IMG_20250729_114340_2": {
        "title": "Zari Pearl Rakhi",
        "price": 115,
        "discount": 30,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777821/WhatsApp%20Image%202025-07-29%20at%2011.43.40_29d3c9dc.jpg"
    },
    "IMG_20250729_114341_1": {
        "title": "Elegant Floral Rakhi",
        "price": 125,
        "discount": 30,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777822/WhatsApp%20Image%202025-07-29%20at%2011.43.41_c90ca9c0.jpg"
    },
    "IMG_20250729_114340_3": {
        "title": "Red Gemstone Rakhi",
        "price": 145,
        "discount": 40,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777823/WhatsApp%20Image%202025-07-29%20at%2011.43.40_90609f14.jpg"
    },
    "IMG_20250729_114341_2": {
        "title": "Classic Rudraksha Rakhi",
        "price": 95,
        "discount": 20,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777824/WhatsApp%20Image%202025-07-29%20at%2011.43.41_50feea60.jpg"
    },
    "IMG_20250729_114342_1": {
        "title": "Minimal Designer Rakhi",
        "price": 105,
        "discount": 25,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777825/WhatsApp%20Image%202025-07-29%20at%2011.43.42_ab1eb195.jpg"
    },
    "IMG_20250729_114342_2": {
        "title": "Silver Stone Rakhi",
        "price": 135,
        "discount": 40,
        "image": "https://res.cloudinary.com/dx35lfv49/image/upload/v1753777826/WhatsApp%20Image%202025-07-29%20at%2011.43.42_ea071a48.jpg"
    },
}
rakhi_catalog = dict(sorted(rakhi_catalog.items(), key=lambda x: -x[1]["discount"]))

# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="Saaurabh Collections", layout="wide")

# Simple login with phone
if "user_phone" not in st.session_state:
    with st.form("login_form"):
        st.title("🔐 Login to Saaurabh Collections")
        user_phone = st.text_input("Enter your phone number")
        login_submit = st.form_submit_button("Login")
    if login_submit:
        if user_phone:
            st.session_state.user_phone = str(user_phone).strip()
            st.rerun()
        else:
            st.warning("📱 Please enter a valid phone number.")
    st.stop()

st.sidebar.markdown(f"📱 Logged in as: `{st.session_state.user_phone}`")
if st.sidebar.button("🔓 Logout"):
    st.session_state.clear()
    st.rerun()

selected_tab = st.sidebar.radio("Navigate", ["🛍️ Shop", "📦 My Orders"])

if "cart" not in st.session_state:
    st.session_state.cart = {}

if selected_tab == "🛍️ Shop":
    st.title("🛍️ Saaurabh Collections")
    cols = st.columns(3)

    for i, (key, item) in enumerate(rakhi_catalog.items()):
        with cols[i % 3]:
            final_price = int(item["price"] * (1 - item["discount"] / 100))
            st.image(item["image"], use_column_width=True)
            st.markdown(f"**{item['title']}**")
            st.markdown(f"~~₹{item['price']}~~ 🎉 **{item['discount']}% OFF** → ₹{final_price}")
            qty = st.number_input(f"Qty for {key}", min_value=1, max_value=10, value=1, key=f"qty_{key}")
            if st.button("🛒 Add to Cart", key=f"add_{key}"):
                if key in st.session_state.cart:
                    st.session_state.cart[key]["quantity"] += qty
                else:
                    st.session_state.cart[key] = {
                        "title": item["title"],
                        "price": final_price,
                        "quantity": qty
                    }
                st.success(f"Added {qty} x {item['title']} to cart")

    if st.session_state.cart:
        st.markdown("---")
        st.header("🧾 Your Cart")
        total_price = 0
        for pid, details in st.session_state.cart.items():
            subtotal = details["price"] * details["quantity"]
            total_price += subtotal
            st.write(f"{details['title']} × {details['quantity']} = ₹{subtotal}")
        st.write(f"### Grand Total: ₹{total_price}")

        with st.form("checkout_form"):
            st.subheader("📦 Checkout")
            name = st.text_input("Your Name")
            address = st.text_area("Delivery Address")
            pincode = st.text_input("Pincode")
            reference_by = st.text_input("Reference By")
            submit = st.form_submit_button("Place Order")

        if submit:
            if not name or not address or not pincode:
                st.error("Please complete all fields.")
            else:
                order_id = str(uuid.uuid4())[:8]
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                phone_number = str(st.session_state.user_phone).strip()
                orders = []
                for pid, details in st.session_state.cart.items():
                    orders.append({
                        "Order ID": order_id,
                        "Product": details["title"],
                        "Quantity": details["quantity"],
                        "Unit Price": details["price"],
                        "Subtotal": details["price"] * details["quantity"],
                        "Name": name,
                        "Phone": phone_number,
                        "Address": address,
                        "Pincode": pincode,
                        "Reference By": reference_by,
                        "Timestamp": timestamp
                    })

                save_orders_to_sheet(orders)

                msg = f"*Order ID:* {order_id}\n*Name:* {name}\n*Phone:* {phone_number}\n*Pincode:* {pincode}\n*Address:* {address}\n"
                if reference_by:
                    msg += f"*Reference By:* {reference_by}\n"
                for d in orders:
                    msg += f"- {d['Product']} × {d['Quantity']} = ₹{d['Subtotal']}\n"
                msg += f"\n*Total:* ₹{total_price}"
                wa_link = f"https://wa.me/{YOUR_PHONE}?text={urllib.parse.quote(msg)}"

                st.success("✅ Order placed!")
                st.markdown(f"[📲 Send order via WhatsApp]({wa_link})", unsafe_allow_html=True)
                st.session_state.cart = {}
    else:
        st.info("🛒 Your cart is empty.")

elif selected_tab == "📦 My Orders":
    st.title("📦 Your Orders")
    phone = str(st.session_state.user_phone).strip()
    df = get_user_orders(phone)

    if df.empty:
        st.info("No orders found.")
    else:
        st.success(f"Total orders: {df['Order ID'].nunique()} | Items: {len(df)}")
        grouped = df.groupby("Order ID")
        for oid, group in grouped:
            st.markdown(f"### 🧾 Order ID: `{oid}`")
            st.markdown(
                f"**Name:** {group.iloc[0]['Name']} | **Pincode:** {group.iloc[0]['Pincode']} | **Address:** {group.iloc[0]['Address']}"
            )
            if str(group.iloc[0].get("Reference By", "")).strip():
                st.markdown(f"**Reference By:** {group.iloc[0]['Reference By']}")
            st.write(group[["Product", "Quantity", "Unit Price", "Subtotal", "Timestamp"]])
