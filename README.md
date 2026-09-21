# DexTacWAM Project Page

A static academic project page for **DexTacWAM: A Visuo-Tactile World-Action Model for
Dexterous Manipulation**, adapting the
[Nerfies](https://github.com/nerfies/nerfies.github.io) and
[Academic Project Page](https://github.com/eliahuhorwitz/Academic-project-page-template)
templates.

## Structure

```
.
├── index.html                    # all page content / sections
├── static/
│   ├── css/style.css             # styling
│   ├── js/main.js                # scroll progress, TOC scroll-spy, nav toggle, copy-BibTeX
│   ├── images/                   # figures
│   └── videos/
│       ├── web/                  # transcoded, published clips (mp4 + poster jpg)
│       └── demos/                # raw iPhone .MOV originals — GITIGNORED, ~900 MB
└── tools/
    ├── build_web_videos.py       # source clips -> web mp4 + poster frames
    ├── make_contact_sheet.py     # QA grid of all transcoded clips
    └── preview.html              # local asset preview page
```

## Preview locally

```bash
python3 -m http.server 8000
# open http://localhost:8000
```

## Page narrative

The section order follows the DexTacWAM talk deck:

1. **Motivation** — reactive tactile policies → predictive tactile world models.
2. **Key insight** — pretrain the lightweight tactile encoder on four hours of data, then
   directly adapt a pretrained video model to touch without tactile midtraining.
3. **Bottleneck** — ten fingertip views would explode DiT tokens; compression to two hand views.
4. **Method** — system overview, multi-finger tactile encoder, three training stages.
5. **Per-module ablation** — contact recall/retention through five-finger fusion.
6. **Six tasks** — Cube Place, Handover, Wipe, Tongs, Bowl, Bottle Cap, with rollout videos.
7. **Quantitative results** — per-task table, policy ablations, generalization, significance.
8. **World-model prediction** — long-horizon 4-column rollout video and prediction metrics.
9. **Continual learning** — tactile is gained without losing RGB prediction ability.

Headline numbers: **70.6** average across six tasks vs **38.0** for the strongest baseline;
removing tactile *prediction* (while keeping tactile input) drops the four-task mean
**74.7 → 26.6**; tactile compression provides **2.26× faster training** and
**1.29× faster inference**.

## Video assets

Published clips live in `static/videos/web/` as H.264 mp4 with `+faststart` and a matching
`_poster.jpg` first frame. The raw `.MOV` originals in `static/videos/demos/` are gitignored —
GitHub Pages only needs the transcoded files. To regenerate after adding new source footage:

```bash
python3 tools/build_web_videos.py
```

## What you still need to customize

Everything is plain HTML — edit `index.html` directly. Add the Paper, arXiv, and Video
buttons once their public URLs are available. Colors can be adjusted through the `:root`
variables at the top of `style.css` (for example, `--accent`).

## Deploy to GitHub Pages

This repository is the organization site for `dextacwam`, so pushing to `main` publishes to
https://dextacwam.github.io/ directly, with no subpath. If Pages is not yet enabled, set
**Settings → Pages** to branch `main` / folder `/ (root)`. Every path in `index.html` is
relative, so the same tree also serves correctly from a subdirectory or from `file://`.

## License

Released under the MIT License; see [LICENSE](LICENSE). The figures and videos depict
results from the DexTacWAM paper — please cite the paper if you reuse them.
