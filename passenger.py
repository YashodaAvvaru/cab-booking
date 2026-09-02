"""
passenger.py
--------------
Run this file for the PASSENGER side of the Cab Booking System.
Run driver.py separately (in another terminal) for the DRIVER side.

Only TWO files needed: passenger.py and driver.py.
They share data through a plain JSON file (cab_data.json), created
automatically in the same folder - no SQL, no separate storage module,
no frontend, pure Python standard library only.

Run with:  python3 passenger.py
"""

import json
import os
import hashlib
from datetime import datetime

DATA_FILE = "cab_data.json"
BASE_FARE = 40.0
RATE_PER_KM = 12.0


# ----------------------------------------------------------------------
# SHARED DATA FILE HELPERS
# ----------------------------------------------------------------------

def _empty_data():
    return {
        "users": [],           # list of dicts: id, name, phone, password_hash, role
        "driver_details": {},  # str(user_id) -> {vehicle_no, vehicle_type, is_available}
        "bookings": [],        # list of dicts
        "ratings": {},         # str(booking_id) -> {rating, comment}
        "next_user_id": 1,
        "next_booking_id": 1,
    }


def load_data():
    """Read the latest shared state from disk (so we see the driver app's changes too)."""
    if not os.path.exists(DATA_FILE):
        data = _empty_data()
        save_data(data)
        return data
    with open(DATA_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            data = _empty_data()
            save_data(data)
            return data


def save_data(data):
    """Write the shared state back to disk so the driver app can see it."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def calculate_fare(distance_km: float) -> float:
    return round(BASE_FARE + distance_km * RATE_PER_KM, 2)


def find_user_by_phone(data, phone, role):
    for u in data["users"]:
        if u["phone"] == phone and u["role"] == role:
            return u
    return None


def find_user_by_id(data, user_id):
    for u in data["users"]:
        if u["id"] == user_id:
            return u
    return None


def pause():
    input("\nPress Enter to continue...")


def get_password(prompt="Password: "):
    # Plain input() is used instead of getpass so this works reliably in
    # every console/IDE (getpass can fail silently in some environments).
    # Note: the password will be visible on screen as you type it.
    return input(prompt)


# ----------------------------------------------------------------------
# AUTH
# ----------------------------------------------------------------------

def register():
    print("\n--- Passenger Registration ---")
    data = load_data()

    name = input("Full name: ").strip()
    phone = input("Phone number: ").strip()

    if find_user_by_phone(data, phone, "passenger"):
        print("\n❌ A user with this phone number already exists.")
        return

    password = get_password()
    user_id = data["next_user_id"]
    data["next_user_id"] += 1

    data["users"].append({
        "id": user_id,
        "name": name,
        "phone": phone,
        "password_hash": hash_password(password),
        "role": "passenger",
    })

    save_data(data)
    print(f"\n✅ Registration successful! Your user ID is {user_id}. Please log in now.")


def login():
    print("\n--- Passenger Login ---")
    data = load_data()

    phone = input("Phone number: ").strip()
    password = get_password()

    user = find_user_by_phone(data, phone, "passenger")
    if user and user["password_hash"] == hash_password(password):
        print(f"\n✅ Welcome back, {user['name']}!")
        return user["id"], user["name"]
    else:
        print("\n❌ Invalid credentials.")
        return None, None


# ----------------------------------------------------------------------
# PASSENGER FEATURES
# ----------------------------------------------------------------------

def search_available_cabs(data=None):
    data = data or load_data()
    available = []
    for uid_str, details in data["driver_details"].items():
        if details["is_available"]:
            driver = find_user_by_id(data, int(uid_str))
            if driver:
                available.append((int(uid_str), driver["name"], details["vehicle_no"], details["vehicle_type"]))

    if not available:
        print("\nNo cabs available right now. Try again later.")
        return []

    print("\nAvailable Cabs:")
    print(f"{'ID':<5}{'Driver':<20}{'Vehicle No':<15}{'Type':<12}")
    for r in available:
        print(f"{r[0]:<5}{r[1]:<20}{r[2]:<15}{r[3]:<12}")
    return available


def book_cab(passenger_id):
    data = load_data()
    available = search_available_cabs(data)
    if not available:
        return

    try:
        driver_id = int(input("\nEnter Driver ID to book: "))
    except ValueError:
        print("Invalid ID.")
        return

    if driver_id not in [r[0] for r in available]:
        print("That driver is not available.")
        return

    pickup = input("Pickup location: ").strip()
    drop = input("Drop location: ").strip()
    try:
        distance = float(input("Estimated distance (km): "))
    except ValueError:
        print("Invalid distance.")
        return

    fare = calculate_fare(distance)
    booking_id = data["next_booking_id"]
    data["next_booking_id"] += 1

    data["bookings"].append({
        "id": booking_id,
        "passenger_id": passenger_id,
        "driver_id": driver_id,
        "pickup": pickup,
        "drop": drop,
        "distance_km": distance,
        "fare": fare,
        "status": "pending",   # pending -> accepted/rejected -> ongoing -> completed (or cancelled)
        "created_at": datetime.now().isoformat(timespec="seconds"),
    })

    save_data(data)
    print(f"\n✅ Booking placed! Booking ID: {booking_id}. Estimated fare: ₹{fare}")
    print("Waiting for driver to accept (run driver.py in another terminal).")


def cancel_booking(passenger_id):
    data = load_data()
    active = [b for b in data["bookings"] if b["passenger_id"] == passenger_id and b["status"] in ("pending", "accepted")]

    if not active:
        print("\nNo active bookings to cancel.")
        return

    print("\nYour active bookings:")
    for b in active:
        print(f"Booking ID: {b['id']}  |  Status: {b['status']}")

    try:
        booking_id = int(input("\nEnter Booking ID to cancel: "))
    except ValueError:
        print("Invalid ID.")
        return

    for b in data["bookings"]:
        if b["id"] == booking_id and b["passenger_id"] == passenger_id and b["status"] in ("pending", "accepted"):
            b["status"] = "cancelled"
            save_data(data)
            print("✅ Booking cancelled.")
            return

    print("❌ Could not cancel (invalid ID or already in progress).")


def view_ride_history(passenger_id):
    data = load_data()
    history = [b for b in data["bookings"] if b["passenger_id"] == passenger_id]

    if not history:
        print("\nNo ride history yet.")
        return

    print("\n--- Ride History ---")
    for b in sorted(history, key=lambda x: x["id"], reverse=True):
        driver = find_user_by_id(data, b["driver_id"])
        driver_name = driver["name"] if driver else "Unknown"
        print(f"ID:{b['id']} | Driver: {driver_name} | {b['pickup']} -> {b['drop']} "
              f"| Fare: ₹{b['fare']} | Status: {b['status']}")


def give_rating(passenger_id):
    data = load_data()
    eligible = [
        b for b in data["bookings"]
        if b["passenger_id"] == passenger_id and b["status"] == "completed" and str(b["id"]) not in data["ratings"]
    ]

    if not eligible:
        print("\nNo completed rides awaiting rating.")
        return

    print("\nRides awaiting rating:")
    for b in eligible:
        driver = find_user_by_id(data, b["driver_id"])
        print(f"Booking ID: {b['id']}  |  Driver: {driver['name']}")

    try:
        booking_id = int(input("\nEnter Booking ID to rate: "))
        rating = int(input("Rating (1-5): "))
    except ValueError:
        print("Invalid input.")
        return

    if booking_id not in [b["id"] for b in eligible] or not (1 <= rating <= 5):
        print("Invalid booking ID or rating.")
        return

    comment = input("Comment (optional): ").strip()
    data["ratings"][str(booking_id)] = {"rating": rating, "comment": comment}
    save_data(data)
    print("✅ Thanks for your feedback!")


def passenger_menu(user_id, name):
    while True:
        print(f"\n===== PASSENGER MENU ({name}) =====")
        print("1. Search available cabs")
        print("2. Book a cab")
        print("3. Cancel a booking")
        print("4. View ride history")
        print("5. Give rating")
        print("6. Logout")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            search_available_cabs()
        elif choice == "2":
            book_cab(user_id)
        elif choice == "3":
            cancel_booking(user_id)
        elif choice == "4":
            view_ride_history(user_id)
        elif choice == "5":
            give_rating(user_id)
        elif choice == "6":
            print("Logging out...")
            break
        else:
            print("Invalid choice.")
        pause()


# ----------------------------------------------------------------------
# MAIN
# ----------------------------------------------------------------------

def main():
    print("=" * 48)
    print("      CAB BOOKING SYSTEM -- PASSENGER APP")
    print("=" * 48)
    print("(Run driver.py separately, in another terminal, for the driver side)")

    while True:
        print("\n1. Register")
        print("2. Login")
        print("3. Exit")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            register()
        elif choice == "2":
            user_id, name = login()
            if user_id:
                passenger_menu(user_id, name)
        elif choice == "3":
            print("\nThank you for using the Passenger App. Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
