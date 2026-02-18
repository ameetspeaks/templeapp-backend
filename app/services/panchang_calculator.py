import ephem
import math
from datetime import datetime
import pytz

# Constants
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami", "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami", "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra", "Punarvasu", "Pushya", "Ashlesha",
    "Magha", "Purva Phalguni", "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha", "Jyeshtha",
    "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana", "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Sobhana", "Atiganda", "Sukarma", "Dhriti", "Shula",
    "Ganda", "Vriddhi", "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata", "Variyan",
    "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha", "Shukla", "Brahma", "Indra", "Vaidhriti"
]

KARAN_NAMES = [
    "Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti", "Shakuni", "Chatushpada", "Naga", "Kimstughna"
]

CITIES = {
    "Delhi": {"lat": "28.6139", "lon": "77.2090"},
    "Mumbai": {"lat": "19.0760", "lon": "72.8777"},
    "Kolkata": {"lat": "22.5726", "lon": "88.3639"},
    "Chennai": {"lat": "13.0827", "lon": "80.2707"},
    "Bangalore": {"lat": "12.9716", "lon": "77.5946"},
    "Hyderabad": {"lat": "17.3850", "lon": "78.4867"},
    "Ahmedabad": {"lat": "23.0225", "lon": "72.5714"},
    "Pune": {"lat": "18.5204", "lon": "73.8567"},
    "Jaipur": {"lat": "26.9124", "lon": "75.7873"},
    "Lucknow": {"lat": "26.8467", "lon": "80.9462"},
    "Varanasi": {"lat": "25.3176", "lon": "82.9739"},
    "Ayodhya": {"lat": "26.7922", "lon": "82.1998"},
    "Mathura": {"lat": "27.4924", "lon": "77.6737"},
    "Haridwar": {"lat": "29.9457", "lon": "78.1642"},
    "Rishikesh": {"lat": "30.0869", "lon": "78.2676"},
    "Ujjain": {"lat": "23.1765", "lon": "75.7885"},
    "Nashik": {"lat": "19.9975", "lon": "73.7898"},
    "Prayagraj": {"lat": "25.4358", "lon": "81.8463"},
    "Bhubaneswar": {"lat": "20.2961", "lon": "85.8245"},
    "Guwahati": {"lat": "26.1445", "lon": "91.7362"}
}

class PanchangCalculator:
    def calculate(self, date_str: str, city_name: str) -> dict:
        city_data = CITIES.get(city_name, CITIES["Delhi"])
        lat = city_data["lat"]
        lon = city_data["lon"]
        
        # Date processing
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        # Ephem setup
        observer = ephem.Observer()
        observer.lat = lat
        observer.lon = lon
        # Ephem date at midnight UTC usually
        # But for panchang we often check sunrise time properties
        # For simplicity, calculating at 6 AM IST roughly or just use UTC midnight of that day
        observer.date = date_str 
        
        # Sun and Moon
        sun = ephem.Sun()
        moon = ephem.Moon()
        
        sun.compute(observer)
        moon.compute(observer)
        
        # Sunrise/Sunset (IST)
        # Using next_rising from the observer date (which defaults to midnight UTC)
        # Note: next_rising might return previous day or next day depending on time
        # We assume observer.date is 00:00 UTC. Sunrise in India is around 00:00-01:30 UTC
        try:
            sunrise_utc = observer.next_rising(sun).datetime()
            sunset_utc = observer.next_setting(sun).datetime()
            moonrise_utc = observer.next_rising(moon).datetime()
        except:
            sunrise_utc = datetime.utcnow()
            sunset_utc = datetime.utcnow()
            moonrise_utc = datetime.utcnow()

        ist = pytz.timezone("Asia/Kolkata")
        
        def to_ist_str(dt_utc):
            return pytz.utc.localize(dt_utc).astimezone(ist).strftime("%H:%M")
            
        sunrise_ist = to_ist_str(sunrise_utc)
        sunset_ist = to_ist_str(sunset_utc)
        moonrise_ist = to_ist_str(moonrise_utc)

        # Longitude in degrees (Geocentric Ecliptic)
        sun_ecl = ephem.Ecliptic(sun)
        moon_ecl = ephem.Ecliptic(moon)
        sun_lon = math.degrees(sun_ecl.lon)
        moon_lon = math.degrees(moon_ecl.lon)
        
        # Normalize to 0-360
        if sun_lon < 0: sun_lon += 360
        if moon_lon < 0: moon_lon += 360
        
        # Tithi
        diff = moon_lon - sun_lon
        if diff < 0: diff += 360
        
        tithi_index = int(diff / 12.0)
        tithi_name = TITHI_NAMES[tithi_index % 30]
        tithi_index_val = tithi_index % 30
        
        # Paksha
        paksha = "Shukla" if tithi_index < 15 else "Krishna"
        
        # Nakshatra
        # Ayanamsa correction (Lahiri approx 24 deg)
        ayanamsa = 24.0
        sidereal_moon_lon = (moon_lon - ayanamsa) % 360
        sidereal_sun_lon = (sun_lon - ayanamsa) % 360
        
        nakshatra_index = int(sidereal_moon_lon / (360/27))
        nakshatra_name = NAKSHATRA_NAMES[nakshatra_index % 27]
        
        # Yoga
        yoga_sum = (sidereal_sun_lon + sidereal_moon_lon) % 360
        yoga_index = int(yoga_sum / (360/27))
        yoga_name = YOGA_NAMES[yoga_index % 27]
        
        # Karan
        karan_calc = diff / 6.0 # 0-60
        karan_num = int(karan_calc)
        if karan_num == 0:
            karan_name = "Kimstughna"
        elif karan_num >= 57:
            if karan_num == 57: karan_name = "Shakuni"
            elif karan_num == 58: karan_name = "Chatushpada"
            else: karan_name = "Naga"
        else:
            karan_name = KARAN_NAMES[(karan_num - 1) % 7] # Cycle Bava to Vishti 0-6

        # Rahukaal (Simplified fixed slots)
        weekday = date_obj.weekday() # Mon=0, Sun=6
        rahukaal_map = {
            0: "07:30-09:00", 1: "15:00-16:30", 2: "12:00-13:30", 3: "13:30-15:00",
            4: "10:30-12:00", 5: "09:00-10:30", 6: "16:30-18:00"
        }
        rahukaal = rahukaal_map.get(weekday, "Unknown")
        
        # Yamaganda
        yamaganda_map = {
             0: "10:30-12:00", 1: "09:00-10:30", 2: "07:30-09:00", 3: "06:00-07:30",
             4: "15:00-16:30", 5: "13:30-15:00", 6: "12:00-13:30"
        }
        yamaganda = yamaganda_map.get(weekday, "Unknown")
        
        # Gulika
        gulika_map = {
             0: "13:30-15:00", 1: "12:00-13:30", 2: "10:30-12:00", 3: "09:00-10:30",
             4: "07:30-09:00", 5: "06:00-07:30", 6: "15:00-16:30"
        }
        gulika = gulika_map.get(weekday, "Unknown")

        return {
            "date": date_str,
            "city": city_name,
            "sunrise": sunrise_ist,
            "sunset": sunset_ist,
            "moonrise": moonrise_ist,
            "tithi": tithi_name,
            "tithi_index": tithi_index_val,
            "paksha": paksha,
            "nakshatra": nakshatra_name,
            "yoga": yoga_name,
            "karan": karan_name,
            "rahukaal": rahukaal,
            "yamaganda": yamaganda,
            "gulika": gulika
        }
