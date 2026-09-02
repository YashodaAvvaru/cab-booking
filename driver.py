"""
driver.py
-----------
Run this file for the DRIVER side of the Cab Booking System.
Run passenger.py separately (in another terminal) for the PASSENGER side.

Only TWO files needed: passenger.py and driver.py.
They share data through a plain JSON file (cab_data.json), created
automatically in the same folder - no SQL, no separate storage module,
no frontend, pure Python standard library only.

Run with:  python3 driver.py
"""

import json
import os
import hashlib

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
    """Read the latest shared state from disk (so we see the passenger app's changes too)."""
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
    """Write the shared state back to disk so the passenger app can see it."""
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=2)


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


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
    print("\n--- Driver Registration ---")
    data = load_data()

    name = input("Full name: ").strip()
    phone = input("Phone number: ").strip()

    if find_user_by_phone(data, phone, "driver"):
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
        "role": "driver",
    })

    vehicle_no = input("Vehicle number: ").strip()
    vehicle_type = input("Vehicle type (Hatchback/Sedan/SUV/Auto): ").strip()
    data["driver_details"][str(user_id)] = {
        "vehicle_no": vehicle_no,
        "vehicle_type": vehicle_type,
        "is_available": True,
    }

    save_data(data)
    print(f"\n✅ Registration successful! Your user ID is {user_id}. Please log in now.")


def login():
    print("\n--- Driver Login ---")
    data = load_data()

    phone = input("Phone number: ").strip()
    password = get_password()

    user = find_user_by_phone(data, phone, "driver")
    if user and user["password_hash"] == hash_password(password):
        print(f"\n✅ Welcome back, {user['name']}!")
        return user["id"], user["name"]
    else:
        print("\n❌ Invalid credentials.")
        return None, None


# ----------------------------------------------------------------------
# DRIVER FEATURES
# ----------------------------------------------------------------------

def set_availability(driver_id):
    data = load_data()
    details = data["driver_details"][str(driver_id)]
    details["is_available"] = not details["is_available"]
    save_data(data)
    print(f"\n✅ You are now {'AVAILABLE' if details['is_available'] else 'UNAVAILABLE'} for rides.")


def accept_reject_ride(driver_id):
    data = load_data()
    pending = [b for b in data["bookings"] if b["driver_id"] == driver_id and b["status"] == "pending"]

    if not pending:
        print("\nNo pending ride requests.")
        return

    print("\nPending Requests:")
    for b in pending:
        passenger = find_user_by_id(data, b["passenger_id"])
        print(f"ID:{b['id']} | Passenger: {passenger['name']} | {b['pickup']} -> {b['drop']} | Fare: ₹{b['fare']}")

    try:
        booking_id = int(input("\nEnter Booking ID to respond to: "))
    except ValueError:
        print("Invalid ID.")
        return

    match = next((b for b in data["bookings"]
                  if b["id"] == booking_id and b["driver_id"] == driver_id and b["status"] == "pending"), None)
    if not match:
        print("Invalid booking ID.")
        return

    decision = input("Accept or Reject? (A/R): ").strip().upper()
    if decision == "A":
        match["status"] = "accepted"
    elif decision == "R":
        match["status"] = "rejected"
    else:
        print("Invalid choice.")
        return

    save_data(data)
    print(f"✅ Ride {match['status']}.")


def start_complete_ride(driver_id):
    data = load_data()
    active = [b for b in data["bookings"] if b["driver_id"] == driver_id and b["status"] in ("accepted", "ongoing")]

    if not active:
        print("\nNo accepted/ongoing rides.")
        return

    print("\nYour rides:")
    for b in active:
        print(f"Booking ID: {b['id']}  |  Status: {b['status']}")

    try:
        booking_id = int(input("\nEnter Booking ID: "))
    except ValueError:
        print("Invalid ID.")
        return

    match = next((b for b in data["bookings"]
                  if b["id"] == booking_id and b["driver_id"] == driver_id and b["status"] in ("accepted", "ongoing")), None)
    if not match:
        print("Invalid booking ID.")
        return

    if match["status"] == "accepted":
        match["status"] = "ongoing"
        save_data(data)
        print("✅ Ride started (status: ongoing).")
    elif match["status"] == "ongoing":
        match["status"] = "completed"
        save_data(data)
        print("✅ Ride completed!")


def view_earnings(driver_id):
    data = load_data()
    completed = [b for b in data["bookings"] if b["driver_id"] == driver_id and b["status"] == "completed"]
    total = sum(b["fare"] for b in completed)

    driver_ratings = [data["ratings"][str(b["id"])]["rating"] for b in data["bookings"]
                       if b["driver_id"] == driver_id and str(b["id"]) in data["ratings"]]
    avg_rating = round(sum(driver_ratings) / len(driver_ratings), 2) if driver_ratings else None

    print(f"\n--- Earnings Summary ---")
    print(f"Completed rides : {len(completed)}")
    print(f"Total earnings  : ₹{total}")
    print(f"Average rating  : {avg_rating if avg_rating else 'No ratings yet'}")


def driver_menu(user_id, name):
    while True:
        data = load_data()
        status = "AVAILABLE" if data["driver_details"][str(user_id)]["is_available"] else "UNAVAILABLE"
        print(f"\n===== DRIVER MENU ({name}) — Currently: {status} =====")
        print("1. Set availability (toggle)")
        print("2. Accept/Reject ride")
        print("3. Start/Complete ride")
        print("4. View earnings")
        print("5. Logout")
        choice = input("Choose an option: ").strip()

        if choice == "1":
            set_availability(user_id)
        elif choice == "2":
            accept_reject_ride(user_id)
        elif choice == "3":
            start_complete_ride(user_id)
        elif choice == "4":
            view_earnings(user_id)
        elif choice == "5":
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
    print("       CAB BOOKING SYSTEM -- DRIVER APP")
    print("=" * 48)
    print("(Run passenger.py separately, in another terminal, for the passenger side)")

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
                driver_menu(user_id, name)
        elif choice == "3":
            print("\nThank you for using the Driver App. Goodbye!")
            break
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()