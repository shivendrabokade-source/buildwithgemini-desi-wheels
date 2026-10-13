"""Seed script for DesiWheels used car catalog in Firestore."""
from google.cloud import firestore

# Hardcode project ID explicitly to prevent project-number resolution issues on Agent Platform
PROJECT_ID = "qwiklabs-gcp-04-dcb18a21adcb"

SAMPLE_CARS = [
    {
        "id": "car_001",
        "make": "Maruti Suzuki",
        "model": "Brezza ZXi",
        "year": 2021,
        "price_lakhs": 8.75,
        "fuel_type": "Petrol",
        "transmission": "Manual",
        "mileage_km": 32000,
        "city": "Delhi NCR",
        "rto_state": "DL",
        "owners": 1,
        "bs_stage": "BS6",
        "condition_rating": 4.5,
        "features": ["Sunroof", "Touchscreen", "Dual Airbags", "Alloy Wheels"],
        "inspection_status": "Verified 120-point check, non-accidental, clean RC",
    },
    {
        "id": "car_002",
        "make": "Hyundai",
        "model": "Creta SX(O)",
        "year": 2020,
        "price_lakhs": 12.50,
        "fuel_type": "Diesel",
        "transmission": "Automatic",
        "mileage_km": 48000,
        "city": "Bengaluru",
        "rto_state": "KA",
        "owners": 1,
        "bs_stage": "BS6",
        "condition_rating": 4.7,
        "features": ["Panoramic Sunroof", "Ventilated Seats", "Bose Audio", "Wireless Charging"],
        "inspection_status": "Verified, authorized service record available, no hypothecation",
    },
    {
        "id": "car_003",
        "make": "Honda",
        "model": "City VX",
        "year": 2019,
        "price_lakhs": 7.90,
        "fuel_type": "Petrol",
        "transmission": "CVT",
        "mileage_km": 41000,
        "city": "Mumbai",
        "rto_state": "MH",
        "owners": 1,
        "bs_stage": "BS4",
        "condition_rating": 4.3,
        "features": ["Sunroof", "Cruise Control", "Paddle Shifters", "Leatherette Seats"],
        "inspection_status": "Clean title, minor bumper touch-up, excellent engine health",
    },
    {
        "id": "car_004",
        "make": "Tata",
        "model": "Nexon EV Max XZ+ Lux",
        "year": 2022,
        "price_lakhs": 13.20,
        "fuel_type": "EV",
        "transmission": "Automatic",
        "mileage_km": 24000,
        "city": "Delhi NCR",
        "rto_state": "DL",
        "owners": 1,
        "bs_stage": "Zero Emission",
        "condition_rating": 4.8,
        "features": ["Fast Charger Included", "Air Purifier", "Electronic Parking Brake", "Regen Modes"],
        "inspection_status": "Battery health at 96%, original warranty valid, zero accident history",
    },
    {
        "id": "car_005",
        "make": "Toyota",
        "model": "Innova Crysta 2.4 GX",
        "year": 2018,
        "price_lakhs": 14.80,
        "fuel_type": "Diesel",
        "transmission": "Manual",
        "mileage_km": 85000,
        "city": "Hyderabad",
        "rto_state": "TS",
        "owners": 2,
        "bs_stage": "BS4",
        "condition_rating": 4.2,
        "features": ["7 Seater", "Touchscreen Infotainment", "Rear AC", "Eco/Power Modes"],
        "inspection_status": "Heavy duty suspension tested, timely dealer service history, clean RC",
    },
    {
        "id": "car_006",
        "make": "Maruti Suzuki",
        "model": "Swift VXi CNG",
        "year": 2022,
        "price_lakhs": 6.40,
        "fuel_type": "CNG",
        "transmission": "Manual",
        "mileage_km": 29000,
        "city": "Delhi NCR",
        "rto_state": "HR",
        "owners": 1,
        "bs_stage": "BS6",
        "condition_rating": 4.6,
        "features": ["Factory Fitted S-CNG", "Power Windows", "Keyless Entry", "Music System"],
        "inspection_status": "CNG hydro-test certified, high fuel efficiency verified, first owner",
    }
]

def seed():
    db = firestore.Client(project=PROJECT_ID)
    collection = db.collection("cars")
    print(f"Connecting to Firestore for project: {PROJECT_ID}...")
    for car in SAMPLE_CARS:
        doc_ref = collection.document(car["id"])
        doc_ref.set(car)
        print(f"  ✓ Added car: {car['year']} {car['make']} {car['model']} ({car['city']}) - ₹{car['price_lakhs']}L")
    print("\n✅ Successfully seeded cars catalog in Firestore!")

if __name__ == "__main__":
    seed()
