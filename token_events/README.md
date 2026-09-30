# Token cổ phiếu đa issuer qua event ban đêm

Đo cùng một cổ phiếu được token hoá bởi nhiều issuer (Ondo, xStocks, bStocks, Robinhood, Dinari, token riêng của sàn)
phản ứng thế nào với event xảy ra khi sàn Mỹ đóng cửa: issuer nào phản ánh tin nhanh hơn, ai lệch giá mở cửa nhiều hơn,
giá giữa các issuer phân tán tới mức nào. Nến 5 phút, 5–6 event, chia large / mid / small cap.

## Cài đặt

```bash
cd token_events
python3.11 -m venv .venv-events && . .venv-events/bin/activate
pip install -r requirements.txt
```

Không cần API key. Endpoint nào lỗi hoặc bị geo-block thì bị log và bỏ qua; cuối mỗi lệnh in bảng nguồn lấy được / không
lấy được (lưu cả ở `data/source_status.csv`, log đầy đủ ở `data/run.log`).

## Quy trình

| Lệnh | Việc |
|---|---|
| `python run.py discover` | Bước 1: quét listing các sàn + Hyperliquid + Binance perp, GeckoTerminal, Pyth; daily 60 ngày + lịch KQKD + market cap từ yfinance; lọc đêm có \|gap\| ≥ 3%; probe dữ liệu của 20 ứng viên tốt nhất; ghi `events_candidates.csv`, `sources.yaml`, `events.yaml` rồi **dừng** để duyệt |
| `python run.py fetch` | Bước 2: tải nến 5m cho mọi nguồn trong `sources.yaml`, cửa sổ `t_evt − 12h → 09:30 ET + 2h` (cộng phiên chính ngày trước để hiệu chỉnh k), cache ở `data/raw/{ticker}_{issuer}_{venue}_{date}.parquet` |
| `python run.py analyze` | Bước 3–4: lưới 5m UTC chung, quy đổi USDT/USDC, hệ số k, mọi chỉ số, dispersion, arb window, lead-lag |
| `python run.py report` | Bước 5: `report.html` (Plotly, 1 file) + `summary.xlsx` |
| `python run.py all --only ORCL` | fetch + analyze + report cho 1 event (chạy thử trước) |
| `python run.py demo` | Event **giả lập** `DEMO` chạy end-to-end trong `./demo`, không cần mạng |

Tuỳ chọn: `--only <event_id|ticker> ...`, `--refresh` (bỏ cache), `--today YYYY-MM-DD`, `--workdir`, `-v`.
Tham số (ngưỡng gap, ngưỡng arb, ngưỡng cảnh báo k, …) nằm trong `config.yaml`.

## Duyệt sau `discover`

- `sources.yaml`: mỗi nguồn có `issuer`, `venue`, `kind` (cex_spot / dex / perp / perp_index / perp_mark / ref / stock),
  `adapter`, `symbol`, `quote` và `identified_by` giải thích cách nhận diện (listing base + hậu tố, tên token, asset class
  Kraken, địa chỉ pool + reserve GeckoTerminal …). Đặt `enabled: false` cho nguồn nhận diện sai; thêm nguồn thiếu bằng tay.
  Perp Binance chỉ bật khi `underlyingType/SubType` của hợp đồng ghi rõ là cổ phiếu.
- `events.yaml`: 5–6 event đề xuất (cân bằng 3 nhóm vốn hoá, ưu tiên ≥ 2 issuer có dữ liệu, AMC, gap lớn). Sửa / thêm
  từ `events_candidates.csv`. `t_event_utc` là mốc chuẩn; BMO và đêm không có KQKD được gắn nhãn riêng.

## Định nghĩa chính

- Giá tại thời điểm t = giá khớp cuối của nến đã kết thúc trước hoặc đúng t. Nến volume 0 không tính là giá giao dịch.
- `k` = median(P_token / P_stock) trong phiên chính ngày giao dịch trước event, chỉ nến có volume > 0; `P_adj = P / k`.
  Cảnh báo khi |k − 1| > 2%.
- `captured(t) = (P_adj(t) − C0) / (O1 − C0)`; `t50/t90` phải giữ ≥ 30 phút.
- `dispersion = (max − min) / median` trên các nguồn token có volume trong nến; `arb_windows` = đoạn liên tục dispersion >
  ngưỡng (0,5%).
- Lead-lag: tương quan chéo lợi suất log 5m, lag −6…+6 nến; lag dương = A dẫn B.

## Giới hạn nguồn đã biết

- Kraken chỉ trả 720 nến gần nhất (5m ≈ 2,5 ngày) → event cũ hơn tự hạ xuống 15m / 1h / 4h và ghi rõ trong cột `interval`.
- Hyperliquid chỉ ~5000 nến gần nhất (5m ≈ 17 ngày) → tự hạ xuống 15m / 1h.
- yfinance 5m chỉ ~60 ngày gần nhất; nếu thiếu, k được hiệu chỉnh theo Pyth.
- GeckoTerminal ~30 request/phút (đã throttle), kết quả tìm pool cache ở `data/meta/gt_search.json`.
- Nến thô hơn 5m được đặt ở ô 5m cuối cùng của nó (giá chỉ biết khi nến đóng).

## Test

```bash
python -m pytest -q tests
```
