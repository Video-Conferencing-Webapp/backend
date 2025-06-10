import asyncio
import redis.asyncio as redis
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_redis_connection():
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    print(f"Testing Redis connection to: {redis_url}")
    
    try:
        # Try to connect
        client = redis.from_url(redis_url, encoding="utf-8", decode_responses=True)
        
        # Test ping
        pong = await client.ping()
        print(f"✓ Redis PING successful: {pong}")
        
        # Test basic operations
        await client.set("test_key", "test_value")
        value = await client.get("test_key")
        print(f"✓ Redis SET/GET successful: {value}")
        
        # Test set operations
        await client.sadd("test_set", "member1", "member2")
        members = await client.smembers("test_set")
        print(f"✓ Redis SADD/SMEMBERS successful: {members}")
        
        # Cleanup
        await client.delete("test_key", "test_set")
        print("✓ Redis cleanup successful")
        
        await client.close()
        print("\n✅ All Redis operations successful!")
        
    except redis.ConnectionError as e:
        print(f"\n❌ Redis connection failed: {e}")
        print("\nPossible solutions:")
        print("1. Make sure Redis is running")
        print("2. Check if Redis is accessible at the configured URL")
        print("3. If running locally, change REDIS_URL to 'redis://localhost:6379/0'")
        print("4. If using Docker, make sure the Redis container is running")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")

if __name__ == "__main__":
    asyncio.run(test_redis_connection())