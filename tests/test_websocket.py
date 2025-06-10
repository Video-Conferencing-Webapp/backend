import pytest
import asyncio
from app.core.websocket import sio, manager

@pytest.mark.asyncio
async def test_join_room():
    # Test joining a room
    mock_sid = "test-sid-123"
    test_data = {
        "roomId": "test-room",
        "peerId": "test-peer",
        "userData": {"userName": "Test User"}
    }
    
    # Simulate join
    response = await sio._trigger_event(
        'join_room', 
        mock_sid, 
        test_data
    )
    
    assert response['roomId'] == "test-room"
    assert 'iceServers' in response
    
    # Check if peer was added
    peers = await manager.get_room_peers("test-room")
    assert "test-peer" in peers
