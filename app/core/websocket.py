import json
from typing import Dict, Set
import socketio
from app.core.config import settings
from app.core.redis_client import redis_client
import logging

logger = logging.getLogger(__name__)

# Create Socket.IO server
sio = socketio.AsyncServer(
    async_mode='asgi',
    cors_allowed_origins=settings.BACKEND_CORS_ORIGINS,
    logger=True,
    engineio_logger=True
)

# Store active connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[str]] = {}  # room_id -> set of peer_ids
        self.peer_to_room: Dict[str, str] = {}  # peer_id -> room_id
        self.peer_to_sid: Dict[str, str] = {}  # peer_id -> socket_id
        self.peer_user_data: Dict[str, dict] = {}  # peer_id -> user_data
        self.room_hosts: Dict[str, str] = {}  # room_id -> host_peer_id
        
    async def connect(self, sid: str, peer_id: str, room_id: str, user_data: dict = None, is_host: bool = False):
        """Add peer to room"""
        if room_id not in self.active_connections:
            self.active_connections[room_id] = set()
        
        self.active_connections[room_id].add(peer_id)
        self.peer_to_room[peer_id] = room_id
        self.peer_to_sid[peer_id] = sid
        if user_data:
            self.peer_user_data[peer_id] = user_data
        
        # Set as host if this is the first peer or explicitly marked as host
        if is_host or room_id not in self.room_hosts:
            self.room_hosts[room_id] = peer_id
            await redis_client.hset("room:host", room_id, peer_id)
        
        # Store in Redis for scaling
        await redis_client.sadd(f"room:{room_id}:peers", peer_id)
        await redis_client.hset("peer:room", peer_id, room_id)
        await redis_client.hset("peer:sid", peer_id, sid)
        if user_data:
            await redis_client.hset("peer:userdata", peer_id, json.dumps(user_data))
        
    async def disconnect(self, peer_id: str):
        """Remove peer from room"""
        if peer_id in self.peer_to_room:
            room_id = self.peer_to_room[peer_id]
            
            if room_id in self.active_connections:
                self.active_connections[room_id].discard(peer_id)
                if not self.active_connections[room_id]:
                    del self.active_connections[room_id]
                    # Remove host when room is empty
                    if room_id in self.room_hosts:
                        del self.room_hosts[room_id]
                        await redis_client.hdel("room:host", room_id)
            
            del self.peer_to_room[peer_id]
            
            if peer_id in self.peer_to_sid:
                del self.peer_to_sid[peer_id]
                
            if peer_id in self.peer_user_data:
                del self.peer_user_data[peer_id]
            
            # Remove from Redis
            await redis_client.srem(f"room:{room_id}:peers", peer_id)
            await redis_client.hdel("peer:room", peer_id)
            await redis_client.hdel("peer:sid", peer_id)
            await redis_client.hdel("peer:userdata", peer_id)
            
    async def get_room_peers(self, room_id: str) -> Set[str]:
        """Get all peers in a room"""
        # Try local first, then Redis
        if room_id in self.active_connections:
            return self.active_connections[room_id]
        
        peers = await redis_client.smembers(f"room:{room_id}:peers")
        return set(peers) if peers else set()
        
    async def get_room_participants(self, room_id: str) -> Dict[str, dict]:
        """Get all participants in a room with their user data"""
        peers = await self.get_room_peers(room_id)
        participants = {}
        
        for peer_id in peers:
            # Try local first, then Redis
            user_data = self.peer_user_data.get(peer_id)
            if not user_data:
                # Try Redis
                redis_data = await redis_client.hget("peer:userdata", peer_id)
                if redis_data:
                    try:
                        user_data = json.loads(redis_data)
                        self.peer_user_data[peer_id] = user_data  # Cache locally
                    except json.JSONDecodeError:
                        user_data = {}
                else:
                    user_data = {}
            
            participants[peer_id] = user_data
            
        return participants
    
    async def get_room_host(self, room_id: str) -> str:
        """Get the host peer ID for a room"""
        # Try local first, then Redis
        if room_id in self.room_hosts:
            return self.room_hosts[room_id]
        
        host_peer_id = await redis_client.hget("room:host", room_id)
        if host_peer_id:
            self.room_hosts[room_id] = host_peer_id
        
        return host_peer_id

manager = ConnectionManager()

# Socket.IO Events
@sio.event
async def connect(sid, environ, auth):
    """Handle new connection"""
    logger.info(f"Client {sid} connected")
    await sio.emit('connected', {'sid': sid}, room=sid)

@sio.event
async def disconnect(sid):
    """Handle disconnection"""
    logger.info(f"Client {sid} disconnected")
    # Find peer_id by sid and clean up
    for peer_id, peer_sid in list(manager.peer_to_sid.items()):
        if peer_sid == sid:
            room_id = manager.peer_to_room.get(peer_id)
            await manager.disconnect(peer_id)
            
            if room_id:
                # Notify others in room
                await sio.emit('peer_disconnected', {
                    'peerId': peer_id
                }, room=room_id, skip_sid=sid)
            break

@sio.event
async def join_room(sid, data):
    """Join a room"""
    room_id = data.get('roomId')
    peer_id = data.get('peerId')
    user_data = data.get('userData', {})
    
    if not room_id or not peer_id:
        return {'error': 'Missing roomId or peerId'}
    
    # Check if this is the first peer (will be the host)
    existing_peers = await manager.get_room_peers(room_id)
    is_first_peer = len(existing_peers) == 0
    
    # Join Socket.IO room
    await sio.enter_room(sid, room_id)
    await manager.connect(sid, peer_id, room_id, user_data, is_host=is_first_peer)
    
    # Get existing participants with their user data (after connection to exclude self)
    existing_participants = await manager.get_room_participants(room_id)
    existing_participants.pop(peer_id, None)  # Remove self
    
    # Get room host
    room_host_id = await manager.get_room_host(room_id)
    
    # Notify existing peers
    await sio.emit('peer_joined', {
        'peerId': peer_id,
        'userData': user_data
    }, room=room_id, skip_sid=sid)
    
    logger.info(f"Peer {peer_id} joined room {room_id} as {'host' if is_first_peer else 'participant'}")
    
    return {
        'roomId': room_id,
        'participants': existing_participants,  # Return participants with user data
        'roomHostId': room_host_id,  # Return the actual room host peer ID
        'iceServers': [
            {
                'urls': f'turn:{settings.TURN_SERVER_URL}',
                'username': settings.TURN_USERNAME,
                'credential': settings.TURN_PASSWORD
            },
            {
                'urls': 'stun:stun.l.google.com:19302'
            }
        ]
    }

@sio.event
async def leave_room(sid, data):
    """Leave a room"""
    peer_id = data.get('peerId')
    
    if peer_id and peer_id in manager.peer_to_room:
        room_id = manager.peer_to_room[peer_id]
        await sio.leave_room(sid, room_id)
        await manager.disconnect(peer_id)
        
        # Notify others
        await sio.emit('peer_left', {
            'peerId': peer_id
        }, room=room_id, skip_sid=sid)
        
        logger.info(f"Peer {peer_id} left room {room_id}")

# WebRTC Signaling Events
@sio.event
async def signal(sid, data):
    """Relay WebRTC signaling messages"""
    from_peer = data.get('from')
    to_peer = data.get('to')
    signal_data = data.get('signal')
    
    if not all([from_peer, to_peer, signal_data]):
        return {'error': 'Missing required fields'}
    
    # Get target socket ID
    target_sid = manager.peer_to_sid.get(to_peer)
    
    if target_sid:
        await sio.emit('signal', {
            'from': from_peer,
            'signal': signal_data
        }, room=target_sid)
        logger.debug(f"Relayed signal from {from_peer} to {to_peer}")
    else:
        logger.warning(f"Target peer {to_peer} not found")
        return {'error': 'Target peer not found'}

# Screen Sharing Events
@sio.event
async def start_screen_share(sid, data):
    """Notify room about screen sharing"""
    peer_id = data.get('peerId')
    room_id = manager.peer_to_room.get(peer_id)
    
    if room_id:
        await sio.emit('screen_share_started', {
            'peerId': peer_id
        }, room=room_id, skip_sid=sid)

@sio.event
async def stop_screen_share(sid, data):
    """Notify room about screen sharing stop"""
    peer_id = data.get('peerId')
    room_id = manager.peer_to_room.get(peer_id)
    
    if room_id:
        await sio.emit('screen_share_stopped', {
            'peerId': peer_id
        }, room=room_id, skip_sid=sid)

# Remote Control Events
@sio.event
async def request_remote_control(sid, data):
    """Request remote control of shared screen"""
    requester_id = data.get('requesterId')
    target_id = data.get('targetId')
    
    target_sid = manager.peer_to_sid.get(target_id)
    if target_sid:
        await sio.emit('remote_control_requested', {
            'requesterId': requester_id
        }, room=target_sid)

@sio.event
async def remote_control_response(sid, data):
    """Respond to remote control request"""
    requester_id = data.get('requesterId')
    granted = data.get('granted')
    
    requester_sid = manager.peer_to_sid.get(requester_id)
    if requester_sid:
        await sio.emit('remote_control_response', {
            'granted': granted
        }, room=requester_sid)

@sio.event
async def remote_control_event(sid, data):
    """Relay remote control events (mouse/keyboard)"""
    target_id = data.get('targetId')
    event_type = data.get('type')
    event_data = data.get('data')
    
    target_sid = manager.peer_to_sid.get(target_id)
    if target_sid:
        await sio.emit('remote_control_event', {
            'type': event_type,
            'data': event_data
        }, room=target_sid)

# Chat Message Events
@sio.event
async def send_chat_message(sid, data):
    """Handle incoming chat message and broadcast to room"""
    room_id = data.get('roomId')
    user_id = data.get('userId')
    
    logger.info(f"📨 Received chat message: {data}")
    logger.info(f"🏠 Current peer_to_room mapping: {manager.peer_to_room}")
    logger.info(f"🔍 Looking for user_id: {user_id} in peer_to_room")
    
    if not room_id:
        logger.warning(f"Chat message missing roomId: {data}")
        return {'error': 'Missing roomId'}
    
    if not user_id:
        logger.warning(f"Chat message missing userId: {data}")
        return {'error': 'Missing userId'}
    
    # Get the room from connection manager
    if user_id in manager.peer_to_room:
        logger.info(f"✅ User {user_id} found in room {manager.peer_to_room[user_id]}")
        # Broadcast message to all users in the room except sender
        await sio.emit('chat_message', data, room=room_id, skip_sid=sid)
        logger.info(f"📤 Chat message from {user_id} broadcasted to room {room_id}")
        return {'success': True}
    else:
        logger.warning(f"❌ User {user_id} not found in any room. Current peer_to_room: {manager.peer_to_room}")
        return {'error': 'User not in room'}

# Media State Events
@sio.event
async def update_media_state(sid, data):
    """Handle media state updates (audio/video on/off)"""
    peer_id = data.get('peerId')
    media_state = data.get('mediaState', {})
    
    # Extract media state properties
    audio_enabled = media_state.get('audioEnabled')
    video_enabled = media_state.get('videoEnabled')
    hand_raised = media_state.get('handRaised')
    
    if not peer_id:
        return {'error': 'Missing peerId'}
    
    room_id = manager.peer_to_room.get(peer_id)
    if not room_id:
        return {'error': 'Peer not in any room'}
    
    # Update the peer's user data with only non-None values
    if peer_id in manager.peer_user_data:
        update_data = {}
        if audio_enabled is not None:
            update_data['audioEnabled'] = audio_enabled
        if video_enabled is not None:
            update_data['videoEnabled'] = video_enabled
        if hand_raised is not None:
            update_data['handRaised'] = hand_raised
            
        manager.peer_user_data[peer_id].update(update_data)
        # Update in Redis
        await redis_client.hset("peer:userdata", peer_id, json.dumps(manager.peer_user_data[peer_id]))
    
    # Notify other peers in the room with only the changed properties
    emit_data = {'peerId': peer_id}
    if audio_enabled is not None:
        emit_data['audioEnabled'] = audio_enabled
    if video_enabled is not None:
        emit_data['videoEnabled'] = video_enabled
    if hand_raised is not None:
        emit_data['handRaised'] = hand_raised
        
    await sio.emit('media_state_updated', emit_data, room=room_id, skip_sid=sid)
    
    logger.debug(f"Media state updated for peer {peer_id}: {emit_data}")
    return {'success': True}
