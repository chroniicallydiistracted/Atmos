.PHONY: build-images push-images fonts importer renderer validate

build-images:
	bash scripts/build_cyclosm_images.sh

push-images:
	bash scripts/push_cyclosm_images.sh

fonts:
	docker run --rm -v $$PWD/services/cyclosm/fonts:/out cyclosm-fonts:local bash -lc 'node generate-font-pbfs.js && node generate-font-manifest.js && cp -r fonts-pbf /out/'

upload-fonts:
	@test -n "$$S3_FONTS_PATH" || (echo "Set S3_FONTS_PATH to s3://bucket/fonts" && exit 2)
	bash scripts/upload_fonts_to_s3.sh services/cyclosm/fonts/fonts-pbf $$S3_FONTS_PATH

importer:
	docker run --rm -e PGHOST -e PGUSER -e PGPASSWORD -e PGDATABASE -e THREADS=8 -v $$PWD/services/cyclosm/importer:/import cyclosm-importer:local

renderer:
	docker run --rm -p 8080:8080 -e PGHOST -e PGUSER -e PGPASSWORD -e PGDATABASE -e TILE_S3_BUCKET -e TILE_S3_PREFIX -e AWS_REGION -e METATILE=8 cyclosm-renderer:local

validate:
	node scripts/validate_cyclosm_tiles.js
