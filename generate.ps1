docker run --rm `
  -v ${PWD}:/local `
  openapitools/openapi-generator-cli generate `
  -i /local/app/src/openapi/product-api.yaml `
  -g python-fastapi `
  -o /local/app/generated