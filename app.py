from flask import Flask, render_template, redirect, url_for, request, session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
from models import db, User, Plant, Cart
from twilio.rest import Client
import csv
import os

twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# ---------------- APP CONFIG ----------------
app = Flask(__name__)
app.config.from_object(Config)
app.secret_key = "secret123"

db.init_app(app)

login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------------- USER LOADER ----------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- HOME ----------------
@app.route("/")
def index():
    plants = Plant.query.all()
    return render_template("index.html", plants=plants)

# ---------------- REGISTER ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user = User(
            username=request.form["username"],
            password=generate_password_hash(request.form["password"]),
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        return redirect(url_for("login"))
    return render_template("register.html")

# ---------------- LOGIN ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect(url_for("index"))
    return render_template("login.html")

# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("index"))

# ---------------- CART ----------------
@app.route("/add_to_cart/<int:id>")
@login_required
def add_to_cart(id):
    db.session.add(Cart(user_id=current_user.id, plant_id=id))
    db.session.commit()
    return redirect(url_for("cart"))

@app.route("/cart")
@login_required
def cart():
    items = Cart.query.filter_by(user_id=current_user.id).all()
    plants = [Plant.query.get(item.plant_id) for item in items]
    return render_template("cart.html", plants=plants)

# ---------------- BUY NOW ----------------
@app.route("/buy_now/<int:id>")
@login_required
def buy_now(id):
    session["buy_now_plant"] = id
    return redirect(url_for("address"))

# ---------------- ADDRESS ----------------
@app.route("/address", methods=["GET", "POST"])
@login_required
def address():
    plant = Plant.query.get(session.get("buy_now_plant"))

    if request.method == "POST":
        session["delivery_address"] = {
            "name": request.form["name"],
            "phone": request.form["phone"],
            "address": request.form["address"]
        }
        return redirect(url_for("payment"))

    return render_template("address.html", plant=plant)

# ---------------- PAYMENT (COD ONLY) ----------------
@app.route("/payment", methods=["GET", "POST"])
@login_required
def payment():
    plant = Plant.query.get(session.get("buy_now_plant"))
    address = session.get("delivery_address")

    if request.method == "POST":
        phone = address["phone"]

        # SEND REAL SMS FOR COD
        twilio_client.messages.create(
            body=f"""
🌱 Order Placed Successfully!

Product: {plant.name}
Price: ₹{plant.price}

Payment Mode: Cash on Delivery
Please pay at delivery.

Thank you for shopping with us!
            """,
            from_=TWILIO_PHONE,
            to=f"+91{phone}"
        )

        return redirect(url_for("success"))

    return render_template("payment.html", plant=plant, address=address)

# ---------------- SUCCESS ----------------
@app.route("/success")
@login_required
def success():
    return render_template("success.html")

# ---------------- ADMIN ----------------
@app.route("/admin", methods=["GET", "POST"])
@login_required
def admin():
    if not current_user.is_admin:
        return redirect(url_for("index"))

    if request.method == "POST":
        db.session.add(Plant(
            name=request.form["name"],
            price=float(request.form["price"]),
            category=request.form["category"],
            image=request.form["image"],
            description=request.form["description"]
        ))
        db.session.commit()

    return render_template("admin.html")

# ---------------- CSV IMPORT ----------------
def import_plants_csv():
    csv_path = os.path.join(os.path.dirname(__file__), "dataset", "plants.csv")

    if not os.path.exists(csv_path) or Plant.query.first():
        return

    with open(csv_path, newline="", encoding="utf-8") as file:
        for row in csv.DictReader(file):
            db.session.add(Plant(
                name=row["name"],
                price=float(row["price"]),
                category=row["category"],
                image=row["image"],
                description=row["description"]
            ))
    db.session.commit()

# ---------------- RUN ----------------
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        import_plants_csv()
    app.run(debug=True)
