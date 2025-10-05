"""FastAPI application for LiveKit Voice AI agent.

This application provides REST API endpoints to:
- Create LiveKit rooms
- Generate access tokens for participants
- Health check endpoint
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from livekit import api

from config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="LiveKit Voice AI API",
    description="REST API for managing LiveKit voice agent rooms and tokens",
    version="1.0.0",
)


# Request/Response models
class CreateRoomRequest(BaseModel):
    """Request model for creating a room."""

    room_name: str
    empty_timeout: Optional[int] = 300  # 5 minutes default
    max_participants: Optional[int] = 10


class CreateRoomResponse(BaseModel):
    """Response model for room creation."""

    room_name: str
    room_sid: str
    success: bool


class GenerateTokenRequest(BaseModel):
    """Request model for generating access tokens."""

    room_name: str
    participant_identity: str
    participant_name: Optional[str] = None


class GenerateTokenResponse(BaseModel):
    """Response model for token generation."""

    token: str
    room_name: str
    participant_identity: str


# Initialize LiveKit API client
livekit_api = api.LiveKitAPI(
    url=settings.LIVEKIT_URL,
    api_key=settings.LIVEKIT_API_KEY,
    api_secret=settings.LIVEKIT_API_SECRET,
)


@app.get("/")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "LiveKit Voice AI API",
        "version": "1.0.0",
    }


@app.post("/rooms", response_model=CreateRoomResponse)
async def create_room(request: CreateRoomRequest):
    """Create a new LiveKit room.

    Args:
        request: Room creation parameters.

    Returns:
        CreateRoomResponse: Room details including SID.

    Raises:
        HTTPException: If room creation fails.
    """
    try:
        logger.info(f"Creating room: {request.room_name}")

        # Create room with specified options
        room = await livekit_api.room.create_room(
            api.CreateRoomRequest(
                name=request.room_name,
                empty_timeout=request.empty_timeout,
                max_participants=request.max_participants,
            )
        )

        logger.info(f"Room created successfully: {room.name} (SID: {room.sid})")

        return CreateRoomResponse(
            room_name=room.name,
            room_sid=room.sid,
            success=True,
        )

    except Exception as e:
        logger.error(f"Failed to create room: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to create room: {str(e)}")


@app.post("/token", response_model=GenerateTokenResponse)
async def generate_token(request: GenerateTokenRequest):
    """Generate an access token for a participant to join a room.

    Args:
        request: Token generation parameters.

    Returns:
        GenerateTokenResponse: Access token and participant details.

    Raises:
        HTTPException: If token generation fails.
    """
    try:
        logger.info(
            f"Generating token for participant {request.participant_identity} in room {request.room_name}"
        )

        # Create access token with permissions
        token = (
            api.AccessToken(
                api_key=settings.LIVEKIT_API_KEY,
                api_secret=settings.LIVEKIT_API_SECRET,
            )
            .with_identity(request.participant_identity)
            .with_name(request.participant_name or request.participant_identity)
            .with_grants(
                api.VideoGrants(
                    room_join=True,
                    room=request.room_name,
                    can_publish=True,
                    can_subscribe=True,
                )
            )
        )

        jwt_token = token.to_jwt()

        logger.info(f"Token generated successfully for {request.participant_identity}")

        return GenerateTokenResponse(
            token=jwt_token,
            room_name=request.room_name,
            participant_identity=request.participant_identity,
        )

    except Exception as e:
        logger.error(f"Failed to generate token: {str(e)}")
        raise HTTPException(
            status_code=500, detail=f"Failed to generate token: {str(e)}"
        )


@app.get("/rooms")
async def list_rooms():
    """List all active LiveKit rooms.

    Returns:
        List of active rooms with their details.
    """
    try:
        logger.info("Listing all rooms")

        rooms = await livekit_api.room.list_rooms(api.ListRoomsRequest())

        return {
            "rooms": [
                {
                    "name": room.name,
                    "sid": room.sid,
                    "num_participants": room.num_participants,
                    "creation_time": room.creation_time,
                }
                for room in rooms.rooms
            ]
        }

    except Exception as e:
        logger.error(f"Failed to list rooms: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list rooms: {str(e)}")


@app.delete("/rooms/{room_name}")
async def delete_room(room_name: str):
    """Delete a LiveKit room.

    Args:
        room_name: Name of the room to delete.

    Returns:
        Success message.
    """
    try:
        logger.info(f"Deleting room: {room_name}")

        await livekit_api.room.delete_room(api.RoomName(room=room_name))

        logger.info(f"Room deleted successfully: {room_name}")

        return {"success": True, "message": f"Room {room_name} deleted successfully"}

    except Exception as e:
        logger.error(f"Failed to delete room: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete room: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    # Validate settings before starting
    settings.validate()

    logger.info("Starting FastAPI server...")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
