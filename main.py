from fastapi import FastAPI
from models import MoveRequest, ModeRequest

app = FastAPI(
    title="Ferb API", description="API para controlar al robot FERB", version="1.0"
)

current_mode = "manual"  # Estado inicial del robot


@app.post("/move/")
async def move(move_request: MoveRequest):
    """
    Move the robot in the specified direction.
    """
    # Here you would add the logic to control the robot
    if current_mode == "manual":
        # Logic to move the robot
        return {"message": f"Moving {move_request.direction}"}

    else:
        return {"message": "El modo actual no permite el movimiento manual"}


@app.post("/mode/")
async def mode(mode_request: ModeRequest):
    """
    Change the robot's mode.
    """
    global current_mode
    current_mode = mode_request.mode
    return {"message": f"Changing mode to {mode_request.mode}"}
