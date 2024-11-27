from flask import Flask, render_template, request, redirect, url_for
import json
import requests
import os
from datetime import datetime

app = Flask(__name__)
app.config['DEBUG'] = False

# File path for storing user data (adjust for deployment)
DATA_FILE = "data.json"

# Telegram bot token from environment variable
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_API_URL = f"https://api.telegram.org/bot{BOT_TOKEN}"

# Load JSON data
def load_data():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {"users": [], "link": ""}

# Save JSON data
def save_data(data):
    try:
        with open(DATA_FILE, "w") as f:
            json.dump(data, f, indent=4)
    except Exception as e:
        print(f"Error saving data: {e}")

# Notify user via bot
def notify_user(chat_id, message):
    try:
        if chat_id:
            requests.post(f"{BOT_API_URL}/sendMessage", json={"chat_id": chat_id, "text": message})
    except Exception as e:
        print(f"Error notifying user: {e}")

# Admin panel route
@app.route("/")
def admin_panel():
    data = load_data()
    return render_template("admin.html", users=data["users"])

# Update user status
@app.route("/update_status", methods=["POST"])
def update_status():
    whatsapp = request.form.get("whatsapp")
    status = request.form.get("status")

    if status:
        data = load_data()
        for user in data["users"]:
            if user["whatsapp"] == whatsapp:
                user["status"] = status
                if status == "verified":
                    user["remaining_days"] = 0  # Set default days to 0
                    user["last_verified"] = datetime.now().isoformat()
                save_data(data)

                # Notify user based on status
                if status == "verified":
                    message = (
                        f"🎉 Dear {user['name']}, your profile has been verified successfully. "
                        f"Now you are a premium user with 0 days remaining. Please renew to enjoy the benefits!"
                    )
                elif status == "rejected":
                    message = f"❌ Dear {user['name']}, your profile has been rejected. Please try again with a different WhatsApp number."

                notify_user(user.get("chat_id"), message)
                break

    return redirect(url_for("admin_panel"))

# Delete user
@app.route("/delete_user", methods=["POST"])
def delete_user():
    whatsapp = request.form["whatsapp"]
    data = load_data()

    for user in data["users"]:
        if user["whatsapp"] == whatsapp:
            message = f"❌ Dear {user['name']}, your profile has been deleted by admin. For more details, contact admin."
            notify_user(user.get("chat_id"), message)
            break

    data["users"] = [user for user in data["users"] if user["whatsapp"] != whatsapp]
    save_data(data)
    return redirect(url_for("admin_panel"))

# Send link to verified users
@app.route("/send_link", methods=["POST"])
def send_link():
    link = request.form.get("link")
    data = load_data()
    data["link"] = link  # Save the new link
    save_data(data)

    # Notify all verified users
    for user in data["users"]:
        if user["status"] == "verified" and "chat_id" in user:
            notify_user(
                user.get("chat_id"),
                f"💫 Jackpot alert! 🌟 Your coins are waiting—collect them now! 🪙\n\n{link}"
            )

    return redirect(url_for("admin_panel"))

# Renew user membership
@app.route("/renew_user", methods=["POST"])
def renew_user():
    whatsapp = request.form.get("whatsapp")
    renewal_days = int(request.form.get("renewal_days"))
    data = load_data()

    for user in data["users"]:
        if user["whatsapp"] == whatsapp and user["status"] == "verified":
            user['remaining_days'] += renewal_days
            user['last_renewed'] = datetime.now().isoformat()
            save_data(data)

            notify_user(
                user.get("chat_id"),
                (
                    f"🌟 Membership Renewed!\n\n"
                    f"A big thank-you for your renewal! 💖\n"
                    f"Your total days: 🗓️ {user['remaining_days']} days\n"
                    f"Your journey with us continues—make it amazing! 🚀"
                )
            )
            break

    return redirect(url_for("admin_panel"))

if __name__ == "__main__":
    app.run(debug=False)
