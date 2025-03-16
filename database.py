import asyncpg
from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import TelegramObject
from config import settings
from datetime import datetime, timedelta


class Database:
    def __init__(self):
        self.pool: asyncpg.Pool = None

    async def create_pool(self):
        self.pool = await asyncpg.create_pool(
            dsn=settings.database_url,
            min_size=5,
            max_size=20
        )

    async def init_db(self):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id BIGINT PRIMARY KEY,
                    username TEXT,
                    subscribe BOOLEAN DEFAULT FALSE,
                    subscription_start TIMESTAMP,
                    subscription_end TIMESTAMP,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)

    async def add_user(self, user_id: int, username: str):
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO users (user_id, username)
                VALUES ($1, $2)
                ON CONFLICT (user_id) DO NOTHING
            """, user_id, username)

    async def subscribe_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                sub_start = datetime.now()
                sub_end = sub_start + timedelta(days=30)
                await conn.execute("""
                    UPDATE users 
                    SET subscribe = TRUE, 
                        subscription_start = $2,
                        subscription_end = $3
                    WHERE user_id = $1
                """, user_id, sub_start, sub_end)

    async def unsubscribe_user(self, user_id: int):
        async with self.pool.acquire() as conn:
            async with conn.transaction():
                await conn.execute("""
                    UPDATE users 
                    SET subscribe = FALSE,
                        subscription_start = NULL,
                        subscription_end = NULL 
                    WHERE user_id = $1
                """, user_id)

    async def get_subscription_status(self, user_id: int):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow("""
                SELECT subscribe, subscription_start, subscription_end 
                FROM users 
                WHERE user_id = $1
            """, user_id)
        
    async def get_soon_expired_subscriptions(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
                SELECT user_id, subscription_end 
                FROM users 
                WHERE subscribe = TRUE 
                AND subscription_end BETWEEN NOW() AND NOW() + INTERVAL '3 days'
            """)

    async def get_expired_subscriptions(self):
        async with self.pool.acquire() as conn:
            return await conn.fetch("""
                SELECT user_id 
                FROM users 
                WHERE subscribe = TRUE 
                AND subscription_end < NOW()
            """)
                

class DatabaseMiddleware(BaseMiddleware):
    def __init__(self, db: Database):
        self.db = db

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        async with self.db.pool.acquire() as connection:
            data["db"] = self.db
            data["connection"] = connection
            return await handler(event, data)
