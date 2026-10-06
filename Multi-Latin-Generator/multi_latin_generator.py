"""Generate and inspect multi-Latin squares with a persistent Sudoku condition.

Implements Construction 3.2 in Hoffman, Johnson and Schloss (2026):
https://ajc.maths.uq.edu.au/pdf/95/ajc_v95_p083.pdf
Python 3.9+; standard library only. Tkinter is needed for the optional GUI.
"""

import argparse
import colorsys
import csv
from collections import Counter
from math import gcd


def generate_square(m, k, d):
    """Return one valid square for eligible positive integer parameters."""
    if any(type(v) is not int or v <= 0 for v in (m, k, d)):
        raise ValueError("m, k and d must be positive integers.")
    n = m * k
    if d >= n:
        raise ValueError("The paper requires d < n, where n = m * k.")
    if d > 1 and m < d * d + 1:
        raise ValueError(
            f"No square exists for these inputs: d={d} requires m >= {d*d+1}."
        )
    if n > 500:
        raise ValueError("This demo supports n = m * k up to 500.")
    g = gcd(n, d)
    h = n // g
    # r = p + q*h, so p = r % h and q = r // h.
    return [
        [(c - (r // h + (r % h) * d)) % m for c in range(n)]
        for r in range(n)
    ]


def validate_square(square, m, k, d):
    """Independently check shape, symbols, row/column counts and all windows.

    Return a report, with the first failing window represented by its zero-based
    top-left coordinates. These checks do not rely on the construction formula.
    """
    if any(type(v) is not int or v <= 0 for v in (m, k, d)):
        raise ValueError("m, k and d must be positive integers.")
    n = m * k
    if d >= n:
        raise ValueError("d must be smaller than n.")
    if len(square) != n or any(len(row) != n for row in square):
        return {"valid": False, "error": f"Expected a {n} x {n} square."}
    if any(type(s) is not int or not 0 <= s < m for row in square for s in row):
        return {"valid": False, "error": f"Symbols must be integers from 0 to {m-1}."}
    expected = Counter({symbol: k for symbol in range(m)})
    rows_ok = all(Counter(row) == expected for row in square)
    columns_ok = all(
        Counter(square[r][c] for r in range(n)) == expected for c in range(n)
    )
    first_bad = None
    checked = 0
    # Slide horizontally: update only the departing/arriving window columns.
    for top in range(n - d + 1):
        counts = Counter(
            square[r][c] for r in range(top, top + d) for c in range(d)
        )
        for left in range(n - d + 1):
            if left:
                for r in range(top, top + d):
                    old = square[r][left - 1]
                    counts[old] -= 1
                    if counts[old] == 0:
                        del counts[old]
                    counts[square[r][left + d - 1]] += 1
            checked += 1
            if len(counts) != d * d and first_bad is None:
                first_bad = (top, left)
    return {
        "valid": rows_ok and columns_ok and first_bad is None,
        "rows_ok": rows_ok,
        "columns_ok": columns_ok,
        "blocks_ok": first_bad is None,
        "blocks_checked": checked,
        "first_bad_block": first_bad,
    }


def save_csv(square, filename):
    with open(filename, "w", newline="", encoding="utf-8") as stream:
        csv.writer(stream).writerows(square)


def show_gui(m, k, d):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    root = tk.Tk()
    root.title("Multi-Latin Square Explorer")
    root.geometry("850x780")
    bar = ttk.Frame(root, padding=12)
    bar.pack(fill="x")
    inputs = {}
    for label, value in (("m", m), ("k", k), ("d", d)):
        ttk.Label(bar, text=label).pack(side="left", padx=(8, 4))
        var = tk.StringVar(value=str(value))
        ttk.Entry(bar, textvariable=var, width=6).pack(side="left")
        inputs[label] = var
    summary = tk.StringVar()
    ttk.Label(root, textvariable=summary, wraplength=810, padding=12).pack(fill="x")
    ttk.Label(
        root, text="Move the pointer over the grid to inspect an overlapping block."
    ).pack()
    frame = ttk.Frame(root, padding=12)
    frame.pack(fill="both", expand=True)
    canvas = tk.Canvas(frame, background="#f5f7fb", highlightthickness=0)
    vertical = ttk.Scrollbar(frame, orient="vertical", command=canvas.yview)
    horizontal = ttk.Scrollbar(frame, orient="horizontal", command=canvas.xview)
    canvas.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
    canvas.grid(row=0, column=0, sticky="nsew")
    vertical.grid(row=0, column=1, sticky="ns")
    horizontal.grid(row=1, column=0, sticky="ew")
    frame.rowconfigure(0, weight=1)
    frame.columnconfigure(0, weight=1)
    detail = tk.StringVar()
    ttk.Label(root, textvariable=detail, wraplength=810, padding=12).pack(fill="x")
    state = {}
    cell, margin = 36, 32

    def inspect(event):
        if not state or not state.get("drawn"):
            return
        square, block = state["square"], state["d"]
        n = len(square)
        x, y = canvas.canvasx(event.x), canvas.canvasy(event.y)
        if not (margin <= x < margin + n*cell and margin <= y < margin + n*cell):
            return
        left = min(int((x-margin)//cell), n-block)
        top = min(int((y-margin)//cell), n-block)
        canvas.delete("window")
        canvas.create_rectangle(
            margin+left*cell, margin+top*cell,
            margin+(left+block)*cell, margin+(top+block)*cell,
            outline="#111827", width=4, tags="window"
        )
        values = [square[r][c] for r in range(top, top+block)
                  for c in range(left, left+block)]
        distinct = len(set(values))
        detail.set(
            f"Rows {top+1}–{top+block}, columns {left+1}–{left+block}: "
            f"{distinct} distinct symbols in {block*block} cells. "
            + ("PASS: no repetition." if distinct == block*block else "FAIL: repeated symbols.")
        )

    def generate():
        try:
            mm, kk, dd = (int(inputs[key].get()) for key in ("m", "k", "d"))
            square = generate_square(mm, kk, dd)
            report = validate_square(square, mm, kk, dd)
        except ValueError as error:
            messagebox.showerror("Invalid inputs", str(error))
            return
        state.update(square=square, m=mm, k=kk, d=dd, drawn=len(square) <= 100)
        n = len(square)
        summary.set(
            f"{n} × {n} grid · symbols 0–{mm-1} · each symbol appears {kk} "
            f"times per row and column.\n"
            f"Rows: {'PASS' if report['rows_ok'] else 'FAIL'} · "
            f"Columns: {'PASS' if report['columns_ok'] else 'FAIL'} · "
            f"All {report['blocks_checked']} overlapping {dd} × {dd} blocks: "
            f"{'PASS' if report['blocks_ok'] else 'FAIL'}"
        )
        canvas.delete("all")
        if n > 100:
            canvas.configure(scrollregion=(0, 0, 600, 120))
            canvas.create_text(20, 40, anchor="w", width=560,
                text="Generated and checked. Grids above 100 × 100 are available through CSV export.")
            detail.set("Reduce m or k to display the grid.")
            return
        canvas.configure(scrollregion=(0, 0, margin+n*cell+10, margin+n*cell+10))
        canvas.xview_moveto(0)
        canvas.yview_moveto(0)
        for i in range(n):
            canvas.create_text(margin+(i+.5)*cell, margin/2, text=str(i+1))
            canvas.create_text(margin/2, margin+(i+.5)*cell, text=str(i+1))
        for r, row in enumerate(square):
            for c, symbol in enumerate(row):
                rgb = colorsys.hsv_to_rgb(symbol/mm, .40, .97)
                color = "#" + "".join(f"{round(channel*255):02x}" for channel in rgb)
                x, y = margin+c*cell, margin+r*cell
                canvas.create_rectangle(x, y, x+cell, y+cell, fill=color, outline="white")
                canvas.create_text(x+cell/2, y+cell/2, text=str(symbol), fill="#111827")
        detail.set("Cell numbers are symbols; labels around the grid are row and column positions.")

    def export():
        if not state:
            return
        filename = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV file", "*.csv")],
            initialfile=f"multi_latin_m{state['m']}_k{state['k']}_d{state['d']}.csv"
        )
        if filename:
            try:
                save_csv(state["square"], filename)
                detail.set(f"Saved: {filename}")
            except OSError as error:
                messagebox.showerror("Export failed", str(error))

    ttk.Button(bar, text="Generate", command=generate).pack(side="left", padx=12)
    ttk.Button(bar, text="Export CSV", command=export).pack(side="left")
    canvas.bind("<Motion>", inspect)
    generate()
    root.mainloop()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m", type=int, default=5, help="Number of symbols (default: 5)")
    parser.add_argument("--k", type=int, default=2, help="Occurrences per row/column (default: 2)")
    parser.add_argument("--d", type=int, default=2, help="Sliding block side length (default: 2)")
    parser.add_argument("--no-gui", action="store_true", help="Print to the terminal instead")
    parser.add_argument("--csv", metavar="FILE", help="Also save the generated square as CSV")
    args = parser.parse_args()
    try:
        square = generate_square(args.m, args.k, args.d)
    except ValueError as error:
        parser.error(str(error))
    if args.csv:
        save_csv(square, args.csv)
        print(f"Saved CSV: {args.csv}")
    if args.no_gui:
        width = len(str(args.m-1))
        for row in square:
            print(" ".join(f"{symbol:{width}d}" for symbol in row))
        print("Validation:", validate_square(square, args.m, args.k, args.d))
    else:
        try:
            show_gui(args.m, args.k, args.d)
        except ImportError:
            parser.exit(1, "Tkinter is unavailable. Run with --no-gui or install Python with Tk support.\n")


if __name__ == "__main__":
    main()
