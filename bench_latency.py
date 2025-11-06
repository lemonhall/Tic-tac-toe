"""基准测速脚本：比较 localhost 与 127.0.0.1 的端点延迟
运行示例：
    python bench_latency.py
输出：均值/中位数/P95/最大值，用于判断是否存在 DNS/IPv6 回退导致的额外等待。
"""
import statistics
import time
import requests
from collections import defaultdict

BASES = ["http://localhost:5000", "http://127.0.0.1:5000"]
ROUNDS = 8  # 缩短默认测试轮次，快速定位；确认后可加大
TIMEOUT = 5

ENDPOINTS = ["/api/health", "/api/game/create"]


def measure(base: str, path: str):
    url = base + path
    t0 = time.perf_counter()
    try:
        if path == "/api/game/create":
            resp = requests.post(url, json={"player_x_type": "agent", "player_o_type": "ai"}, timeout=TIMEOUT)
        else:
            resp = requests.get(url, timeout=TIMEOUT)
        t1 = time.perf_counter()
        return (t1 - t0) * 1000, resp.status_code
    except Exception:
        t1 = time.perf_counter()
        return (t1 - t0) * 1000, -1


def summary(samples):
    if not samples:
        return {}
    return {
        "count": len(samples),
        "mean": statistics.mean(samples),
        "median": statistics.median(samples),
        "p95": statistics.quantiles(samples, n=100)[94],
        "max": max(samples),
        "min": min(samples),
    }


def fmt(s):
    return (
        f"count={s['count']} mean={s['mean']:.1f}ms median={s['median']:.1f}ms "
        f"p95={s['p95']:.1f}ms max={s['max']:.1f}ms min={s['min']:.1f}ms"
    )


def main():
    print("=== 基准测速开始 (ROUNDS=%d) ===" % ROUNDS)
    for base in BASES:
        print(f"\nBase: {base}")
        results = defaultdict(list)
        codes = defaultdict(list)
        for ep in ENDPOINTS:
            for i in range(ROUNDS):
                ms, code = measure(base, ep)
                results[ep].append(ms)
                codes[ep].append(code)
                print(f"{ep} round={i+1} code={code} {ms:.1f}ms")
                time.sleep(0.03)
        for ep in ENDPOINTS:
            s = summary(results[ep])
            print(f"{ep}: {fmt(s)} status_codes={codes[ep]}")
    print("\n若 localhost 明显慢于 127.0.0.1（例如前者 ~2000ms，后者 <10ms），说明可能是 IPv6 回退或代理解析导致延迟。")
    print("可在 hosts 中固定 127.0.0.1 或改用 127.0.0.1 作为 base_url。")
    print("=== 结束 ===")

if __name__ == "__main__":
    main()
