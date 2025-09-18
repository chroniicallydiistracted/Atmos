#!/usr/bin/env bash
set -euo pipefail
: "${AWS_ACCOUNT_ID:?AWS_ACCOUNT_ID required}"
: "${AWS_REGION:=us-east-1}"

REPO_BASENAME=${REPO_BASENAME:-atmos}

RENDERER_REPO=${RENDERER_REPO:-${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_BASENAME}-cyclosm-renderer}
IMPORTER_REPO=${IMPORTER_REPO:-${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_BASENAME}-cyclosm-importer}
HILLSHADE_REPO=${HILLSHADE_REPO:-${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_BASENAME}-cyclosm-hillshade}
FONTS_REPO=${FONTS_REPO:-${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_BASENAME}-cyclosm-fonts}

TAG=${TAG:-$(date +%Y%m%d%H%M%S)}

echo "== ECR Login =="
aws ecr get-login-password --region "$AWS_REGION" | docker login --username AWS --password-stdin "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "== Tag & Push =="

push_if_exists() {
	local image_local="$1" repo_uri="$2" tag="$3"
	if aws ecr describe-repositories --repository-names "${repo_uri##*/}" --region "$AWS_REGION" >/dev/null 2>&1; then
		docker tag "$image_local" "$repo_uri:$tag"
		docker push "$repo_uri:$tag"
	else
		echo "[SKIP] ECR repo not found: ${repo_uri##*/}"
	fi
}

push_if_exists cyclosm-renderer:local "$RENDERER_REPO" "$TAG"
push_if_exists cyclosm-renderer:local "$RENDERER_REPO" latest

push_if_exists cyclosm-importer:local "$IMPORTER_REPO" "$TAG"
push_if_exists cyclosm-importer:local "$IMPORTER_REPO" latest

push_if_exists cyclosm-hillshade:local "$HILLSHADE_REPO" "$TAG"
push_if_exists cyclosm-hillshade:local "$HILLSHADE_REPO" latest

push_if_exists cyclosm-fonts:local "$FONTS_REPO" "$TAG" || true
push_if_exists cyclosm-fonts:local "$FONTS_REPO" latest || true

echo "Pushed tag $TAG"
