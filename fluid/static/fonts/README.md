# Local fonts

Sora (weights 400–800), Inter (400–600) and JetBrains Mono (400–500), Latin and Latin Extended
subsets, are served locally through `fonts.css` with `font-display: swap`.
The six WOFF2 files total 213,820 bytes. The browser loads only the subsets it needs.

Sources: Google Fonts CSS API and its `fonts.gstatic.com` font files, retrieved 2026-11-01.
The unmodified font binaries retain the corresponding SIL Open Font License notices in this
folder (`sora-OFL.txt`, `inter-OFL.txt`, `jetbrainsmono-OFL.txt`). No runtime request goes to those
services. Keep the license notices and update filenames when replacing cached font binaries.
