import uuid
from fastapi import FastAPI, Request
import mysql.connector

from fastapi.responses import FileResponse

app = FastAPI()

def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="root",
        database="dashboard_db"
    )

@app.get("/dashboard")
def serve_dashboard(batch_id: str):
    # Serve the HTML page
    return FileResponse("dashboard.html")

# -------------------------------
# Upload endpoint
# -------------------------------
@app.post("/upload-data")
async def upload_data(request: Request):
    body = await request.json()
    batch_id = str(uuid.uuid4())

    print("Received payload:")
    for item in body :
        print (item)
        print("\n")
        
    conn = get_db_connection()
    cursor = conn.cursor()

    for item in body:
        cursor.execute("""
            INSERT INTO comparisons (
                batch_id,
                dealer_name, car_mark, car_model, car_model_variant,
                car_model_sub_variant, engine_name, kw, hp, transmission,
                drive, fuel_type, year, vehicle_type, seats, emission_standard,
                co2_level_combined, delivery_cost_eur, condition_type,
                condition_id, condition_created_at, condition_updated_at,
                value_original, value_extracted, value_eur_original,
                value_eur_extracted, remark_original, remark_extracted
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            batch_id,
            item.get("dealer_name"),
            item.get("car_mark"),
            item.get("car_model"),
            item.get("car_model_variant"),
            item.get("car_model_sub_variant"),
            item.get("engine_name"),
            item.get("kw"),
            item.get("hp"),
            item.get("transmission"),
            item.get("drive"),
            item.get("fuel_type"),
            item.get("year"),
            item.get("vehicle_type"),
            item.get("seats"),
            item.get("emission_standard"),
            item.get("co2_level_combined"),
            item.get("delivery_cost_eur"),
            item.get("condition_type"),
            item.get("condition_id"),
            item.get("condition_created_at"),
            item.get("condition_updated_at"),
            item.get("value", {}).get("original"),
            item.get("value", {}).get("extracted"),
            item.get("value_eur", {}).get("original"),
            item.get("value_eur", {}).get("extracted"),
            item.get("remark", {}).get("original"),
            item.get("remark", {}).get("extracted"),
        ))

    conn.commit()
    cursor.close()
    conn.close()

    dashboard_url = f"http://localhost:5000/dashboard?batch_id={batch_id}"
    return {"message": "Data stored", "items_count": len(body), "dashboard_url": dashboard_url}

# -------------------------------
# Get data endpoint
# -------------------------------
@app.get("/get-data")
def get_data(batch_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM comparisons WHERE batch_id = %s", (batch_id,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"batch_id": batch_id, "data": rows}


# -------------------------------
# Rules endpoint (returns long string)
# -------------------------------
@app.get("/rules")
def get_rules():
    rules_text = """
    These are the rules for comparison:
    1. Value_original vs Value_extracted must be checked for mismatches.
    2. Value_eur_original vs Value_eur_extracted should be validated.
    3. Remarks need to be compared and flagged if inconsistent.
    4. Other domain-specific rules can be added here...
    """
    return {"rules": rules_text.strip()}
