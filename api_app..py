from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import uuid
from typing import List
import os

DATABASE_URI = os.getenv("DATABASE_URL") 
engine = create_engine(DATABASE_URI, connect_args={"sslmode": "require"})
app = FastAPI(title="Peru Geotech API")

# 2. Data Models (What the API expects to receive)
class CalculationInput(BaseModel):
    session_id: str
    soil_id: int
    project_id: int = 1  # Default to our Demo Project
    slope_angle: float
    z_depth: float = 5.0
    water_table_ratio: float = 0.0

# 3. Endpoint: Save and Trigger Calculation
@app.post("/calculate")
async def calculate_slope(data: CalculationInput):
    insert_query = text("""
        INSERT INTO calculations (session_id, project_id, soil_id, slope_angle, z_depth, water_table_ratio)
        VALUES (:sess, :proj, :soil, :slope, :z, :water)
        RETURNING id;
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(insert_query, {
                "sess": data.session_id,
                "proj": data.project_id,
                "soil": data.soil_id,
                "slope": data.slope_angle,
                "z": data.z_depth,
                "water": data.water_table_ratio
            })
            calc_id = result.fetchone()[0]
            conn.commit()
            return {"status": "success", "calculation_id": calc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Endpoint: Get History (Using Advanced SQL Window Function)
@app.get("/history/{session_id}")
async def get_history(session_id: str):
    # This query uses your VIEW and filters by session
    # It only takes the 3 most recent for privacy
    history_query = text("""
        SELECT * FROM (
            SELECT *, 
            ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY calc_id DESC) as rank
            FROM v_slope_safety
            WHERE session_id = :sess
        ) ranked_results
        WHERE rank <= 3;
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(history_query, {"sess": session_id})
            rows = result.fetchall()
            
            # Convert SQL rows to a list of dictionaries for JSON response
            history = []
            for row in rows:
                history.append({
                    "material": row.material_name,
                    "project": row.project_name,
                    "fs": round(row.factor_of_safety, 3),
                    "status": "Safe" if row.factor_of_safety > 1.5 else "Warning" if row.factor_of_safety > 1.0 else "Critical"
                })
            return {"session_id": session_id, "recent_calculations": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)