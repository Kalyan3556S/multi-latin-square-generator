# Multi-Latin Square Explorer

Implements Construction 3.2 from Hoffman, Johnson and Schloss,
*Existence of multi-latin squares satisfying a persistent Sudoku condition*,
Australasian Journal of Combinatorics 95(1), 2026, pp. 83–90.
Source: https://ajc.maths.uq.edu.au/pdf/95/ajc_v95_p083.pdf

## Run

Use Python 3.9 or newer. No pip packages are needed. The graphical interface
uses Tkinter, which is included with the usual Windows python.org installer.

From a terminal in the folder containing the script:

```powershell
python multi_latin_generator.py
```

This opens a colored 10 × 10 grid with m=5, k=2, d=2. Edit the three inputs and
press Generate. Move the mouse across the grid to highlight a sliding block.
The block's coordinates and distinct-symbol count appear below it. Row and
column labels are one-based; the symbols start at zero. Numbers remain visible
so interpreting a grid does not depend only on color.

Choose your own initial parameters:

```powershell
python multi_latin_generator.py --m 10 --k 2 --d 3
```

For a terminal or notebook environment without a graphical display:

```powershell
python multi_latin_generator.py --m 10 --k 2 --d 3 --no-gui --csv square.csv
```

If your Windows installation uses the Python launcher, replace `python` with `py`.

## Interpretation

- `m`: number of symbols, numbered 0 through m−1.
- `k`: each symbol occurs exactly k times in every row and every column.
- `n = m*k`: side length of the generated square.
- `d`: every overlapping d × d block must have d² distinct entries.
- For d>1, existence requires and is guaranteed by m ≥ d²+1.
- d=1 has a trivial block condition; this implementation also supports it
  when d<n, as required by the paper's definition.
- k=1 gives an ordinary Latin square; k>1 gives the paper's multi-Latin square.

Construction: let g=gcd(n,d), h=n/g, p=r mod h, q=floor(r/h).
At zero-based position (r,c), the symbol is `(c - (q + p*d)) % m`.

The validator independently checks the grid's dimensions, symbol range,
all row and column counts, and every overlapping block. The program constructs
one square per parameter set; it does not enumerate or randomly sample all
possible solutions. Repeating the same inputs gives the same square.

The demo limits n to 500. Grids up to 100 × 100 are drawn; larger grids can be
generated, validated and exported. Symbol colors can be similar for large m.
