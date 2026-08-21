# Ramps and Batteries

**Interactive deck: https://lampspuc.github.io/ramps-and-batteries/**

Why a battery earns what it earns, worked out first on a two-unit example small
enough to check by hand, and then on a real day of the Brazilian power system.

The page runs in English, Portuguese, Spanish and Chinese, and the last slide
lets you move the hydro ramp limit and the battery size and watch prices, the
merit order and the settlement table respond.

The argument in one line: **a ramp constraint, not a shortage of energy, is what
pulls two hours apart in price**, and the value of storage is the size of that
gap. On 4 February 2026 the Brazilian system moved 43 GW between the midday
trough and the evening peak while gross load barely changed, and the marginal
cost multiplied by eight.

## Contents

| Path | What it is |
|---|---|
| `slides/when-the-price-tells-the-truth.pdf` | Nine slides, English. |
| `slides/preco-diz-a-verdade.pdf` | The same nine slides, Portuguese. |
| `slides/*.tex`, `slides/figures/` | Beamer sources. pdfLaTeX, no external images: every figure is TikZ. |
| `index.html` | The interactive deck, served at the link above. Self-contained, no build step: open the file in a browser and it works offline too. |
| `model/modelo.py` | The two-hour dispatch model. The reference implementation. |
| `model/solver.js` | The same model in JavaScript, driving the interactive page. Reproduces `modelo.py` digit for digit. |
| `model/despacho-check.py` | The textbook example, solved as an LP and verified three ways. |
| `model/gerar_tikz.py` | Emits the TikZ figures and the settlement table from the same data, so slides and page cannot drift apart. |
| `data/` | The merit-order stack, the day's series, and `FONTES.md` with the provenance of every number. |

## The two-unit example

Two thermal units, unlimited capacity, variable cost 100 and 300 R$/MWh, ramp-up
limit 25 MWh/h for both. Demand of 100 MWh in the first hour and 130 MWh in the
second. The optimal dispatch gives:

```
mu_1     = c2 - c1      = 200 R$/MWh     rent on the binding ramp
lambda_1 = c1 - mu_1    = -100 R$/MWh    price in the first hour
lambda_2 = c1 + mu_1    = +300 R$/MWh    price in the second
spread   = 2 (c2 - c1)  =  400 R$/MWh    twice the cost difference
```

The price in the first hour is negative and no generator loses money: revenue
adequacy and cost recovery both hold. A 1 MWh battery earns exactly 400, which is
exactly what it saves the system. Push storage past 2.5 MWh and the rent
disappears, because the ramp stops binding.

## The Brazilian day

Wednesday, 4 February 2026, chosen by scanning 180 days of half-hourly marginal
cost and taking the largest trough-to-peak spread.

| Average MW | t1 · 12:00 | t2 · 19:00 | Δ |
|---|---:|---:|---:|
| Gross load | 97,168 | 99,352 | +2,185 |
| Wind + solar | 41,281 | 5,464 | −35,816 |
| Distributed solar | 28,428 | 278 | −28,150 |
| **Controllable fleet** | **50,148** | **93,111** | **+42,963** |
| Marginal cost, SE (R$/MWh) | 309 | 2,521 | ×8.2 |
| Settlement price, SE (R$/MWh) | 350 | 1,200 | ×3.4 |

Hydro is split into the part that cannot ramp (the day's floor: run-of-river,
minimum flow, multiple water uses) and the part that can. The ramp parameter
applies only to the flexible part. On that day the flexible fleet ramped at
14.3%/h of its own capacity.

## Data sources

Everything comes from the Brazilian system operator (ONS) and the market chamber
(CCEE), both open data. `data/FONTES.md` lists each query and records one caveat
worth reading: the operator's load series and its generation balance account for
distributed solar on different bases, so the identity
`generation = load − distributed − wind − solar` does not close. The model
therefore uses the measured sum of hydro and thermal, which is what the
controllable fleet actually delivered and depends on no accounting assumption.

## Reproducing

```
python3 model/despacho-check.py     # the two-unit example, three independent checks
python3 model/modelo.py             # the Brazilian day
cd slides && pdflatex when-the-price-tells-the-truth.tex
```

`model/modelo.py` needs `scipy` only for `despacho-check.py`; the two-hour model
is plain Python.

## How to cite

GitHub reads `CITATION.cff`, so the **Cite this repository** button on the
sidebar gives you the reference in APA and BibTeX. In short:

> Street, A. (2026). *Ramps and Batteries: why a battery earns what it earns*
> (Version 1.0.0). LAMPS, PUC-Rio. https://github.com/LAMPSPUC/ramps-and-batteries

## License

Copyright © 2026 Alexandre Street de Aguiar.

The slides, figures, text and data are licensed under
[CC BY 4.0](https://creativecommons.org/licenses/by/4.0/): use, adapt and
redistribute them, including commercially, as long as you give credit, say
whether you changed anything, and link to the license. Full text in `LICENSE`.

The code in `model/` is additionally available under the MIT license, in
`LICENSE-CODE`, since a content licence is not written for software.

---

Alexandre Street · LAMPS, PUC-Rio
