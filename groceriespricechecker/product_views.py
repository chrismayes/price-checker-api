# groceries/product_views.py

import requests
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Grocery
from django.utils.dateparse import parse_datetime
from django.utils.timezone import make_aware


class ProductFromBarcodeAPIView(APIView):

    def post(self, request, format=None):
        barcode_number = request.data.get("barcode_number")
        if not barcode_number:
            return Response(
                {"error": "barcode_number is required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        now = timezone.now()

        # Check if barcode exists in local DB
        grocery, created = Grocery.objects.get_or_create(barcode_number=barcode_number)

        needs_update = False

        if created:
            needs_update = True  # Newly created record
        else:
            # Check if older than 6 months and not manually entered
            if grocery.manually_entered:
                needs_update = False
            elif grocery.barcode_api_last_checked:
                six_months_ago = now - timedelta(days=180)
                if grocery.barcode_api_last_checked < six_months_ago:
                    needs_update = True
            else:
                needs_update = True  # Never checked before

        if needs_update:
            api_url = settings.BARCODE_LOOKUP_URL
            api_key = settings.BARCODE_LOOKUP_KEY
            full_url = f"{api_url}?barcode={barcode_number}&formatted=y&key={api_key}"

            try:
                external_response = requests.get(full_url, timeout=10)
                grocery.barcode_api_last_checked = now

                if external_response.status_code == 200:
                    data = external_response.json()
                    if data.get("products"):
                        product = data["products"][0]
                        # Update local record
                        grocery.name = product.get("title", grocery.name or "Unknown Product")
                        grocery.description = product.get("description", "")
                        grocery.category = product.get("category", "")
                        grocery.brand = product.get("brand", "")
                        grocery.size = product.get("size", "")
                        grocery.image_url = product["images"][0] if product.get("images") else None
                        if product.get("stores"):
                            store = product["stores"][0]
                            grocery.store_name = store.get("name", "")
                            grocery.store_price = store.get("price") or None
                            last_update_str = store.get("last_update")
                            if last_update_str:
                                parsed_date = parse_datetime(last_update_str)
                                if parsed_date:
                                    grocery.store_price_last_updated = make_aware(parsed_date)
                                else:
                                    grocery.store_price_last_updated = None
                            else:
                                grocery.store_price_last_updated = None
                        grocery.barcode_lookup_failed = False
                        grocery.save()
                    else:
                        # Barcode doesn't exist on API
                        grocery.barcode_lookup_failed = True
                        grocery.save()
                        return Response({"error": "Barcode not found in external API."},
                                        status=status.HTTP_404_NOT_FOUND)
                else:
                    grocery.save()
                    return Response(
                        {"error": "External API error", "status_code": external_response.status_code},
                        status=status.HTTP_502_BAD_GATEWAY
                    )

            except Exception as e:
                grocery.save()
                return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Build response from grocery instance
        response_data = {
            "barcode_number": grocery.barcode_number,
            "title": grocery.name,
            "description": grocery.description,
            "category": grocery.category,
            "brand": grocery.brand,
            "size": grocery.size,
            "images": [grocery.image_url] if grocery.image_url else [],
            "stores": [{
                "name": grocery.store_name,
                "price": str(grocery.store_price) if grocery.store_price else "",
                "last_update": grocery.store_price_last_updated.strftime("%Y-%m-%d %H:%M:%S") if grocery.store_price_last_updated else ""
            }] if grocery.store_name else [],
            "manually_entered": grocery.manually_entered,
            "barcode_lookup_failed": grocery.barcode_lookup_failed,
            "barcode_api_last_checked": grocery.barcode_api_last_checked.strftime("%Y-%m-%d %H:%M:%S") if grocery.barcode_api_last_checked else ""
        }

        return Response({"products": [response_data]}, status=status.HTTP_200_OK)
