from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from contextlib import asynccontextmanager
from models import MoveRequest, ModeRequest
from ferb import Ferb
from fastapi.staticfiles import StaticFiles

robot = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Initialize the robot on startup.
    """
    global robot
    robot = Ferb()
    robot.start_dog_thread()
    yield
    robot.cleanup()


app = FastAPI(
    title="Ferb API",
    description="API para controlar al robot FERB",
    version="1.0",
    lifespan=lifespan,
)

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.post("/move/")
async def move(move_request: MoveRequest):
    """
    Move the robot in the specified direction.
    """
    if robot is None:
        return {"message": "El robot no se ha inicializado"}

    if robot.current_mode == "manual":
        print(f"Moving robot - {move_request.direction} at speed {move_request.speed}")
        robot.move(move_request.direction, move_request.speed)
        return {
            "message": f"Se movió al robot - {move_request.direction} a velocidad {move_request.speed}"
        }

    else:
        return {"message": "El modo actual no permite el movimiento manual"}


@app.post("/mode/")
async def mode(mode_request: ModeRequest):
    """
    Change the robot's mode.
    """
    if robot is None:
        return {"message": "El robot no se ha inicializado"}
    robot.current_mode = mode_request.mode
    return {"message": f"Changing mode to {mode_request.mode}"}


@app.get("/camera/stream")
async def camera_stream():
    """
    Stream de la cámara del robot en tiempo real (MJPEG).
    """
    if robot is None:
        return {"message": "El robot no se ha inicializado"}
    try:
        return StreamingResponse(
            robot.camera_stream(), media_type="multipart/x-mixed-replace; boundary=frame"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Camera error: {e}")
