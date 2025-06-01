# PDF Metadata Service Documentation

This directory contains documentation for the PDF Metadata Service, a form-agnostic solution for extracting, storing, and managing metadata from PDF forms.

## Available Documentation

- [Integration Guide](pdf_metadata_service_integration.md) - Comprehensive guide for integrating with the PDF Metadata Service
- [API Reference](https://your-domain.com/api-docs) - OpenAPI/Swagger documentation
- [MongoDB Schema](https://your-domain.com/schema-docs) - Detailed database schema documentation

## Quick Links

- [Getting Started](#getting-started)
- [API Endpoints](#api-endpoints)
- [Integration Examples](#integration-examples)
- [Troubleshooting](#troubleshooting)

## Getting Started

1. **Installation**
   ```bash
   pip install requests  # For Python client
   ```

2. **Basic Usage**
   ```python
   import requests

   # Initialize client
   url = "http://your-domain/api/v1/pdf-metadata/extract"
   headers = {"Authorization": "Bearer your-api-key"}

   # Upload and extract metadata
   with open("form.pdf", "rb") as pdf:
       response = requests.post(url, files={"file": pdf}, headers=headers)
   
   metadata = response.json()
   ```

3. **Next Steps**
   - Review the [Integration Guide](pdf_metadata_service_integration.md) for detailed implementation
   - Check out example code in the integration guide
   - Set up proper error handling and caching

## Support

For additional support:
- Email: support@your-domain.com
- Documentation: https://your-domain.com/docs
- API Status: https://status.your-domain.com 