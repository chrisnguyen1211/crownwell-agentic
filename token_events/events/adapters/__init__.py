from .binance import BinancePerp, BinancePerpIndex, BinancePerpMark, BinanceSpot
from .bitget import Bitget
from .bybit import Bybit
from .gate import Gate
from .geckoterminal import GeckoTerminal
from .hyperliquid import Hyperliquid
from .kraken import Kraken
from .kucoin import Kucoin
from .mexc import Mexc
from .okx import Okx
from .pyth import Pyth
from .yahoo import Yahoo

ADAPTERS = {a.name: a for a in (
    Gate(), Bitget(), Mexc(), Okx(), Kraken(), Bybit(), Kucoin(), BinanceSpot(),
    BinancePerp(), BinancePerpIndex(), BinancePerpMark(), Hyperliquid(), GeckoTerminal(), Pyth(), Yahoo(),
)}

# CEX spot venues scanned for stock tokens during discovery
CEX_SPOT = ["gate", "bitget", "mexc", "okx", "kraken", "bybit", "kucoin", "binance"]
