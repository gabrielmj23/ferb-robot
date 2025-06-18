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
async def move(move_request: MoveRequest, continuous: bool = False):
    """
    Move the robot in the specified direction.
    Si continuous=True, el robot se moverá continuamente hasta recibir otra orden o stop.
    """
    if robot is None:
        return {"message": "El robot no se ha inicializado"}

    if robot.current_mode == "manual":
        print(
            f"Moving robot - {move_request.direction} at speed {move_request.speed} (continuous={continuous})"
        )
        robot.move(move_request.direction, move_request.speed, continuous=continuous)
        return {
            "message": f"Se movió al robot - {move_request.direction} a velocidad {move_request.speed} (continuous={continuous})"
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
    print(f"Changing mode to {mode_request.mode}")
    robot.current_mode = mode_request.mode
    if mode_request.mode == "manual":
        robot.stop_dog_thread()
    else:
        robot.start_dog_thread()
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
            robot.camera_stream(),
            media_type="multipart/x-mixed-replace; boundary=frame",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Camera error: {e}")


@app.get("/gps/stream")
async def gps_stream():
    """
    Stream de datos GPS en tiempo real (Server-Sent Events).
    """
    if robot is None:
        return {"message": "El robot no se ha inicializado"}
    try:
        return StreamingResponse(robot.gps_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"GPS error: {e}")


@app.get("/compass/stream")
async def compass_stream():
    """
    Stream de datos de la brújula en tiempo real (Server-Sent Events).
    """
    if robot is None:
        return {"message": "El robot no se ha inicializado"}
    try:
        return StreamingResponse(robot.compass_stream(), media_type="text/event-stream")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Compass error: {e}")
