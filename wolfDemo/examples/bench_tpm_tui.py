#!/usr/bin/env python3
import re, sys, time, argparse
from collections import OrderedDict

# -------- args / runtime/IO ----------
ap = argparse.ArgumentParser(description="wolfTPM benchmark live TUI (single table, static, newest-row highlight)")
ap.add_argument("port", nargs="?", help="Serial port like /dev/ttyACM0")
ap.add_argument("baud", nargs="?", type=int, default=115200, help="Baud rate (default 115200)")
ap.add_argument("--demo", action="store_true", help="Run a local demo data source to preview layout")
args = ap.parse_args()

PORT = args.port if args.port and args.port.startswith("/dev/") else None
BAUD = args.baud
USE_SERIAL = bool(PORT)

# ---- layout knobs ----
COL_ALGO   = 16          # width of "Algo"
COL_MODE   = 20          # width of "Mode/Op"
COL_RESULT = 16          # width of "Result"
CELL_PAD   = 1           # left/right padding inside each cell

HDR_PERIOD = 0.5         # header heartbeat period (dots)

from rich.console import Console, Group
from rich.live import Live
from rich.table import Table
from rich.layout import Layout
from rich.align import Align
from rich.text import Text
from rich import box

console = Console()

def line_iter():
    if args.demo:
        # generate fake rows periodically to fill and overflow
        seq = [
            "RNG                 32 KB took 1.016 seconds,   31.496 KB/s",
            "AES-128-CBC-enc     64 KB took 1.008 seconds,   63.492 KB/s",
            "AES-128-CBC-dec     64 KB took 1.016 seconds,   62.992 KB/s",
            "AES-256-CBC-enc     55 KB took 1.004 seconds,   54.781 KB/s",
            "AES-256-CBC-dec     55 KB took 1.012 seconds,   54.348 KB/s",
            "SHA256             159 KB took 1.000 seconds,  159.000 KB/s",
            "RSA     2048 key gen        4 ops took 33.870 sec, avg 8467.500 ms, 0.118 ops/sec",
            "RSA     2048 Public       186 ops took 1.004 sec, avg 5.398 ms, 185.259 ops/sec",
            "RSA     2048 Priv OAEP     11 ops took 1.020 sec, avg 92.727 ms, 10.784 ops/sec",
            "ECC      256 key gen       12 ops took 1.043 sec, avg 86.917 ms, 11.505 ops/sec",
            "ECDSA    256 sign          41 ops took 1.015 sec, avg 24.756 ms, 40.394 ops/sec",
            "ECDHE    256 agree         16 ops took 1.059 sec, avg 66.187 ms, 15.109 ops/sec",
        ]
        i = 0
        # Emit a fake header/reset once at start
        yield "wolfSSL STM32U585 @ 160 MHz, TPM benchmark"
        time.sleep(0.3)
        while True:
            time.sleep(0.35)
            yield seq[i % len(seq)]
            i += 1
    elif USE_SERIAL:
        import serial  # type: ignore
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
        buf = b""
        while True:
            chunk = ser.read(4096)
            if not chunk:
                time.sleep(0.02)
                yield ""
                continue
            buf += chunk
            while b"\n" in buf:
                ln, buf = buf.split(b"\n", 1)
                yield ln.decode("utf-8", "ignore").strip()
    else:
        for ln in sys.stdin:
            yield ln.strip()
        while True:
            time.sleep(0.1)
            yield ""

# -------- parsing (TPM) ----------
# Example stream lines:
# RNG                 32 KB took 1.016 seconds,   31.496 KB/s
# AES-128-CBC-enc     64 KB took 1.008 seconds,   63.492 KB/s
# SHA256             159 KB took 1.000 seconds,  159.000 KB/s
re_stream = re.compile(
    r"^(?P<name>.+?)\s+(?P<amnt>\d+)\s+KB\s+took\s+(?P<sec>[\d.]+)\s+seconds?,\s+(?P<rate>[\d.]+)\s+KB/s$",
    re.IGNORECASE,
)

# RSA variants:
# RSA     2048 key gen        4 ops took 33.870 sec, avg 8467.500 ms, 0.118 ops/sec
# RSA     2048 Public       186 ops took 1.004 sec, avg 5.398 ms, 185.259 ops/sec
# RSA     2048 Priv OAEP     11 ops took 1.020 sec, avg 92.727 ms, 10.784 ops/sec
re_rsa_keygen = re.compile(
    r"^RSA\s+(?P<bits>\d+)\s+key\s+gen\s+(?P<ops>\d+)\s+ops\s+took\s+(?P<sec>[\d.]+)\s+sec,.*?,\s+(?P<rate>[\d.]+)\s+ops/sec$",
    re.IGNORECASE,
)
re_rsa_pubpriv = re.compile(
    r"^RSA\s+(?P<bits>\d+)\s+(?P<op>Public|Private)\s+(?P<ops>\d+)\s+ops\s+took\s+(?P<sec>[\d.]+)\s+sec,.*?,\s+(?P<rate>[\d.]+)\s+ops/sec$",
    re.IGNORECASE,
)
re_rsa_oaep = re.compile(
    r"^RSA\s+(?P<bits>\d+)\s+(?P<op>(?:Pub|Priv)\s+OAEP)\s+(?P<ops>\d+)\s+ops\s+took\s+(?P<sec>[\d.]+)\s+sec,.*?,\s+(?P<rate>[\d.]+)\s+ops/sec$",
    re.IGNORECASE,
)

# ECC-family:
# ECC      256 key gen       12 ops took 1.043 sec, avg 86.917 ms, 11.505 ops/sec
# ECDSA    256 sign          41 ops took 1.015 sec, avg 24.756 ms, 40.394 ops/sec
# ECDHE    256 agree         16 ops took 1.059 sec, avg 66.187 ms, 15.109 ops/sec
re_ecc = re.compile(
    r"^(?P<kind>ECC|ECDSA|ECDHE)\s+(?P<bits>\d+)\s+(?P<op>key\s+gen|sign|verify|agree)\s+(?P<ops>\d+)\s+ops\s+took\s+(?P<sec>[\d.]+)\s+sec,.*?,\s+(?P<rate>[\d.]+)\s+ops/sec$",
    re.IGNORECASE,
)

# A new run header we can use to clear state (start of run), and a completion line.
re_reset = re.compile(r"(TPM benchmark|Benchmark Demo run|TPM2 Benchmark)", re.IGNORECASE)
re_done  = re.compile(r"Benchmark complete!", re.IGNORECASE)

def split_name(name: str):
    """Return (algo, mode/op) from a 'name' token like 'AES-128-CBC-enc' or 'SHA256'."""
    n = name.strip()
    if n.upper().startswith("AES-"):
        parts = n.split("-")
        if len(parts) >= 3:
            # AES-128-CBC-enc -> algo: AES-128, mode: CBC-enc
            algo = f"{parts[0]}-{parts[1]}"
            mode = "-".join(parts[2:]) if len(parts) > 2 else "—"
            return algo, mode
    # SHA*, RNG, etc.
    return n, "—"

def norm_stream(m):
    algo, mode = split_name(m.group("name"))
    # Rate in KB/s (as printed by wolfTPM sample)
    return {"algo": algo, "mode": mode, "result": f"{float(m.group('rate')):.3f} KB/s"}

def norm_rsa_keygen(m):
    return {"algo": f"RSA-{m.group('bits')}", "mode": "key gen", "result": f"{float(m.group('rate')):.3f} ops/s"}

def norm_rsa_pubpriv(m):
    op = m.group("op").strip().lower()
    return {"algo": f"RSA-{m.group('bits')}", "mode": op, "result": f"{float(m.group('rate')):.3f} ops/s"}

def norm_rsa_oaep(m):
    raw = m.group("op").strip().lower().replace("  ", " ")
    mode = "public OAEP" if raw.startswith("pub") else "private OAEP"
    return {"algo": f"RSA-{m.group('bits')}", "mode": mode, "result": f"{float(m.group('rate')):.3f} ops/s"}

def norm_ecc(m):
    kind = m.group("kind").upper()
    return {"algo": f"{kind}-{m.group('bits')}", "mode": m.group("op").replace("  ", " "), "result": f"{float(m.group('rate')):.3f} ops/s"}

def parse_line(s: str):
    s = s.strip()
    if not s:
        return None
    if re_reset.search(s):
        return {"reset": True}
    if re_done.search(s):
        return {"done": True}
    for rx, fn in (
        (re_stream,        norm_stream),
        (re_rsa_keygen,    norm_rsa_keygen),
        (re_rsa_pubpriv,   norm_rsa_pubpriv),
        (re_rsa_oaep,      norm_rsa_oaep),
        (re_ecc,           norm_ecc),
    ):
        m = rx.match(s)
        if m:
            return fn(m)
    return None

# -------- state ----------
rows = OrderedDict()  # key: (algo, mode) -> dict
order = []            # insertion order keys
abs_index = {}        # key -> stable insertion index for row striping

# -------- rendering ----------
def build_table():
    t = Table(
        expand=False,
        show_edge=True,
        header_style="bold",
        padding=(0, CELL_PAD),
        pad_edge=False,
        show_lines=False,
        title=None,
        box=box.ROUNDED,
        leading=0
    )
    t.add_column("Algo",    width=COL_ALGO,   no_wrap=True, overflow="ellipsis", style="bold")
    t.add_column("Mode/Op", width=COL_MODE,   no_wrap=True, overflow="ellipsis")
    t.add_column("Result",  width=COL_RESULT, no_wrap=True, overflow="ellipsis", justify="right", style="bold")
    return t

def make_table_for_keys(keys, highlight_key=None):
    t = build_table()
    for k in keys:
        d = rows[k]
        idx = abs_index.get(k, 0)
        # stable striping first
        row_style = "" if (idx % 2 == 0) else "dim"
        # newest-row highlight overrides striping when in view
        if highlight_key is not None and k == highlight_key:
            row_style = "bold green"
        t.add_row(d["algo"], d["mode"], colorize_result(d["result"]), style=row_style)
    return Align.center(t)

def colorize_result(s: str) -> str:
    if "KB/s" in s:
        num, unit = s.split(" ", 1)
        return f"[bold]{num}[/bold] [cyan]{unit}[/cyan]"
    if "ops/s" in s:
        num, unit = s.split(" ", 1)
        return f"[bold]{num}[/bold] [magenta]{unit}[/magenta]"
    return s

def layout_frame():
    lay = Layout()
    lay.split_column(
        Layout(name="hdr", size=3),
        Layout(name="tbl", ratio=1),
        Layout(name="ftr", size=1),
    )
    return lay

def header(dots: int):
    dots_str = ""
    txt = Text.from_markup(
        ":wolf: [underline][bold white]wolf[/bold white][bold cyan]SSL[/bold cyan] [bold white]wolf[/bold white][bold cyan]TPM[/bold cyan] [bold green]Benchmark[/bold green] [bold red]LIVE[/bold red][/underline]"
    )
    if dots == 0:
        dots_str = "..."
    elif dots == 1:
        dots_str = "·.."
    elif dots == 2:
        dots_str = ".·."
    elif dots == 3:
        dots_str = "..·"
    txt.justify = "center"
    txt.append(Text.from_markup(f"[bold red]{dots_str}[/bold red]"))
    txt2 = Text.from_markup("[dim]TPM2 Wrapper API — parsing live UART output[/dim]", justify="center")
    return Group(txt, txt2)

def footer():
    return Align.center("[dim]ST33 SPI • TPM 2.0[/dim]")

def visible_capacity():
    term_h = console.size.height
    # 3 (hdr) + 1 (ftr) + 2 (margins) + 3 (table header/borders) = 9
    reserved = 9
    return max(1, term_h - reserved)

# -------- main ----------
def main():
    dot_counter = 0  # cycles 0..3
    lay = layout_frame()
    lay["hdr"].update(header(0))
    lay["ftr"].update(footer())

    last_hdr = time.monotonic()
    newest_key = None

    with Live(lay, refresh_per_second=8, console=console, screen=True):
        for s in line_iter():
            # periodic header update
            now = time.monotonic()
            if now - last_hdr >= HDR_PERIOD:
                dot_counter = (dot_counter + 1) % 4
                lay["hdr"].update(header(dot_counter))
                last_hdr = now

            d = parse_line(s)
            if not d:
                continue

            if d.get("reset"):
                rows.clear(); order.clear(); abs_index.clear()
                newest_key = None
                lay["tbl"].update(make_table_for_keys([]))
                continue

            if d.get("done"):
                cap = visible_capacity()
                window = order[-cap:]
                lay["tbl"].update(make_table_for_keys(window, highlight_key=newest_key if newest_key in window else None))
                continue

            key = (d["algo"], d["mode"])
            if key not in rows:
                rows[key] = d
                order.append(key)
                abs_index[key] = len(abs_index)  # stable index
            else:
                rows[key] = d  # update existing row content

            newest_key = key  # track most recent update/insert
            cap = visible_capacity()
            window = order[-cap:]
            lay["tbl"].update(make_table_for_keys(window, highlight_key=newest_key if newest_key in window else None))

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
