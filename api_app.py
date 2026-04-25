from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from sqlalchemy import create_engine, text
import uuid
from typing import List
import os

DATABASE_URL = os.getenv("DATABASE_URL") 
engine = create_engine(DATABASE_URL, connect_args={"sslmode": "require"})
app = FastAPI(title="Peru Geotech API")

# 2. Data Models
class CalculationInput(BaseModel):
    session_id: str
    soil_id: int
    project_id: int = 1  
    slope_angle: float
    z_depth: float = 5.0
    water_table_ratio: float = 0.0
    kh_seismic: float = 0.0  # Added default kh_seismic (Static by default)

# 3. Endpoint: Save and Trigger Calculation
@app.post("/calculate")
async def calculate_slope(data: CalculationInput):
    # Added kh_seismic to the INSERT statement
    insert_query = text("""
        INSERT INTO calculations (session_id, project_id, soil_id, slope_angle, z_depth, water_table_ratio, kh_seismic)
        VALUES (:sess, :proj, :soil, :slope, :z, :water, :kh)
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
                "water": data.water_table_ratio,
                "kh": data.kh_seismic  # Mapping the new field
            })
            calc_id = result.fetchone()[0]
            conn.commit()
            return {"status": "success", "calculation_id": calc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# 4. Endpoint: Get History
@app.get("/history/{session_id}")
async def get_history(session_id: str):
    history_query = text("""
        SELECT * FROM (
            SELECT *, 
            ROW_NUMBER() OVER (PARTITION BY session_id ORDER BY calc_id DESC) as rank
            FROM v_slope_safety
            WHERE session_id = :sess
        ) ranked_results
        WHERE rank <= 5; -- Increased to 5 to see more comparisons
    """)
    
    try:
        with engine.connect() as conn:
            result = conn.execute(history_query, {"sess": session_id})
            rows = result.fetchall()
            
            history = []
            for row in rows:
                # Determine status based on Peruvian standards (E.050)
                # Seismic FS often has a lower threshold (1.1) than Static (1.5)
                fs_val = row.factor_of_safety
                is_seismic = row.kh_seismic > 0
                
                status = "Safe"
                if is_seismic:
                    if fs_val < 1.1: status = "Critical"
                    elif fs_val < 1.3: status = "Warning"
                else:
                    if fs_val < 1.3: status = "Critical"
                    elif fs_val < 1.5: status = "Warning"

                history.append({
                    "material": row.material_name,
                    "project": row.project_name,
                    "kh": row.kh_seismic, # Returning kh so the dashboard can label it
                    "fs": round(fs_val, 3),
                    "status": status
                })
            return {"session_id": session_id, "recent_calculations": history}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
