"""Firestore backend tools for DesiWheels used car catalog."""
from typing import Any, Dict, List, Optional
from google.cloud import firestore
from google.adk.tools import ToolContext

# Hardcode project ID explicitly as required:
# On Agent Platform, google.auth.default() and GOOGLE_CLOUD_PROJECT return the project number,
# which breaks Firestore (default) database lookups if not pinned to the string ID.
FIRESTORE_PROJECT_ID = "qwiklabs-gcp-04-dcb18a21adcb"


def _get_db() -> firestore.Client:
    return firestore.Client(project=FIRESTORE_PROJECT_ID)


def search_used_cars(
    city: Optional[str] = None,
    max_price_lakhs: Optional[float] = None,
    fuel_type: Optional[str] = None,
    transmission: Optional[str] = None,
    make: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Searches the verified used car catalog in Firestore with filters.

    Args:
        city: Filter by city/region (e.g., 'Delhi NCR', 'Bengaluru', 'Mumbai', 'Hyderabad').
        max_price_lakhs: Maximum budget in INR Lakhs (e.g., 10.0 for ₹10 Lakhs).
        fuel_type: Filter by fuel type ('Petrol', 'Diesel', 'CNG', 'EV').
        transmission: Filter by transmission ('Manual', 'Automatic', 'CVT').
        make: Filter by manufacturer (e.g., 'Maruti Suzuki', 'Hyundai', 'Tata', 'Honda', 'Toyota').

    Returns:
        List of matching car listing dictionaries.
    """
    db = _get_db()
    docs = db.collection("cars").stream()
    results = []

    for doc in docs:
        car = doc.to_dict()
        car["id"] = doc.id

        # Case-insensitive filtering
        if city and city.lower() not in car.get("city", "").lower():
            continue
        if max_price_lakhs is not None and car.get("price_lakhs", 0) > max_price_lakhs:
            continue
        if fuel_type and fuel_type.lower() != car.get("fuel_type", "").lower():
            continue
        if transmission and transmission.lower() not in car.get("transmission", "").lower():
            continue
        if make and make.lower() not in car.get("make", "").lower():
            continue

        results.append(car)

    # Sort by price ascending
    results.sort(key=lambda x: x.get("price_lakhs", 0))
    return results


def get_car_details(car_id: str) -> Dict[str, Any]:
    """Retrieves full details and inspection status of a specific car by its ID.

    Args:
        car_id: The unique identifier of the car (e.g. 'car_001').

    Returns:
        The car details dictionary, or an error message if not found.
    """
    db = _get_db()
    doc = db.collection("cars").document(car_id).get()
    if not doc.exists:
        return {"error": f"Car with ID '{car_id}' not found."}
    data = doc.to_dict()
    data["id"] = doc.id
    return data


def add_car_listing(
    make: str,
    model: str,
    year: int,
    price_lakhs: float,
    fuel_type: str,
    transmission: str,
    mileage_km: int,
    city: str,
    rto_state: str,
    owners: int = 1,
    bs_stage: str = "BS6",
    features: Optional[List[str]] = None,
    inspection_notes: str = "Self-reported listing, verification pending",
) -> Dict[str, Any]:
    """Adds a new used car listing into the Firestore catalog.

    Args:
        make: Brand or manufacturer (e.g. 'Tata', 'Maruti Suzuki', 'Mahindra').
        model: Model name and trim (e.g. 'Harrier XZA+').
        year: Year of manufacturing/registration.
        price_lakhs: Asking price in INR Lakhs (e.g. 15.5).
        fuel_type: 'Petrol', 'Diesel', 'CNG', or 'EV'.
        transmission: 'Manual' or 'Automatic'.
        mileage_km: Odometer reading in kilometers.
        city: City where vehicle is registered/located (e.g. 'Delhi NCR', 'Pune').
        rto_state: 2-letter state code for RTO (e.g. 'DL', 'MH', 'KA', 'HR').
        owners: Number of previous owners (1 for 1st owner, 2 for 2nd owner).
        bs_stage: Bharat Stage emission standard (e.g. 'BS4', 'BS6').
        features: Key features of the car (e.g. ['Sunroof', 'Leather Seats']).
        inspection_notes: Initial notes or inspection status.

    Returns:
        A confirmation dict with the generated car_id.
    """
    db = _get_db()
    collection = db.collection("cars")
    new_doc_ref = collection.document()
    
    car_data = {
        "id": new_doc_ref.id,
        "make": make,
        "model": model,
        "year": year,
        "price_lakhs": price_lakhs,
        "fuel_type": fuel_type,
        "transmission": transmission,
        "mileage_km": mileage_km,
        "city": city,
        "rto_state": rto_state,
        "owners": owners,
        "bs_stage": bs_stage,
        "condition_rating": 4.0,
        "features": features or [],
        "inspection_status": inspection_notes,
    }
    new_doc_ref.set(car_data)
    return {"status": "success", "message": f"Listing created for {year} {make} {model}", "car_id": new_doc_ref.id}


def check_rto_compliance(car_id: str, target_city: Optional[str] = None) -> Dict[str, Any]:
    """Checks RTO regulations and NGT compliance rules for a specific car.
    
    Covers the Delhi-NCR NGT rule (10 years max for diesel, 15 years max for petrol),
    interstate NOC requirements, and road tax validity.

    Args:
        car_id: The car ID to check.
        target_city: Target city where the buyer intends to register and drive the car.

    Returns:
        Compliance evaluation, remaining legal lifespan, and advisory warnings.
    """
    car = get_car_details(car_id)
    if "error" in car:
        return car

    current_year = 2026
    car_year = car.get("year", current_year)
    fuel = car.get("fuel_type", "").lower()
    city_to_eval = (target_city or car.get("city", "")).lower()
    age = current_year - car_year

    warnings = []
    compliance = "Compliant"

    # Delhi NCR 10-year diesel / 15-year petrol rule check
    if "delhi" in city_to_eval or "ncr" in city_to_eval or "noida" in city_to_eval or "gurgaon" in city_to_eval:
        if "diesel" in fuel:
            remaining_years = 10 - age
            if remaining_years <= 0:
                compliance = "Non-Compliant / Prohibited"
                warnings.append("CRITICAL: Under NGT Delhi-NCR orders, diesel vehicles older than 10 years cannot be registered, renewed, or driven in Delhi-NCR.")
            else:
                warnings.append(f"Diesel vehicle has only {remaining_years} years of legal fitness remaining in Delhi-NCR under NGT rules.")
        elif "petrol" in fuel or "cng" in fuel:
            remaining_years = 15 - age
            if remaining_years <= 0:
                compliance = "Non-Compliant / Prohibited"
                warnings.append("CRITICAL: Petrol/CNG vehicles older than 15 years cannot ply in Delhi-NCR.")
            else:
                warnings.append(f"Petrol/CNG vehicle has {remaining_years} years remaining in Delhi-NCR.")

    # Interstate transfer checks
    rto_state = car.get("rto_state", "")
    if target_city and target_city.lower() not in car.get("city", "").lower():
        warnings.append(f"Interstate transfer from RTO {rto_state} requires Form 28 (NOC) from original RTO and road tax payment in target state.")

    return {
        "car": f"{car.get('year')} {car.get('make')} {car.get('model')}",
        "car_age_years": age,
        "fuel_type": car.get("fuel_type"),
        "bs_stage": car.get("bs_stage"),
        "compliance_status": compliance,
        "advisory_notes": warnings,
    }


def calculate_car_loan_emi(
    car_price_lakhs: float,
    down_payment_lakhs: float = 0.0,
    tenure_years: int = 5,
    annual_interest_rate_pct: float = 12.5,
) -> Dict[str, Any]:
    """Calculates monthly EMI, total interest, and payment breakdown for a car loan.

    Args:
        car_price_lakhs: Total price of the vehicle in INR Lakhs (e.g. 8.5 for ₹8.5 Lakhs).
        down_payment_lakhs: Upfront cash paid by the buyer in INR Lakhs (e.g. 2.0).
        tenure_years: Loan duration in years (typically 1 to 7 years, default is 5).
        annual_interest_rate_pct: Annual interest percentage (default 12.5% for used car loans in India).

    Returns:
        Dictionary with monthly EMI (₹), loan amount, total interest, and total payable.
    """
    principal = max(0.0, (car_price_lakhs - down_payment_lakhs) * 100000)
    if principal == 0:
        return {
            "loan_amount_inr": 0,
            "monthly_emi_inr": 0,
            "total_interest_inr": 0,
            "total_payment_inr": 0,
            "message": "Down payment covers the full price. No loan required.",
        }

    monthly_rate = (annual_interest_rate_pct / 100) / 12
    num_months = max(1, tenure_years * 12)

    if monthly_rate == 0:
        emi = principal / num_months
    else:
        emi = principal * monthly_rate * ((1 + monthly_rate) ** num_months) / (((1 + monthly_rate) ** num_months) - 1)

    total_payment = emi * num_months
    total_interest = total_payment - principal

    return {
        "car_price_lakhs": car_price_lakhs,
        "down_payment_lakhs": down_payment_lakhs,
        "loan_amount_inr": round(principal, 2),
        "monthly_emi_inr": round(emi, 2),
        "total_interest_inr": round(total_interest, 2),
        "total_payment_inr": round(total_payment, 2),
        "tenure_months": num_months,
        "interest_rate_pct": annual_interest_rate_pct,
    }


def decode_vin_specs(vin: str) -> Dict[str, Any]:
    """Decodes a vehicle VIN to fetch real manufacturer specifications from NHTSA vPIC public API.

    This free public API requires no API key.
    Useful for verifying model year, manufacturer, body class, fuel type, engine, and drive type.

    Args:
        vin: 17-character Vehicle Identification Number (or partial VIN).

    Returns:
        Structured specification data decoded directly from the public registry.
    """
    import urllib.request
    import json

    cleaned_vin = vin.strip().upper()
    url = f"https://vpic.nhtsa.dot.gov/api/vehicles/decodevinvalues/{cleaned_vin}?format=json"

    try:
        req = urllib.request.Request(url, headers={"User-Agent": "DesiWheels/1.0"})
        with urllib.request.urlopen(req, timeout=8) as response:
            data = json.loads(response.read().decode())
            results = data.get("Results", [])
            if not results:
                return {"error": "No data returned for this VIN"}

            r = results[0]
            # Extract most useful car attributes
            specs = {
                "vin": cleaned_vin,
                "make": r.get("Make"),
                "model": r.get("Model"),
                "year": r.get("ModelYear"),
                "body_class": r.get("BodyClass"),
                "fuel_type_primary": r.get("FuelTypePrimary"),
                "drive_type": r.get("DriveType"),
                "engine_cylinders": r.get("EngineConfiguration"),
                "displacement_l": r.get("DisplacementL"),
                "plant_country": r.get("PlantCountry"),
                "vehicle_type": r.get("VehicleType"),
                "source": "U.S. DOT NHTSA vPIC Public API",
            }
            # Filter out empty string values
            return {k: v for k, v in specs.items() if v}
    except Exception as e:
        return {"error": f"Failed to query NHTSA public API: {str(e)}"}


def geocode_address(address: str) -> Dict[str, Any]:
    """Converts an address or landmark into latitude and longitude coordinates using Google Maps Geocoding API.

    Reads GOOGLE_MAPS_API_KEY from environment variables.

    Args:
        address: The location or address string (e.g. 'Connaught Place, New Delhi', 'Indiranagar, Bengaluru').

    Returns:
        Dictionary containing formatted address, latitude, longitude, and place_id.
    """
    import os
    import urllib.parse
    import urllib.request
    import json

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    encoded_address = urllib.parse.quote(address)
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={encoded_address}&key={api_key}"

    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            status = data.get("status")
            if status != "OK" or not data.get("results"):
                return {"error": f"Geocoding failed with status: {status}"}

            first = data["results"][0]
            loc = first["geometry"]["location"]
            return {
                "address_queried": address,
                "formatted_address": first.get("formatted_address"),
                "latitude": loc["lat"],
                "longitude": loc["lng"],
                "place_id": first.get("place_id"),
            }
    except Exception as e:
        return {"error": f"Geocoding request failed: {str(e)}"}


def find_nearby_places(
    latitude: float,
    longitude: float,
    place_type: str = "car_dealer",
    radius_meters: float = 5000.0,
    max_results: int = 5,
) -> Dict[str, Any]:
    """Finds nearby places of a given type using Google Maps Places API (New).

    Reads GOOGLE_MAPS_API_KEY from environment variables.
    Calls https://places.googleapis.com/v1/places:searchNearby with required field mask and headers.

    Args:
        latitude: Center latitude.
        longitude: Center longitude.
        place_type: Type of place to search for (e.g. 'car_dealer', 'car_repair', 'car_wash', 'gas_station').
        radius_meters: Search radius in meters (default 5000m / 5km).
        max_results: Maximum number of places to return (default 5, max 20).

    Returns:
        List of places with key fields: name, formatted_address, and location coordinates.
    """
    import os
    import urllib.request
    import json

    api_key = os.environ.get("GOOGLE_MAPS_API_KEY")
    if not api_key:
        return {"error": "GOOGLE_MAPS_API_KEY environment variable is not set."}

    url = "https://places.googleapis.com/v1/places:searchNearby"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": api_key,
        "X-Goog-FieldMask": "places.displayName,places.formattedAddress,places.location,places.types",
    }

    body = {
        "includedTypes": [place_type],
        "maxResultCount": min(max_results, 20),
        "locationRestriction": {
            "circle": {
                "center": {
                    "latitude": latitude,
                    "longitude": longitude,
                },
                "radius": float(radius_meters),
            }
        },
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            places_raw = data.get("places", [])
            places_clean = []
            for p in places_raw:
                display_name = p.get("displayName", {}).get("text", "Unknown")
                formatted_address = p.get("formattedAddress", "")
                loc = p.get("location", {})
                places_clean.append({
                    "name": display_name,
                    "address": formatted_address,
                    "location": {
                        "latitude": loc.get("latitude"),
                        "longitude": loc.get("longitude"),
                    },
                    "types": p.get("types", []),
                })

            return {
                "center": {"latitude": latitude, "longitude": longitude},
                "place_type": place_type,
                "radius_meters": radius_meters,
                "count": len(places_clean),
                "places": places_clean,
            }
    except Exception as e:
        return {"error": f"Places API request failed: {str(e)}"}


async def generate_car_image(
    prompt: str,
    tool_context: ToolContext,
    car_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Generates an image of a vehicle using the gemini-3.1-flash-lite-image model in global region.

    Saves the image to the Playground Artifacts panel via tool_context.save_artifact,
    and uploads the bytes to the public Cloud Storage bucket returning its public HTTPS URL.

    Args:
        prompt: Description of the car to generate (e.g. 'A sleek metallic red Maruti Suzuki Brezza parked in front of India Gate').
        tool_context: ADK ToolContext injected by the framework.
        car_name: Optional short name/identifier for the car image filename.

    Returns:
        Dictionary with public Cloud Storage URL, filename, and status.
    """
    from google import genai
    from google.genai import types
    from google.cloud import storage
    import uuid

    bucket_name = "desiwheels-gallery-2379"

    # 1. Generate image using gemini-3.1-flash-lite-image (client uses location=global from .env)
    client = genai.Client()
    try:
        response = await client.aio.models.generate_content(
            model="gemini-3.1-flash-lite-image",
            contents=prompt,
        )
    except Exception as e:
        return {"error": f"Failed to generate image with gemini-3.1-flash-lite-image: {str(e)}"}

    # Extract image bytes
    image_bytes = None
    mime_type = "image/jpeg"
    if response.candidates:
        for part in response.candidates[0].content.parts:
            if part.inline_data:
                image_bytes = part.inline_data.data
                mime_type = part.inline_data.mime_type or "image/jpeg"
                break

    if not image_bytes:
        return {"error": "Model response did not contain image data."}

    # Clean name for artifact filename
    slug = (car_name or "car").lower().replace(" ", "_").replace("/", "_")
    image_id = uuid.uuid4().hex[:8]
    ext = "jpg" if "jpeg" in mime_type or "jpg" in mime_type else "png"
    filename = f"{slug}_{image_id}.{ext}"

    # 2. Save image artifact so it appears in Playground's Artifacts panel
    artifact_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
    try:
        await tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"prompt": prompt, "model": "gemini-3.1-flash-lite-image"},
        )
    except Exception as e:
        # Artifact service may not be passed in custom standalone runners, but is present in adk web playground
        pass



    # 3. Upload bytes to public Cloud Storage bucket and construct public HTTPS URL
    gcs_client = storage.Client(project="qwiklabs-gcp-04-dcb18a21adcb")
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(image_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

    return {
        "status": "success",
        "prompt": prompt,
        "filename": filename,
        "public_url": public_url,
        "message": f"Image generated and uploaded. Public URL: {public_url}",
    }


async def generate_car_video(
    prompt: str,
    tool_context: ToolContext,
    car_name: Optional[str] = None,
    duration_seconds: int = 4,
) -> Dict[str, Any]:
    """Generates a short video clip for a vehicle/car scenario using Google's Omni model (gemini-omni-flash-preview) in the global region.

    (1) Saves the video with tool_context.save_artifact so it appears in the Playground's Artifacts panel.
    (2) Uploads the same video bytes to the public Cloud Storage bucket (desiwheels-gallery-2379) and returns its public HTTPS URL.

    Args:
        prompt: Description of the car or automotive video scene (e.g. 'A sleek metallic Mahindra Thar driving on a mountain pass in Ladakh').
        tool_context: ADK ToolContext injected by the framework.
        car_name: Optional short name/identifier for the car video filename.
        duration_seconds: Video duration in seconds (between 3 and 10, default 4).

    Returns:
        Dictionary with public Cloud Storage URL, filename, and status.
    """
    import asyncio
    import base64
    import uuid
    import google.auth
    import google.auth.transport.requests
    import httpx
    from google.genai import types
    from google.cloud import storage

    bucket_name = "desiwheels-gallery-2379"
    project_id = "qwiklabs-gcp-04-dcb18a21adcb"

    duration = max(3, min(10, duration_seconds))
    duration_str = f"{duration}s"

    # 1. Obtain auth token for Vertex AI global interactions API
    creds, _ = google.auth.default()
    auth_req = google.auth.transport.requests.Request()
    creds.refresh(auth_req)

    url = f"https://aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/global/interactions"
    headers = {
        "Authorization": f"Bearer {creds.token}",
        "Content-Type": "application/json; charset=utf-8",
    }
    payload = {
        "model": "gemini-omni-flash-preview",
        "background": True,
        "input": [{"type": "text", "text": prompt}],
        "response_format": [{
            "type": "video",
            "aspect_ratio": "16:9",
            "duration": duration_str,
        }],
        "generation_config": {
            "video_config": {
                "task": "text_to_video",
            }
        },
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.post(url, headers=headers, json=payload)
        if resp.status_code != 200:
            return {"error": f"Failed to initiate video generation with gemini-omni-flash-preview: {resp.text}"}
        data = resp.json()
        interaction_id = data.get("id")
        if not interaction_id:
            return {"error": f"No interaction ID returned from gemini-omni-flash-preview: {data}"}

        # Poll interaction until completed
        get_url = f"https://aiplatform.googleapis.com/v1beta1/projects/{project_id}/locations/global/interactions/{interaction_id}"
        video_b64 = None
        mime_type = "video/mp4"

        for _ in range(30):
            await asyncio.sleep(4)
            check_resp = await client.get(get_url, headers=headers)
            if check_resp.status_code != 200:
                continue
            check_data = check_resp.json()
            status = check_data.get("status")
            if status == "completed":
                for step in check_data.get("steps", []):
                    if step.get("type") == "model_output":
                        for content in step.get("content", []):
                            if content.get("data"):
                                video_b64 = content.get("data")
                                mime_type = content.get("mime_type") or "video/mp4"
                                break
                            elif content.get("bytes_base64_encoded"):
                                video_b64 = content.get("bytes_base64_encoded")
                                mime_type = content.get("mime_type") or "video/mp4"
                                break
                break
            elif status == "failed":
                return {"error": f"Video generation failed: {check_data.get('error')}"}

    if not video_b64:
        return {"error": "Video generation timed out or returned no video bytes."}

    video_bytes = base64.b64decode(video_b64)

    # 2. Save artifact using tool_context.save_artifact so it shows up in Playground's Artifacts panel
    slug = (car_name or "car_video").lower().replace(" ", "_").replace("/", "_")
    video_id = uuid.uuid4().hex[:8]
    filename = f"{slug}_{video_id}.mp4"

    artifact_part = types.Part.from_bytes(data=video_bytes, mime_type=mime_type)
    try:
        await tool_context.save_artifact(
            filename=filename,
            artifact=artifact_part,
            custom_metadata={"prompt": prompt, "model": "gemini-omni-flash-preview", "duration": duration_str},
        )
    except Exception:
        pass

    # 3. Upload the same video bytes to the public Cloud Storage bucket
    gcs_client = storage.Client(project=project_id)
    bucket = gcs_client.bucket(bucket_name)
    blob = bucket.blob(filename)
    blob.upload_from_string(video_bytes, content_type=mime_type)

    public_url = f"https://storage.googleapis.com/{bucket_name}/{filename}"

    return {
        "status": "success",
        "prompt": prompt,
        "filename": filename,
        "public_url": public_url,
        "duration": duration_str,
        "message": f"Video generated and uploaded. Public URL: {public_url}",
    }





