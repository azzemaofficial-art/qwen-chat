"""
High-Performance Time-Series Database
Optimized for financial market data with compression and fast queries
"""

import time
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from collections import defaultdict
import bisect
import struct


@dataclass
class Tick:
    """Single market tick"""
    timestamp: datetime
    symbol: str
    price: float
    volume: float
    bid: Optional[float] = None
    ask: Optional[float] = None
    trade_type: str = "regular"  # regular, odd_lot, block
    
    def to_tuple(self) -> Tuple:
        return (
            self.timestamp.timestamp(),
            self.symbol,
            self.price,
            self.volume,
            self.bid or 0.0,
            self.ask or 0.0,
            self.trade_type
        )
    
    @classmethod
    def from_tuple(cls, data: Tuple) -> 'Tick':
        return cls(
            timestamp=datetime.fromtimestamp(data[0]),
            symbol=data[1],
            price=data[2],
            volume=data[3],
            bid=data[4] if data[4] > 0 else None,
            ask=data[5] if data[5] > 0 else None,
            trade_type=data[6]
        )


@dataclass
class OHLCV:
    """OHLCV candlestick data"""
    timestamp: datetime
    symbol: str
    open: float
    high: float
    low: float
    close: float
    volume: float
    trades: int = 0
    
    def to_dict(self) -> Dict:
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "open": self.open,
            "high": self.high,
            "low": self.low,
            "close": self.close,
            "volume": self.volume,
            "trades": self.trades
        }


class TimeSeriesCompressor:
    """Delta-of-delta compression for time-series data"""
    
    @staticmethod
    def compress_timestamps(timestamps: List[float]) -> bytes:
        """Compress timestamps using delta-of-delta encoding"""
        if len(timestamps) < 2:
            return struct.pack('>Q', len(timestamps)) + b''
        
        result = []
        # First timestamp
        result.append(int(timestamps[0]))
        
        # First delta
        if len(timestamps) > 1:
            first_delta = int(timestamps[1] - timestamps[0])
            result.append(first_delta)
            
            # Delta of deltas
            for i in range(2, len(timestamps)):
                current_delta = int(timestamps[i] - timestamps[i-1])
                delta_of_delta = current_delta - first_delta
                result.append(delta_of_delta)
                first_delta = current_delta
        
        # Pack as variable-length integers
        compressed = b''
        for val in result:
            compressed += TimeSeriesCompressor._encode_varint(val)
        
        return struct.pack('>Q', len(timestamps)) + compressed
    
    @staticmethod
    def decompress_timestamps(data: bytes) -> List[float]:
        """Decompress timestamps"""
        count = struct.unpack('>Q', data[:8])[0]
        if count == 0:
            return []
        
        values = []
        offset = 8
        while len(values) < count:
            val, new_offset = TimeSeriesCompressor._decode_varint(data, offset)
            values.append(val)
            offset = new_offset
        
        if len(values) < 2:
            return [float(values[0])] if values else []
        
        # Reconstruct timestamps
        timestamps = [float(values[0])]
        if len(values) > 1:
            timestamps.append(timestamps[0] + values[1])
            
            prev_delta = values[1]
            for i in range(2, len(values)):
                current_delta = prev_delta + values[i]
                timestamps.append(timestamps[-1] + current_delta)
                prev_delta = current_delta
        
        return timestamps
    
    @staticmethod
    def _encode_varint(value: int) -> bytes:
        """Encode integer as variable-length"""
        result = []
        while value > 127:
            result.append((value & 0x7F) | 0x80)
            value >>= 7
        result.append(value & 0x7F)
        return bytes(result)
    
    @staticmethod
    def _decode_varint(data: bytes, offset: int) -> Tuple[int, int]:
        """Decode variable-length integer"""
        result = 0
        shift = 0
        while True:
            byte = data[offset]
            result |= (byte & 0x7F) << shift
            offset += 1
            if not (byte & 0x80):
                break
            shift += 7
        return result, offset
    
    @staticmethod
    def compress_prices(prices: List[float], base_price: float) -> bytes:
        """Compress prices using delta encoding"""
        if not prices:
            return b''
        
        deltas = []
        prev = base_price
        for price in prices:
            delta = int((price - prev) * 10000)  # 4 decimal precision
            deltas.append(delta)
            prev = price
        
        compressed = b''
        for delta in deltas:
            # Handle negative numbers with zigzag encoding
            zigzag = (delta << 1) ^ (delta >> 31)
            compressed += TimeSeriesCompressor._encode_varint(zigzag)
        
        return compressed
    
    @staticmethod
    def decompress_prices(data: bytes, base_price: float) -> List[float]:
        """Decompress prices"""
        if not data:
            return []
        
        prices = [base_price]
        offset = 0
        while offset < len(data):
            zigzag, new_offset = TimeSeriesCompressor._decode_varint(data, offset)
            # Decode zigzag
            delta = (zigzag >> 1) ^ -(zigzag & 1)
            price = prices[-1] + delta / 10000.0
            prices.append(price)
            offset = new_offset
        
        return prices[1:]  # Skip base price


class MarketDataStore:
    """High-performance time-series database for market data"""
    
    def __init__(self, compression: bool = True):
        self.compression = compression
        self.ticks: Dict[str, List[Tick]] = defaultdict(list)
        self.ohlcv: Dict[str, Dict[str, List[OHLCV]]] = defaultdict(lambda: defaultdict(list))
        self.indexes: Dict[str, Dict[str, List[float]]] = defaultdict(lambda: defaultdict(list))
        self.metadata: Dict[str, Dict] = {}
        self.compressed_data: Dict[str, bytes] = {}
    
    def add_tick(self, tick: Tick):
        """Add a single tick"""
        self.ticks[tick.symbol].append(tick)
        
        # Update index
        ts = tick.timestamp.timestamp()
        bisect.insort(self.indexes[tick.symbol]["timestamps"], ts)
        
        # Update metadata
        if tick.symbol not in self.metadata:
            self.metadata[tick.symbol] = {
                "first_tick": tick.timestamp,
                "last_tick": tick.timestamp,
                "tick_count": 0,
                "min_price": tick.price,
                "max_price": tick.price
            }
        
        meta = self.metadata[tick.symbol]
        meta["last_tick"] = tick.timestamp
        meta["tick_count"] += 1
        meta["min_price"] = min(meta["min_price"], tick.price)
        meta["max_price"] = max(meta["max_price"], tick.price)
    
    def add_ticks(self, ticks: List[Tick]):
        """Batch add ticks"""
        for tick in ticks:
            self.add_tick(tick)
    
    def add_ohlcv(self, candle: OHLCV, timeframe: str = "1m"):
        """Add OHLCV candle"""
        self.ohlcv[candle.symbol][timeframe].append(candle)
        
        # Update index
        ts = candle.timestamp.timestamp()
        bisect.insort(self.indexes[candle.symbol][f"ohlcv_{timeframe}"], ts)
    
    def get_ticks(self, symbol: str, start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None, 
                  limit: Optional[int] = None) -> List[Tick]:
        """Query ticks with time range"""
        if symbol not in self.ticks:
            return []
        
        ticks = self.ticks[symbol]
        
        # Filter by time range
        if start_time:
            ticks = [t for t in ticks if t.timestamp >= start_time]
        if end_time:
            ticks = [t for t in ticks if t.timestamp <= end_time]
        
        # Sort by timestamp
        ticks = sorted(ticks, key=lambda t: t.timestamp)
        
        # Apply limit
        if limit:
            ticks = ticks[-limit:]
        
        return ticks
    
    def get_ohlcv(self, symbol: str, timeframe: str = "1m",
                  start_time: Optional[datetime] = None,
                  end_time: Optional[datetime] = None,
                  limit: Optional[int] = None) -> List[OHLCV]:
        """Query OHLCV candles"""
        if symbol not in self.ohlcv or timeframe not in self.ohlcv[symbol]:
            return []
        
        candles = self.ohlcv[symbol][timeframe]
        
        # Filter by time range
        if start_time:
            candles = [c for c in candles if c.timestamp >= start_time]
        if end_time:
            candles = [c for c in candles if c.timestamp <= end_time]
        
        # Sort by timestamp
        candles = sorted(candles, key=lambda c: c.timestamp)
        
        # Apply limit
        if limit:
            candles = candles[-limit:]
        
        return candles
    
    def get_vwap(self, symbol: str, start_time: datetime, 
                 end_time: datetime) -> Optional[float]:
        """Calculate VWAP for time range"""
        ticks = self.get_ticks(symbol, start_time, end_time)
        
        if not ticks:
            return None
        
        total_value = sum(t.price * t.volume for t in ticks)
        total_volume = sum(t.volume for t in ticks)
        
        if total_volume == 0:
            return None
        
        return total_value / total_volume
    
    def get_ohlc_statistics(self, symbol: str, 
                           start_time: Optional[datetime] = None,
                           end_time: Optional[datetime] = None) -> Optional[Dict]:
        """Get OHLC statistics for time range"""
        ticks = self.get_ticks(symbol, start_time, end_time)
        
        if not ticks:
            return None
        
        prices = [t.price for t in ticks]
        
        return {
            "open": prices[0],
            "high": max(prices),
            "low": min(prices),
            "close": prices[-1],
            "volume": sum(t.volume for t in ticks),
            "vwap": sum(t.price * t.volume for t in ticks) / sum(t.volume for t in ticks),
            "trades": len(ticks),
            "avg_trade_size": sum(t.volume for t in ticks) / len(ticks)
        }
    
    def compress_symbol_data(self, symbol: str) -> bool:
        """Compress all data for a symbol"""
        if symbol not in self.ticks:
            return False
        
        ticks = self.ticks[symbol]
        if not ticks:
            return False
        
        # Extract components
        timestamps = [t.timestamp.timestamp() for t in ticks]
        prices = [t.price for t in ticks]
        volumes = [t.volume for t in ticks]
        
        # Compress each component
        ts_compressed = TimeSeriesCompressor.compress_timestamps(timestamps)
        price_compressed = TimeSeriesCompressor.compress_prices(prices, prices[0])
        
        # Simple volume compression (delta encoding)
        vol_deltas = []
        prev_vol = volumes[0]
        for vol in volumes[1:]:
            vol_deltas.append(int(vol - prev_vol))
            prev_vol = vol
        
        vol_compressed = b''
        for delta in vol_deltas:
            zigzag = (delta << 1) ^ (delta >> 31)
            vol_compressed += TimeSeriesCompressor._encode_varint(zigzag)
        
        # Store compressed data
        self.compressed_data[symbol] = json.dumps({
            "count": len(ticks),
            "base_price": prices[0],
            "timestamps": ts_compressed.hex(),
            "prices": price_compressed.hex(),
            "volumes": vol_compressed.hex()
        }).encode()
        
        return True
    
    def decompress_symbol_data(self, symbol: str) -> Optional[List[Tick]]:
        """Decompress data for a symbol"""
        if symbol not in self.compressed_data:
            return None
        
        data = json.loads(self.compressed_data[symbol].decode())
        
        # Decompress components
        timestamps = TimeSeriesCompressor.decompress_timestamps(
            bytes.fromhex(data["timestamps"])
        )
        prices = TimeSeriesCompressor.decompress_prices(
            bytes.fromhex(data["prices"]), data["base_price"]
        )
        
        # Decompress volumes
        vol_hex = data["volumes"]
        vol_data = bytes.fromhex(vol_hex)
        volumes = [0.0]  # Need first volume separately
        offset = 0
        prev_vol = 0.0
        while offset < len(vol_data):
            zigzag, new_offset = TimeSeriesCompressor._decode_varint(vol_data, offset)
            delta = (zigzag >> 1) ^ -(zigzag & 1)
            vol = prev_vol + delta
            volumes.append(vol)
            prev_vol = vol
            offset = new_offset
        
        # Reconstruct ticks
        ticks = []
        for i in range(min(len(timestamps), len(prices))):
            tick = Tick(
                timestamp=datetime.fromtimestamp(timestamps[i]),
                symbol=symbol,
                price=prices[i] if i < len(prices) else 0,
                volume=volumes[i] if i < len(volumes) else 0
            )
            ticks.append(tick)
        
        return ticks
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics"""
        total_ticks = sum(len(t) for t in self.ticks.values())
        total_symbols = len(self.ticks)
        total_candles = sum(
            sum(len(c) for c in timeframes.values())
            for timeframes in self.ohlcv.values()
        )
        
        compressed_size = sum(len(d) for d in self.compressed_data.values())
        
        return {
            "total_symbols": total_symbols,
            "total_ticks": total_ticks,
            "total_candles": total_candles,
            "compressed_datasets": len(self.compressed_data),
            "compressed_size_bytes": compressed_size,
            "compression_ratio": compressed_size / (total_ticks * 50) if total_ticks > 0 else 0
        }
    
    def export_to_parquet_like(self, symbol: str) -> Dict:
        """Export data in columnar format (Parquet-like)"""
        if symbol not in self.ticks:
            return {}
        
        ticks = self.ticks[symbol]
        
        return {
            "schema": {
                "timestamp": "int64",
                "price": "float64",
                "volume": "float64",
                "bid": "float64",
                "ask": "float64"
            },
            "columns": {
                "timestamp": [int(t.timestamp.timestamp() * 1000) for t in ticks],
                "price": [t.price for t in ticks],
                "volume": [t.volume for t in ticks],
                "bid": [t.bid or 0.0 for t in ticks],
                "ask": [t.ask or 0.0 for t in ticks]
            },
            "row_count": len(ticks),
            "metadata": self.metadata.get(symbol, {})
        }


def demo():
    """Demonstrate time-series database capabilities"""
    print("=" * 70)
    print("💾 HIGH-PERFORMANCE TIME-SERIES DATABASE DEMO")
    print("=" * 70)
    
    db = MarketDataStore(compression=True)
    
    # Generate synthetic tick data
    print("\n📊 Generating Synthetic Tick Data...")
    symbols = ["AAPL", "GOOGL", "MSFT", "TSLA"]
    
    base_time = datetime.now() - timedelta(hours=1)
    
    for symbol in symbols:
        base_price = random.uniform(150, 500)
        
        for i in range(1000):
            tick = Tick(
                timestamp=base_time + timedelta(seconds=i),
                symbol=symbol,
                price=base_price * (1 + random.gauss(0, 0.001)),
                volume=random.uniform(10, 1000),
                bid=base_price * (1 - random.uniform(0.0001, 0.0005)),
                ask=base_price * (1 + random.uniform(0.0001, 0.0005))
            )
            db.add_tick(tick)
        
        # Add some OHLCV data
        for timeframe in ["1m", "5m", "1h"]:
            for j in range(60):
                candles_start = base_time + timedelta(minutes=j*5)
                ticks_subset = db.get_ticks(symbol, candles_start, 
                                           candles_start + timedelta(minutes=5))
                
                if ticks_subset:
                    prices = [t.price for t in ticks_subset]
                    candle = OHLCV(
                        timestamp=candles_start,
                        symbol=symbol,
                        open=prices[0],
                        high=max(prices),
                        low=min(prices),
                        close=prices[-1],
                        volume=sum(t.volume for t in ticks_subset),
                        trades=len(ticks_subset)
                    )
                    db.add_ohlcv(candle, timeframe)
    
    print(f"   ✅ Added ticks for {len(symbols)} symbols")
    
    # Query ticks
    print("\n🔍 Querying Ticks...")
    for symbol in symbols[:2]:
        ticks = db.get_ticks(symbol, limit=5)
        print(f"\n   {symbol} - Last 5 ticks:")
        for tick in ticks:
            print(f"      {tick.timestamp.strftime('%H:%M:%S')} - ${tick.price:.2f} ({tick.volume:.0f} vol)")
    
    # Query OHLCV
    print("\n\n🕯️ Querying OHLCV Candles...")
    for symbol in symbols[:2]:
        candles = db.get_ohlcv(symbol, timeframe="5m", limit=3)
        print(f"\n   {symbol} - Last 3 candles (5m):")
        for candle in candles:
            print(f"      {candle.timestamp.strftime('%H:%M')} - O:{candle.open:.2f} H:{candle.high:.2f} L:{candle.low:.2f} C:{candle.close:.2f}")
    
    # Calculate VWAP
    print("\n\n📈 Calculating VWAP...")
    for symbol in symbols[:2]:
        vwap = db.get_vwap(symbol, base_time, datetime.now())
        if vwap:
            print(f"   {symbol} VWAP: ${vwap:.2f}")
    
    # Get OHLC statistics
    print("\n\n📊 OHLC Statistics...")
    for symbol in symbols[:2]:
        stats = db.get_ohlc_statistics(symbol, base_time, datetime.now())
        if stats:
            print(f"\n   {symbol}:")
            print(f"      Open: ${stats['open']:.2f}")
            print(f"      High: ${stats['high']:.2f}")
            print(f"      Low: ${stats['low']:.2f}")
            print(f"      Close: ${stats['close']:.2f}")
            print(f"      Volume: {stats['volume']:.0f}")
            print(f"      VWAP: ${stats['vwap']:.2f}")
            print(f"      Trades: {stats['trades']}")
    
    # Compression demo
    print("\n\n🗜️ Testing Compression...")
    for symbol in symbols:
        db.compress_symbol_data(symbol)
    
    stats = db.get_storage_stats()
    print(f"   Total Ticks: {stats['total_ticks']:,}")
    print(f"   Compressed Size: {stats['compressed_size_bytes']:,} bytes")
    print(f"   Compression Ratio: {stats['compression_ratio']:.2%}")
    
    # Export to columnar format
    print("\n\n📦 Exporting Columnar Format...")
    for symbol in symbols[:1]:
        export = db.export_to_parquet_like(symbol)
        print(f"   {symbol}:")
        print(f"      Row Count: {export['row_count']:,}")
        print(f"      Columns: {list(export['columns'].keys())}")
        print(f"      Schema: {export['schema']}")
    
    print("\n" + "=" * 70)
    print("✅ TIME-SERIES DATABASE DEMO COMPLETED")
    print("=" * 70)


# Import random for demo
import random

if __name__ == "__main__":
    demo()
