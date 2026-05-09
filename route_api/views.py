from rest_framework.views import APIView
from rest_framework.response import Response
from django.shortcuts import render

from pathlib import Path

import pandas as pd
import requests
import math


# =========================================================
# PROJECT BASE DIRECTORY
# =========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# =========================================================
# FRONTEND HOME PAGE
# =========================================================

def home(request):

    # Frontend HTML page render
    return render(
        request,
        'index.html'
    )


# =========================================================
# LOCATION SUGGESTION API
# =========================================================

class LocationSuggestionAPIView(APIView):

    def get(self, request):

        # User input
        query = request.GET.get(
            'query',
            ''
        )

        # Empty query
        if not query:

            return Response([])

        # =================================================
        # CSV FILE PATH
        # =================================================

        csv_path = (

            BASE_DIR /

            'data' /

            'fuel-prices-for-be-assessment.csv'
        )

        # CSV read
        df = pd.read_csv(csv_path)

        # City + State combine
        df['full_location'] = (

            df['City']
            + ', ' +
            df['State']
        )

        # Duplicate remove
        locations = (

            df['full_location']
            .drop_duplicates()
            .tolist()
        )

        # Matching locations
        matched_locations = [

            location

            for location in locations

            if query.lower()
            in location.lower()
        ]

        # Top 8 suggestions
        suggestions = (
            matched_locations[:8]
        )

        return Response(
            suggestions
        )


# =========================================================
# MAIN FUEL ROUTE API
# =========================================================

class FuelRouteAPIView(APIView):

    def get(self, request):

        # =================================================
        # USER INPUT
        # =================================================

        start = request.GET.get(
            'start'
        )

        end = request.GET.get(
            'end'
        )

        # Vehicle type
        vehicle = request.GET.get(
            'vehicle',
            'truck'
        )

        # =================================================
        # VALIDATION
        # =================================================

        if not start or not end:

            return Response({

                "success": False,

                "message":
                "Start aur destination required hai"
            })

        # =================================================
        # OPENROUTESERVICE API KEY
        # =================================================

        api_key = (
            "eyJvcmciOiI1YjNjZTM1OTc4NTExMTAwMDFjZjYyNDgiLCJpZCI6Ijc1OTBjZTc2MmI3MjRhY2JiNTQyNjliNWM1MjZkYzY1IiwiaCI6Im11cm11cjY0In0="
        )

        # =================================================
        # START LOCATION SEARCH
        # =================================================

        start_url = (

            f"https://api.openrouteservice.org/"
            f"geocode/search?"
            f"api_key={api_key}&text={start}"
        )

        start_response = (

            requests.get(
                start_url
            ).json()
        )

        # Invalid start location
        if not start_response.get(
            'features'
        ):

            return Response({

                "success": False,

                "message":
                "Invalid start location"
            })

        # Start coordinates
        start_coords = (

            start_response['features'][0]
            ['geometry']['coordinates']
        )

        # =================================================
        # END LOCATION SEARCH
        # =================================================

        end_url = (

            f"https://api.openrouteservice.org/"
            f"geocode/search?"
            f"api_key={api_key}&text={end}"
        )

        end_response = (

            requests.get(
                end_url
            ).json()
        )

        # Invalid destination
        if not end_response.get(
            'features'
        ):

            return Response({

                "success": False,

                "message":
                "Invalid destination location"
            })

        # End coordinates
        end_coords = (

            end_response['features'][0]
            ['geometry']['coordinates']
        )

        # =================================================
        # ROUTE API
        # =================================================

        route_url = (

            "https://api.openrouteservice.org/"
            "v2/directions/driving-car"
        )

        # API headers
        headers = {

            "Authorization":
            api_key,

            "Content-Type":
            "application/json"
        }

        # API body
        body = {

            "coordinates": [

                start_coords,

                end_coords
            ],

            "instructions": False,

            "geometry": True
        }

        # Route request
        route_response = requests.post(

            route_url,

            json=body,

            headers=headers
        )

        # JSON response
        route_data = (
            route_response.json()
        )

        # =================================================
        # ROUTE ERROR HANDLE
        # =================================================

        if 'routes' not in route_data:

            return Response({

                "success": False,

                "message":
                "Route generate nahi ho paya",

                "api_error":
                route_data
            })

        # =================================================
        # ROUTE SUMMARY
        # =================================================

        route_summary = (

            route_data['routes'][0]
            ['summary']
        )

        # Distance in meters
        distance_meters = (
            route_summary['distance']
        )

        # Duration in seconds
        duration_seconds = (
            route_summary['duration']
        )

        # Convert miles
        distance_miles = (

            distance_meters
            * 0.000621371
        )

        # Convert kilometers
        distance_km = (
            distance_meters / 1000
        )

        # Convert hours
        duration_hours = (
            duration_seconds / 3600
        )

        # =================================================
        # ROUTE MAP DATA
        # =================================================

        route_coordinates = (

            route_data['routes'][0]
            ['geometry']
        )

        # =================================================
        # VEHICLE SETTINGS
        # =================================================

        if vehicle == 'truck':

            mileage = 10

            vehicle_name = "Truck"

        elif vehicle == 'suv':

            mileage = 18

            vehicle_name = "SUV"

        elif vehicle == 'sedan':

            mileage = 25

            vehicle_name = "Sedan"

        else:

            mileage = 10

            vehicle_name = "Truck"

        # =================================================
        # FUEL CALCULATION
        # =================================================

        # Fuel gallons
        fuel_needed_gallons = (
            distance_miles / mileage
        )

        # Convert liters
        fuel_needed_liters = (

            fuel_needed_gallons
            * 3.78541
        )

        # =================================================
        # CSV LOAD
        # =================================================

        csv_path = (

            BASE_DIR /

            'data' /

            'fuel-prices-for-be-assessment.csv'
        )

        # CSV read
        df = pd.read_csv(
            csv_path
        )

        # =================================================
        # CHEAPEST FUEL STOP
        # =================================================

        cheapest_stop = (

            df.sort_values(
                by='Retail Price'
            ).iloc[0]
        )

        # =================================================
        # COST CALCULATION
        # =================================================

        average_price = (
            df['Retail Price'].mean()
        )

        total_cost = (

            fuel_needed_gallons
            * average_price
        )

        # =================================================
        # FUEL STOPS
        # =================================================

        max_range = 500

        total_stops = math.ceil(

            distance_miles
            / max_range
        )

        # =================================================
        # WEATHER DEMO DATA
        # =================================================

        weather_condition = "Sunny"

        temperature = "31°C"

        # =================================================
        # FINAL RESPONSE
        # =================================================

        response_data = {

            "success": True,

            "status":
            "Route successfully generated",

            # =============================================
            # TRIP DETAILS
            # =============================================

            "trip_details": {

                "start_location":
                start,

                "end_location":
                end,

                "distance_miles":
                round(
                    distance_miles,
                    2
                ),

                "distance_km":
                round(
                    distance_km,
                    2
                ),

                "estimated_drive_time_hours":
                round(
                    duration_hours,
                    2
                )
            },

            # =============================================
            # VEHICLE DETAILS
            # =============================================

            "vehicle_details": {

                "vehicle_type":
                vehicle_name,

                "vehicle_mileage":
                mileage
            },

            # =============================================
            # FUEL DETAILS
            # =============================================

            "fuel_details": {

                "fuel_needed_liters":
                round(
                    fuel_needed_liters,
                    2
                ),

                "estimated_total_cost_usd":
                round(
                    total_cost,
                    2
                ),

                "recommended_fuel_stops":
                total_stops
            },

            # =============================================
            # WEATHER DETAILS
            # =============================================

            "weather_details": {

                "temperature":
                temperature,

                "condition":
                weather_condition
            },

            # =============================================
            # BEST FUEL STOP
            # =============================================

            "best_fuel_stop": {

                "truckstop_name":

                cheapest_stop[
                    'Truckstop Name'
                ],

                "city":
                cheapest_stop['City'],

                "state":
                cheapest_stop['State'],

                "fuel_price":

                cheapest_stop[
                    'Retail Price'
                ]
            },

            # =============================================
            # MAP DATA
            # =============================================

            "route_map_data":
            route_coordinates
        }

        return Response(
            response_data
        )