# cv

Auto-builds a LaTeX CV from two live sources every two weeks:

| Source | What it pulls |
|---|---|
| [Zotero public library](https://api.zotero.org/users/11988712/publications/items) | All publications (journal articles, talks, reports, media, …) |
| [`noahweidig.github.io` — `data/authors/me.yaml`](https://github.com/noahweidig/noahweidig.github.io/blob/main/data/authors/me.yaml) | Education, experience, awards, skills |

## How it works

```
scripts/build.py          # fetch → render template/cv.tex.j2 → write cv.tex
xelatex cv.tex            # compile (2 passes for cross-refs)
output/cv.pdf             # committed back to repo
```

## Schedule

GitHub Actions runs on the **1st and 15th of every month** (and on any push that changes the template or script).  The compiled `output/cv.pdf` is committed automatically.

## Local build

```bash
pip install -r requirements.txt
python scripts/build.py
xelatex cv.tex && xelatex cv.tex
```

Requires a TeX Live installation with `texlive-xetex`, `texlive-latex-extra`, and `texlive-fonts-recommended`.
