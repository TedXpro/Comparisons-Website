import uuid
import os
from fastapi import FastAPI, HTTPException, Request, UploadFile, Depends
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
import secrets
import psycopg2
import psycopg2.extras
from dotenv import load_dotenv
import bcrypt

# Load environment variables
load_dotenv()

app = FastAPI()

# -------------------------------
# Database connection
# -------------------------------
def get_db_connection():
    try:
        database_url = os.getenv("DATABASE_URL")
        if not database_url:
            raise HTTPException(status_code=500, detail="Database URL not found in environment")
        
        conn = psycopg2.connect(database_url)
        return conn
    except psycopg2.Error as e:
        print(f"Database connection error: {e}")
        raise HTTPException(status_code=500, detail=f"Database connection failed: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

# -------------------------------
# Basic Auth setup
# -------------------------------
security = HTTPBasic()

def get_current_user(credentials: HTTPBasicCredentials = Depends(security)):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        # Step 1: Fetch the user from the database
        cursor.execute("SELECT password_hash FROM users WHERE username = %s", (credentials.username,))
        user_record = cursor.fetchone()
        
        if not user_record:
            # User not found
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        stored_password_hash = user_record[0].encode('utf-8')
        
        # Step 2: Verify the provided password against the stored hash
        if not bcrypt.checkpw(credentials.password.encode('utf-8'), stored_password_hash):
            # Password does not match
            raise HTTPException(
                status_code=401,
                detail="Unauthorized: Incorrect username or password",
                headers={"WWW-Authenticate": "Basic"},
            )
        
        return credentials.username
    finally:
        cursor.close()
        conn.close()

# -------------------------------
# User Registration Endpoint (for demonstration)
# -------------------------------
@app.post("/register")
async def register_user(request: Request):
    try:
        user_data = await request.json()
        username = user_data.get("username")
        password = user_data.get("password")

        if not username or not password:
            raise HTTPException(status_code=400, detail="Username and password are required.")

        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

        conn = get_db_connection()
        cursor = conn.cursor()
        try:
            # Insert the new user into the database
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s)",
                           (username, hashed_password.decode('utf-8')))
            conn.commit()
            return {"message": "User registered successfully."}
        except psycopg2.IntegrityError:
            conn.rollback()
            raise HTTPException(status_code=409, detail="Username already exists.")
        except Exception as e:
            conn.rollback()
            raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")
        finally:
            cursor.close()
            conn.close()
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid request body: {str(e)}")


# -------------------------------
# Serve dashboard HTML (protected)
# -------------------------------
@app.get("/dashboard")
def serve_dashboard(batch_id: str, user: str = Depends(get_current_user)):
    return FileResponse("dashboard.html")

# -------------------------------
# Upload comparisons endpoint
# -------------------------------
@app.post("/upload-data")
async def upload_data(request: Request):
    body = await request.json()
    
    if not body or not isinstance(body, list) or all(not bool(item) for item in body):
        raise HTTPException(status_code=400, detail="Empty or invalid payload. No data stored.")
    
    batch_id = str(uuid.uuid4())

    print("Received payload:")
    for item in body:
        print(item)
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

    dashboard_url = f"https://comparisons-website.onrender.com/dashboard?batch_id={batch_id}"
    return {"message": "Data stored", "items_count": len(body), "dashboard_url": dashboard_url}

# -------------------------------
# Get comparisons by batch_id
# -------------------------------
@app.get("/get-data")
def get_data(batch_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    cursor.execute("SELECT * FROM comparisons WHERE batch_id = %s", (batch_id,))
    rows = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"batch_id": batch_id, "data": rows}

# -------------------------------
# Store rules endpoint
# -------------------------------
@app.post("/rules")
async def store_rule(request: Request):
    rule = await request.json()
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        sql = "INSERT INTO rules (batch_id, rule_text) VALUES (%s, %s)"
        cursor.execute(sql, (rule.get("batch_id"), rule.get("rules")))
        conn.commit()
        return {"status": "success", "message": "Rule stored successfully."}
    except Exception as e:
        conn.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# -------------------------------
# Get rules by batch_id
# -------------------------------
@app.get("/rules")
def get_rules(batch_id: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        sql = "SELECT * FROM rules WHERE batch_id = %s"
        cursor.execute(sql, (batch_id,))
        results = cursor.fetchall()
        if not results:
            return {"rules": []}
        return {"rules": [row["rule_text"] for row in results]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        cursor.close()
        conn.close()

# ==================================================
# PDF Upload + Serve
# ==================================================
UPLOAD_DIR = "/app/uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/upload-pdf")
async def upload_pdf(file: UploadFile):
    try:
        file_id = str(uuid.uuid4()) + ".pdf"
        file_path = os.path.join(UPLOAD_DIR, file_id)

        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        public_url = f"https://{os.getenv('RENDER_EXTERNAL_HOSTNAME', 'localhost')}/files/{file_id}"
        return {"message": "File uploaded successfully", "url": public_url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"File upload failed: {str(e)}")

@app.get("/files/{file_name}")
def serve_file(file_name: str):
    file_path = os.path.join(UPLOAD_DIR, file_name)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path, media_type="application/pdf")
