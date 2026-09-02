# Cab Booking System — Passenger & Driver (Pure Python, 2 files only)

Just **two files**, nothing else:

| File | Role | Run with |
|---|---|---|
| `passenger.py` | Passenger app | `python3 passenger.py` |
| `driver.py` | Driver app | `python3 driver.py` |

No SQL, no separate storage module, no frontend, no external libraries —
only Python's standard library (`json`, `os`, `hashlib`, `getpass`,
`datetime`).

## How to run

1. Put `passenger.py` and `driver.py` in the same folder.
2. Open **two terminal windows** in that folder.
3. Terminal 1: `python3 passenger.py` → register/login as a passenger.
4. Terminal 2: `python3 driver.py` → register/login as a driver.
5. Book a cab from the passenger app — it appears as a pending request
   the next time the driver checks "Accept/Reject ride".
6. Driver accepts → starts → completes the ride.
7. Back in the passenger app, "View ride history" shows it as
   `completed`, and "Give rating" becomes available.

## How the two files share data

Both files independently define the same small set of helper functions
(`load_data`, `save_data`, `hash_password`, etc.) and both read/write the
same file: **`cab_data.json`**, created automatically in the same folder
the first time either app runs. Every menu action:
1. Loads the latest data from `cab_data.json`
2. Makes its change (registers a user, places a booking, etc.)
3. Immediately saves it back

That file is what keeps the two independent programs in sync — no SQL
database, no server process, just plain JSON.

Delete `cab_data.json` any time to reset all data.

## Data model (inside `cab_data.json`)

```json
{
  "users": [ {"id": 1, "name": "...", "phone": "...", "password_hash": "...", "role": "passenger"} ],
  "driver_details": { "2": {"vehicle_no": "...", "vehicle_type": "...", "is_available": true} },
  "bookings": [ {"id": 1, "passenger_id": 1, "driver_id": 2, "pickup": "...", "drop": "...",
                  "distance_km": 5, "fare": 100.0, "status": "completed", "created_at": "..."} ],
  "ratings": { "1": {"rating": 5, "comment": "Nice ride"} },
  "next_user_id": 3,
  "next_booking_id": 2
}
```

Passwords are stored as SHA-256 hashes, never in plain text.

**Fare formula**: `₹40 base + ₹12 × distance(km)` — see
`calculate_fare()` near the top of each file (change it in both files
if you adjust it).

## Ride lifecycle (state machine)

```
pending --(driver accepts)--> accepted --(driver starts)--> ongoing --(driver completes)--> completed
   |                              |
   +--(passenger cancels)--> cancelled     (driver can also reject -> rejected)
```

## Menus

**Passenger** (`passenger.py`): Register/Login, Search available cabs,
Book a cab, Cancel a booking, View ride history, Give rating.

**Driver** (`driver.py`): Register/Login, Set availability (toggle),
Accept/Reject ride, Start/Complete ride, View earnings.

## Why this is a good submission

- Genuinely **two separate programs**, matching a "tenant & owner" /
  "server & user" two-actor requirement — stronger than a single script
  with an internal menu switch.
- Mirrors, in simplified form, how ride-hailing platforms (Ola, Uber,
  Rapido) split their supply (driver) and demand (passenger) sides —
  good material for the "future usage in society" part of your report.
- Clean discussion points for a viva: password hashing, a booking state
  machine, and file-based state sharing between two independent
  processes — all without needing to explain SQL syntax.

## Ideas to extend for extra credit

- Have each app poll `cab_data.json` every few seconds in a loop so
  updates appear without navigating a menu.
- Add simple file locking to avoid rare write clashes if both apps save
  at the exact same instant.
- A third `admin.py` that reads the same `cab_data.json` to show all
  bookings across every passenger/driver.
- Export ride history to CSV using Python's built-in `csv` module.
