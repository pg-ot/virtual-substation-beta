#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR=$(cd "$(dirname "$0")"/.. && pwd)
GEN_JAR="$ROOT_DIR/libiec61850/tools/model_generator/build/libs/model-generator.jar"
ICD_RELAY="$ROOT_DIR/config/models/compact_ied.icd"
ICD_BREAKER="$ROOT_DIR/config/models/compact_breaker.icd"
OUT_DIR="$ROOT_DIR/gen"

echo "Generating static models from SCL..."

if [ ! -f "$GEN_JAR" ]; then
  echo "Building model generator..."
  (cd "$ROOT_DIR/libiec61850/tools/model_generator" && ./gradlew build)
fi

mkdir -p "$OUT_DIR/relay" "$OUT_DIR/breaker"

if [ -f "$ICD_RELAY" ]; then
  echo "Relay: $ICD_RELAY"
  java -jar "$GEN_JAR" -i "$ICD_RELAY" -o "$OUT_DIR/relay" -p IEDMODEL
  cp -f "$OUT_DIR/relay/static_model.c" "$OUT_DIR/relay_static_model.c"
  cp -f "$OUT_DIR/relay/static_model.h" "$OUT_DIR/relay_static_model.h"
else
  echo "Relay ICD not found: $ICD_RELAY"
fi

if [ -f "$ICD_BREAKER" ]; then
  echo "Breaker: $ICD_BREAKER"
  java -jar "$GEN_JAR" -i "$ICD_BREAKER" -o "$OUT_DIR/breaker" -p IEDMODEL
  cp -f "$OUT_DIR/breaker/static_model.c" "$OUT_DIR/breaker_static_model.c"
  cp -f "$OUT_DIR/breaker/static_model.h" "$OUT_DIR/breaker_static_model.h"
else
  echo "Breaker ICD not found: $ICD_BREAKER"
fi

echo "Generated models are in $OUT_DIR"

