.PHONY: teaser remotion-preview remotion-render

teaser:
	python3 scripts/make_video.py --config scripts/samples/teaser.json

remotion-preview:
	cd content_studio/remotion && npm run preview

remotion-render:
	cd content_studio/remotion && npm run render -- --sequence short-teaser
