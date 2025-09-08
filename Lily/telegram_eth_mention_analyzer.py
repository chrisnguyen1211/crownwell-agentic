#!/usr/bin/env python3
"""
Telegram ETH Mention Analyzer and Searcher
- Provides ETHMentionAnalyzer for simple sentiment scoring
- Provides TelegramETHMentionSearcher using Telethon to fetch real data
- Falls back to sample data if Telethon or network access is unavailable
"""

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional

# Require Telethon (fail fast - no sample fallback)
from telethon import TelegramClient
from telethon.errors import FloodWaitError, RPCError
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.types import Message
TELETHON_AVAILABLE = True


class ETHMentionAnalyzer:
    """Simplified ETH mention analyzer"""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        # Lowercase keywords for quick contains matching
        self.positive_words = [
            'bull', 'moon', 'pump', 'buy', 'long', 'hodl', 'diamond', 'rocket',
            'bullish', 'breakout', 'support holding'
        ]
        self.negative_words = [
            'bear', 'dump', 'sell', 'short', 'crash', 'rekt', 'fud', 'bearish',
            'breakdown', 'resistance rejected'
        ]

    def analyze_sentiment(self, text: str) -> float:
        """Return a coarse sentiment score in [-1, 1]."""
        if not text:
            return 0.0
        text_lower = text.lower()
        pos = sum(1 for w in self.positive_words if w in text_lower)
        neg = sum(1 for w in self.negative_words if w in text_lower)
        if pos == 0 and neg == 0:
            return 0.0
        return max(-1.0, min(1.0, (pos - neg) / max(1.0, pos + neg)))


class TelegramETHMentionSearcher:
    """Telethon-based Telegram ETH mention searcher (no fallback)."""
    
    def __init__(self, api_id: int, api_hash: str, session_name: str) -> None:
        self.api_id = api_id
        self.api_hash = api_hash
        self.session_name = session_name
        self.client: Optional[TelegramClient] = None
        self.logger = logging.getLogger(__name__)
        self.eth_analyzer = ETHMentionAnalyzer()
    
    async def initialize(self) -> bool:
        """Initialize the Telethon client, return True on success."""
        if not TELETHON_AVAILABLE:
            raise RuntimeError("Telethon not available. Install telethon and set TELEGRAM_API_ID/TELEGRAM_API_HASH.")
        try:
            self.client = TelegramClient(self.session_name, self.api_id, self.api_hash)
            await self.client.start()
            self.logger.info("Telegram client initialized (Telethon)")
            return True
        except Exception as exc:
            self.logger.error(f"Failed to initialize Telegram client: {exc}")
            self.client = None
            return False

    async def disconnect(self) -> None:
        if self.client:
            try:
                await self.client.disconnect()
            except Exception:
                pass
            self.logger.info("Telegram client disconnected")

    async def search_multiple_channels(
        self,
                                     channels: List[str], 
        query: str = "ETH",
        limit_per_channel: int = 20,
        days_back: int = 1,
        per_channel_delay_seconds: float = 2.0,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search each channel for messages mentioning ETH.
        Returns a dict: {channel_username: [message_dict, ...]}
        """
        results: Dict[str, List[Dict[str, Any]]] = {}
        if self.client is None or not TELETHON_AVAILABLE:
            raise RuntimeError("Telethon client not initialized. Install telethon and set TELEGRAM_API_ID/TELEGRAM_API_HASH.")

        # Real fetching via Telethon
        assert self.client is not None
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days_back)
        for channel in channels:
            try:
                entity = await self.client.get_entity(channel)
                # Try to fetch channel metadata (subscribers, title)
                try:
                    full = await self.client(GetFullChannelRequest(entity))
                    subscribers = getattr(full.full_chat, 'participants_count', 0) or 0
                    title = getattr(entity, 'title', None)
                except Exception:
                    subscribers = 0
                    title = getattr(entity, 'title', None)

                messages: List[Dict[str, Any]] = []
                async for msg in self.client.iter_messages(entity, limit=limit_per_channel, search=query):
                    if not isinstance(msg, Message):
                        continue
                    if msg.date and msg.date.replace(tzinfo=timezone.utc) < cutoff_dt:
                        break
                    text = msg.message or ""
                    if not text:
                        continue
                    if not self._mentions_eth(text):
                        continue
                    # Build record
                    messages.append({
                        'platform': 'telegram',
                        'message_id': msg.id,
                        'channel_id': getattr(entity, 'id', 0) or 0,
                        'channel_username': getattr(entity, 'username', channel) or channel,
                        'channel_title': title,
                        'channel_subscribers': subscribers,
                        'message_text': text,
                        'message_views': getattr(msg, 'views', 0) or 0,
                        'forwards': getattr(msg, 'forwards', 0) or 0,
                        'replies': (getattr(msg, 'replies', None).replies if getattr(msg, 'replies', None) else 0),
                        'reactions': {},
                        'sender_username': (getattr(msg.sender, 'username', None) if getattr(msg, 'sender', None) else None),
                        'message_url': f"https://t.me/{getattr(entity, 'username', '').strip()}/{msg.id}" if getattr(entity, 'username', None) else None,
                        'sentiment_score': self.eth_analyzer.analyze_sentiment(text),
                        'confidence': 0.8,
                        'keywords_detected': ['ETH', 'Ethereum'],
                        'context_multipliers': [],
                        'engagement_weight': 0,
                        'final_weight': 0,
                        'message_timestamp': (msg.date.replace(tzinfo=timezone.utc).isoformat() if msg.date else datetime.now(timezone.utc).isoformat()),
                        'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                    })
                results[channel] = messages
            except FloodWaitError as fw:
                self.logger.warning(f"FloodWaitError for {channel}: waiting {fw.seconds}s")
                await asyncio.sleep(fw.seconds)
                results[channel] = results.get(channel, [])
            except RPCError as rpc:
                self.logger.warning(f"RPCError for {channel}: {rpc}")
                results[channel] = results.get(channel, [])
            except Exception as exc:
                self.logger.warning(f"Error fetching {channel}: {exc}")
                results[channel] = results.get(channel, [])
            # Rate limit between channels
            await asyncio.sleep(max(0.0, per_channel_delay_seconds))
        return results
    
    async def search_dialogs(
        self,
        include_groups: bool = True,
        include_private: bool = False,
        query: str = "ETH",
        limit_per_chat: int = 20,
        days_back: int = 1,
        per_chat_delay_seconds: float = 1.5,
    ) -> Dict[str, List[Dict[str, Any]]]:
        """
        Search user's dialogs (groups and/or private chats) for ETH mentions.
        Returns a dict: {dialog_name_or_username: [message_dict, ...]}
        """
        results: Dict[str, List[Dict[str, Any]]] = {}
        if self.client is None or not TELETHON_AVAILABLE:
            raise RuntimeError("Telethon client not initialized. Install telethon and set TELEGRAM_API_ID/TELEGRAM_API_HASH.")

        assert self.client is not None
        cutoff_dt = datetime.now(timezone.utc) - timedelta(days=days_back)

        # Import types locally to avoid optional import issues
        try:
            from telethon.tl.types import Channel, Chat, User
        except Exception:
            Channel = Chat = User = object  # type: ignore

        async for dialog in self.client.iter_dialogs():
            entity = dialog.entity
            is_group = isinstance(entity, (Channel, Chat)) and getattr(entity, 'megagroup', False)
            is_private = isinstance(entity, User)

            if (include_groups and is_group) or (include_private and is_private):
                name = getattr(dialog, 'name', None) or getattr(entity, 'username', None) or str(getattr(entity, 'id', 'unknown'))
                messages: List[Dict[str, Any]] = []
                try:
                    async for msg in self.client.iter_messages(entity, limit=limit_per_chat, search=query):
                        if not isinstance(msg, Message):
                            continue
                        if msg.date and msg.date.replace(tzinfo=timezone.utc) < cutoff_dt:
                            break
                        text = msg.message or ""
                        if not text or not self._mentions_eth(text):
                            continue

                        messages.append({
                            'platform': 'telegram',
                            'message_id': msg.id,
                            'channel_id': getattr(entity, 'id', 0) or 0,
                            'channel_username': getattr(entity, 'username', name) or name,
                            'channel_title': name,
                            'channel_subscribers': 0,
                            'message_text': text,
                            'message_views': getattr(msg, 'views', 0) or 0,
                            'forwards': getattr(msg, 'forwards', 0) or 0,
                            'replies': (getattr(msg, 'replies', None).replies if getattr(msg, 'replies', None) else 0),
                            'reactions': {},
                            'sender_username': (getattr(msg.sender, 'username', None) if getattr(msg, 'sender', None) else None),
                            'message_url': None,
                            'sentiment_score': self.eth_analyzer.analyze_sentiment(text),
                            'confidence': 0.8,
                            'keywords_detected': ['ETH', 'Ethereum'],
                            'context_multipliers': [],
                            'engagement_weight': 0,
                            'final_weight': 0,
                            'message_timestamp': (msg.date.replace(tzinfo=timezone.utc).isoformat() if msg.date else datetime.now(timezone.utc).isoformat()),
                            'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
                        })
                except FloodWaitError as fw:  # type: ignore
                    self.logger.warning(f"FloodWaitError for dialog {name}: waiting {getattr(fw, 'seconds', 1)}s")
                    await asyncio.sleep(getattr(fw, 'seconds', 1))
                except RPCError as rpc:  # type: ignore
                    self.logger.warning(f"RPCError for dialog {name}: {rpc}")
                except Exception as exc:
                    self.logger.warning(f"Error fetching dialog {name}: {exc}")

                if messages:
                    results[name] = messages
                await asyncio.sleep(max(0.0, per_chat_delay_seconds))

        return results

    def _mentions_eth(self, text: str) -> bool:
        lower = (text or '').lower()
        return ('eth' in lower) or ('ethereum' in lower)

    def _build_sample_messages(self, channel: str, count: int) -> List[Dict[str, Any]]:
        return [
            {
                'platform': 'telegram',
                'message_id': i,
                'channel_id': 0,
                'channel_username': channel,
                'channel_title': None,
                'channel_subscribers': 0,
                'message_text': f"Sample ETH message from {channel} #{i} - ETH whale accumulation continues!",
                'message_views': 200 + i * 20,
                'forwards': 10 + i,
                'replies': 0,
                'reactions': {},
                'sender_username': f"user_{i}",
                'message_url': None,
                'sentiment_score': 0.7,
                'confidence': 0.8,
                'keywords_detected': ['ETH', 'Ethereum'],
                'context_multipliers': [],
                'engagement_weight': 0,
                'final_weight': 0,
                'message_timestamp': datetime.now(timezone.utc).isoformat(),
                'analysis_timestamp': datetime.now(timezone.utc).isoformat(),
            }
            for i in range(1, count + 1)
        ]



