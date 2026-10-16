import os

import requests
from CoreLocation import CLLocationManager, kCLLocationAccuracyBest
from Foundation import NSDate, NSObject, NSRunLoop


class LocationDelegate(NSObject):
    def init(self):
        self = super().init()
        if self is None:
            return None
        self.location = None
        self.error = None
        self.manager = None
        return self

    def locationManagerDidChangeAuthorization_(self, manager):
        status = manager.authorizationStatus()
        if status in (3, 4):  # Authorized when in use or always
            manager.requestLocation()
        elif status == 2:  # Denied
            self.error = "Location access was denied. Enable it in macOS System Settings."
        elif status == 1:  # Restricted
            self.error = "Location access is restricted on this device."

    def locationManager_didUpdateLocations_(self, manager, locations):
        if locations:
            self.location = locations[-1]
        else:
            self.error = "macOS did not return a location."

    def locationManager_didFailWithError_(self, manager, error):
        self.error = str(error)


def get_device_location(timeout=30):
    delegate = LocationDelegate.alloc().init()
    manager = CLLocationManager.alloc().init()
    delegate.manager = manager
    manager.setDelegate_(delegate)
    manager.setDesiredAccuracy_(kCLLocationAccuracyBest)
    manager.requestWhenInUseAuthorization()

    deadline = NSDate.dateWithTimeIntervalSinceNow_(timeout)
    run_loop = NSRunLoop.currentRunLoop()

    while delegate.location is None and delegate.error is None:
        if deadline.timeIntervalSinceNow() <= 0:
            raise TimeoutError("Timed out waiting for device location.")
        run_loop.runUntilDate_(NSDate.dateWithTimeIntervalSinceNow_(0.2))

    if delegate.error:
        raise RuntimeError(delegate.error)

    coordinate = delegate.location.coordinate()
    return coordinate.latitude, coordinate.longitude


def get_google_weather_forecast(api_key, latitude, longitude, days=3):
    url = "https://weather.googleapis.com/v1/forecast/days:lookup"
    params = {
        "key": api_key,
        "location.latitude": latitude,
        "location.longitude": longitude,
        "languageCode": "en-US",
        "unitsSystem": "METRIC",
        "days": days,
    }

    try:
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as error:
        print(f"Error fetching data from Google Weather API: {error}")
        return None


if __name__ == "__main__":
    API_KEY = os.environ.get("GOOGLE_WEATHER_API_KEY")
    if not API_KEY:
        raise SystemExit("Set the GOOGLE_WEATHER_API_KEY environment variable first.")

    try:
        latitude, longitude = get_device_location()
        print(f"Device location: {latitude:.5f}, {longitude:.5f}")
    except (RuntimeError, TimeoutError) as error:
        raise SystemExit(f"Could not get device location: {error}")

    weather_data = get_google_weather_forecast(API_KEY, latitude, longitude)
    if weather_data:
        print("Successfully retrieved weather data!")
        print(weather_data)
