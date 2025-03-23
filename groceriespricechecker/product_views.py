# groceries/product_views.py

import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

class ProductFromBarcodeAPIView(APIView):
    def post(self, request, format=None):
        # Get the barcode number from the request data
        barcode_number = request.data.get("barcode_number")
        if not barcode_number:
            return Response(
                {"error": "barcode_number is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Build the full URL using environment variables
        api_url = settings.BARCODE_LOOKUP_URL  # e.g. "https://api.barcodelookup.com/v3/products"
        api_key = settings.BARCODE_LOOKUP_KEY  # Your API key
        full_url = f"{api_url}?barcode={barcode_number}&formatted=y&key={api_key}"

        try:
            external_response = requests.get(full_url, timeout=10)
            if external_response.status_code != 200:
                return Response(
                    {"error": "Error from external API", "status_code": external_response.status_code},
                    status=status.HTTP_502_BAD_GATEWAY
                )
            data = external_response.json()
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
