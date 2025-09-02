#!/bin/bash

cd "$(dirname "$0")"/.. || exit 1

echo "Building Virtual Substation with IEC 61850..."

# Optional: generate static model from SCL if generator is available
if [ -f libiec61850/tools/model_generator/build/libs/model-generator.jar ] && [ -f config/models/compact_ied.icd ]; then
  echo "Generating static model from SCL (compact_ied.icd)..."
  mkdir -p src/generated
  java -jar libiec61850/tools/model_generator/build/libs/model-generator.jar \
    -i config/models/compact_ied.icd \
    -o src/generated \
    -p IEDMODEL \
    || echo "Model generation failed; continuing with existing static model."
  if [ -f src/generated/static_model.c ] && [ -f src/generated/static_model.h ]; then
    cp -f src/generated/static_model.c src/static_model.c
    cp -f src/generated/static_model.h src/static_model.h
    echo "Static model updated from SCL."
  fi
else
  echo "SCL model generator not found or ICD missing. Skipping model generation."
  echo "You can generate it manually if desired. See docs below."
fi

# Build Docker images
echo "Building Protection Relay IED..."
docker build -f config/Dockerfile.protection-relay -t protection-relay:latest .

echo "Building Circuit Breaker IED..."
docker build -f config/Dockerfile.circuit-breaker -t circuit-breaker:latest .

echo "Building HMI/SCADA..."
docker build -f config/Dockerfile.hmi-scada -t hmi-scada:latest .

echo "Build complete!"
echo ""
echo "To start the virtual substation:"
echo "  docker-compose up"
echo ""
echo "To stop the virtual substation:"
echo "  docker-compose down"
