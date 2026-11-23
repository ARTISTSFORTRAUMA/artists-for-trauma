# Build tools (Phase 2 prototype)

These scripts generate the static pages in this repo. Netlify serves the repo as-is; nothing here runs on Netlify.

- `nav.py`: shared main menu (old-site layout).
- `build_blog.py`: /blog/ and the 185 posts at /YYYY/MM/slug/ (source: WordPress JSON export, backup in Desktop "AFT WEB Phase 2/08-Blog-Archive").
- `build_pages.py`: imported pages, /calendar/ and /site-archive/ (source: "09-Site-Pages-Archive").
- `build_published.py` + `awarenow-features.json`: /published-features/. Each feature lists its Issuu issue, page range, title, intro, body paragraphs. Magazine page images already live in published-features/<slug>/pages/.

## Adding an AwareNow feature
1. Find the issue on issuu.com/awarenessties and its document id (the `image.isu.pub/<id>/jpg/page_1.jpg` pattern). Page images: `https://image.isu.pub/<id>/jpg/page_<n>.jpg` (needs image.isu.pub in Claude's allowed domains, already added).
2. OCR the text pages at 3x with tesseract (`--psm 3`), clean up, and add an entry to awarenow-features.json (folder = where the page jpgs are).
3. Run build_published.py with the repo path, check, commit, push. Netlify publishes in about a minute.

Optional feature fields: `sort` (number used to order the Published Features grid when an issue has no number, e.g. 30.5 for "The Dreams Edition: Love Louisville Style"); leave `num` null and the "Issue N" label is omitted. Body paragraphs that contain line breaks (poems, lists) keep them on the page.

## Feature articles (Template #1)
`build_feature.py <source.html> <images.json> <slug> .` builds /features/<slug>/ from a Template #1 source (photos are `{{name}}` placeholders). Images go to features/<slug>/img/; an image already there is kept, so a high-res replacement can be dropped in under the same name and the page rebuilt. Add the slug to `ARTICLES` in index.html so its cover on the homepage opens the article.
- Ford Austin: _build/feature-template/ford-austin-source.html → /features/ford-austin/
