import ephem
import math
import pytz
from datetime import datetime, timedelta, date

# Constants for Vedic Astrology
SIDEREAL_YEAR = 365.256363004
AYANAMSA_RATE = 50.290966 / 3600.0 # deg/year

# Tithi Names (1-30)
TITHI_NAMES = [
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Purnima",
    "Pratipada", "Dwitiya", "Tritiya", "Chaturthi", "Panchami",
    "Shashthi", "Saptami", "Ashtami", "Navami", "Dashami",
    "Ekadashi", "Dwadashi", "Trayodashi", "Chaturdashi", "Amavasya"
]

# Nakshatra Names (1-27)
NAKSHATRA_NAMES = [
    "Ashwini", "Bharani", "Krittika", "Rohini", "Mrigashira", "Ardra",
    "Punarvasu", "Pushya", "Ashlesha", "Magha", "Purva Phalguni",
    "Uttara Phalguni", "Hasta", "Chitra", "Swati", "Vishakha", "Anuradha",
    "Jyeshtha", "Mula", "Purva Ashadha", "Uttara Ashadha", "Shravana",
    "Dhanishtha", "Shatabhisha", "Purva Bhadrapada", "Uttara Bhadrapada", "Revati"
]

# Yoga Names (1-27)
YOGA_NAMES = [
    "Vishkambha", "Priti", "Ayushman", "Saubhagya", "Sobhana",
    "Atiganda", "Sukarma", "Dhriti", "Shula", "Ganda", "Vriddhi",
    "Dhruva", "Vyaghata", "Harshana", "Vajra", "Siddhi", "Vyatipata",
    "Variyan", "Parigha", "Shiva", "Siddha", "Sadhya", "Shubha",
    "Shukla", "Brahma", "Indra", "Vaidhriti"
]

# Hindi Names
TITHI_NAMES_HI = [
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "पूर्णिमा",
    "प्रतिपदा", "द्वितीया", "तृतीया", "चतुर्थी", "पंचमी",
    "षष्ठी", "सप्तमी", "अष्टमी", "नवमी", "दशमी",
    "एकादशी", "द्वादशी", "त्रयोदशी", "चतुर्दशी", "अमावस्या"
]

NAKSHATRA_NAMES_HI = [
    "अश्विनी", "भरणी", "कृत्तिका", "रोहिणी", "मृगशिरा", "आर्द्रा",
    "पुनर्वसु", "पुष्य", "अश्लेषा", "मघा", "पूर्वा फाल्गुनी",
    "उत्तरा फाल्गुनी", "हस्त", "चित्रा", "स्वाती", "विशाखा", "अनुराधा",
    "ज्येष्ठा", "मूल", "पूर्वाषाढ़ा", "उत्तराषाढ़ा", "श्रवण",
    "धनिष्ठा", "शतभिषा", "पूर्वाभाद्रपद", "उत्तराभाद्रपद", "रेवती"
]

YOGA_NAMES_HI = [
    "विष्कम्भ", "प्रीति", "आयुष्मान", "सौभाग्य", "शोभन",
    "अतिगण्ड", "सुकर्मा", "धृति", "शूल", "गण्ड", "वृद्धि",
    "ध्रुव", "व्याघात", "हर्षण", "वज्र", "सिद्धि", "व्यतिपात",
    "वरीयान", "परिघ", "शिव", "सिद्ध", "साध्य", "शुभ",
    "शुक्ल", "ब्रह्म", "इन्द्र", "वैधृति"
]

KARAN_CYCLE_HI = ["बव", "बालव", "कौलव", "तैतिल", "गर", "वणिज", "विष्टि"]
KARAN_FIXED_HI = {1: "किस्तुघ्न", 58: "शकुनि", 59: "चतुष्पद", 60: "नाग"}


# City Data (In a real app, this should come from DB or comprehensive list)
CITIES_DB = {
    "Delhi": {"lat": "28.6139", "lon": "77.2090"},
    "Mumbai": {"lat": "19.0760", "lon": "72.8777"},
    "Kolkata": {"lat": "22.5726", "lon": "88.3639"},
    "Chennai": {"lat": "13.0827", "lon": "80.2707"},
    "Bangalore": {"lat": "12.9716", "lon": "77.5946"},
    "Hyderabad": {"lat": "17.3850", "lon": "78.4867"},
    "Ayodhya": {"lat": "26.7922", "lon": "82.1998"},
    "Varanasi": {"lat": "25.3176", "lon": "82.9739"},
    "Pune": {"lat": "18.5204", "lon": "73.8567"},
     # Add more cities as needed
}

IST = pytz.timezone("Asia/Kolkata")

class PanchangEngine:
    def __init__(self):
        pass

    def _get_ayanamsa(self, jd):
        """
        Calculate Lahiri Ayanamsa roughly for a given Julian Date.
        Base epoch J2000.0 (JD 2451545.0), Ayanamsa approx 23.85 degrees.
        Rate is about 50.29 arcseconds per year.
        """
        # Epoch J2000.0 Ayanamsa (Lahiri) ~ 23 deg 51 min 25.5 sec = 23.857 degrees
        # Simple linear approximation is sufficient for general panchang
        # A more complex model is available in Swisseph but we use python-native logic here.
        # Days since J2000.0
        T = (jd - 2451545.0) / 36525.0
        ayanamsa = 23.8585 + 1.396 * T 
        return ayanamsa

    def _normalize_deg(self, deg):
        return deg % 360

    def _get_observer(self, date_obj, lat, lon):
        obs = ephem.Observer()
        obs.lat = lat
        obs.lon = lon
        obs.date = date_obj # UTC
        obs.elevation = 0
        return obs
    
    def _to_ist_display(self, utc_dt):
        if not utc_dt: return None
        return pytz.utc.localize(utc_dt).astimezone(IST).strftime("%H:%M")
    
    def _get_day_properties(self, date_str, lat, lon):
        """
        Calculate sunrise, sunset, moonrise, day duration.
        """
        obs = ephem.Observer()
        obs.lat = lat
        obs.lon = lon
        date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
        obs.date = date_obj # Midnight of that day UTC
        
        sun = ephem.Sun()
        moon = ephem.Moon()
        
        try:
            sunrise_utc = obs.next_rising(sun).datetime()
            sunset_utc = obs.next_setting(sun).datetime()
            moonrise_utc = obs.next_rising(moon).datetime()
            moonset_utc = obs.next_setting(moon).datetime()
        except ephem.AlwaysUpError:
             # Polar regions or weird edge case
             sunrise_utc = None
             sunset_utc = None
             moonrise_utc = None
        except ephem.AlwaysDownError:
             sunrise_utc = None
             sunset_utc = None
             moonrise_utc = None
             
        # Calculate day duration
        day_duration_mins = 0
        if sunrise_utc and sunset_utc:
            diff = sunset_utc - sunrise_utc
            day_duration_mins = diff.total_seconds() / 60.0
            
        return {
            "sunrise_utc": sunrise_utc,
            "sunset_utc": sunset_utc,
            "moonrise_utc": moonrise_utc,
            "moonset_utc": moonset_utc,
            "day_duration_mins": day_duration_mins
        }

    def calculate_panchang(self, date_str: str, city_name: str):
        """
        Calculate daily Panchang details.
        """
        city_data = CITIES_DB.get(city_name, CITIES_DB["Delhi"])
        lat = city_data["lat"]
        lon = city_data["lon"]
        
        props = self._get_day_properties(date_str, lat, lon)
        sunrise_utc = props["sunrise_utc"]
        
        # Calculate Tithi, Nakshatra, Yoga at Sunrise time (Standard Panchang rule)
        # If Sunrise is None (unlikely for India), fallback to 6 AM IST
        if not sunrise_utc:
             # Fallback
             dt = datetime.strptime(date_str, "%Y-%m-%d")
             sunrise_utc = dt - timedelta(hours=5, minutes=30) + timedelta(hours=6) # 00:30 UTC
             
        # Create observer at Sunrise
        obs = ephem.Observer()
        obs.lat = lat
        obs.lon = lon
        obs.date = sunrise_utc
        
        sun = ephem.Sun()
        moon = ephem.Moon()
        sun.compute(obs)
        moon.compute(obs)
        
        # Ecliptic longitudes
        sun_lon = math.degrees(ephem.Ecliptic(sun).lon)
        moon_lon = math.degrees(ephem.Ecliptic(moon).lon)
        
        # Ayanamsa
        jd = ephem.julian_date(sunrise_utc)
        ayanamsa = self._get_ayanamsa(jd)
        
        sidereal_sun = self._normalize_deg(sun_lon - ayanamsa)
        sidereal_moon = self._normalize_deg(moon_lon - ayanamsa)
        
        # Tithi
        # Span of Tithi = 12 deg.
        # Tithi = (Moon_Lon - Sun_Lon) / 12
        diff = self._normalize_deg(moon_lon - sun_lon)
        tithi_idx = int(diff / 12.0)
        tithi_name = TITHI_NAMES[tithi_idx % 30]
        tithi_val = tithi_idx / 30.0 # Normalized 0-1
        
        # Paksha
        paksha = "Shukla" if tithi_idx < 15 else "Krishna"
        
        # Nakshatra
        # Span of Nakshatra = 13 deg 20 min = 13.333 deg
        nak_span = 360.0 / 27.0
        nak_idx = int(sidereal_moon / nak_span)
        nakshatra_name = NAKSHATRA_NAMES[nak_idx % 27]
        
        # Yoga
        # Yoga = (Sun_Lon + Moon_Lon) / 13.333
        yoga_sum = self._normalize_deg(sidereal_sun + sidereal_moon)
        yoga_idx = int(yoga_sum / nak_span)
        yoga_name = YOGA_NAMES[yoga_idx % 27]
        
        # Karan
        # Karan = Tithi / 2 (6 deg spans)
        # But Karan calculation is complex as it changes every half-tithi
        karan_idx_calc = int(diff / 6.0)
        # 1st Karan is Kinstughna (unique)
        # Then Bava to Vishti cycle 8 times
        # Then Shakuni, Chatushpada, Naga, Kimstughna
        # Simplified Karan name map for now:
        karan_num = karan_idx_calc + 1
        if karan_num == 1: 
             karan_name = "Kimstughna"
             karan_name_hi = "किस्तुघ्न"
        elif karan_num > 57:
             if karan_num == 58: 
                  karan_name = "Shakuni"
                  karan_name_hi = "शकुनि"
             elif karan_num == 59: 
                  karan_name = "Chatushpada"
                  karan_name_hi = "चतुष्पद"
             elif karan_num == 60: 
                  karan_name = "Naga"
                  karan_name_hi = "नाग"
             else: 
                  karan_name = "Kimstughna"
                  karan_name_hi = "किस्तुघ्न"
        else:
             karan_cycle = ["Bava", "Balava", "Kaulava", "Taitila", "Gara", "Vanija", "Vishti"]
             karan_name = karan_cycle[(karan_num - 2) % 7]
             karan_name_hi = KARAN_CYCLE_HI[(karan_num - 2) % 7]

        # Rahu Kaal, Yamaganda, Gulika (Fixed slots based on Weekday)
        # A nicer implementation divides day/night into 8 parts (ashta bhagas)
        # But standard "fixed slot" mappings are widely accepted for general use.
        # Using the standard mapping logic from previous file as it's sufficient.
        dt_date = datetime.strptime(date_str, "%Y-%m-%d")
        weekday = dt_date.weekday()
        
        # Mapping slots roughly (could be improved by scaling to actual sunrise-sunset)
        # For meaningfulness, we scale standard slots to actual sunrise-sunset
        sunrise_dt_utc = props["sunrise_utc"]
        sunset_dt_utc = props["sunset_utc"]
        day_len_mins = props["day_duration_mins"]
        
        # 8 parts of the day
        one_eigth = day_len_mins / 8.0 # mins per part
        
        # Rahu period indices (0-7, sunrise to sunset)
        # Mon: 2nd part (1-2), Tue: 7th (6-7)...
        rahu_indices = {0: 1, 1: 6, 2: 4, 3: 5, 4: 3, 5: 2, 6: 7} # Mon=0
        yama_indices = {0: 3, 1: 2, 2: 1, 3: 0, 4: 5, 5: 4, 6: 6}
        guli_indices = {0: 5, 1: 4, 2: 3, 3: 2, 4: 1, 5: 0, 6: 6} # Sat Gulika is 1st part usually? Confirming... Sat Gulika is often cited as 6:00-7:30.
        # Standard chart:
        # Day | Rahu | Yama | Gulika
        # Mon | 7:30-9 | 10:30-12 | 1:30-3
        # Tue | 3-4:30 | 9-10:30 | 12-1:30
        # Wed | 12-1:30 | 7:30-9 | 10:30-12
        # Thu | 1:30-3 | 6-7:30 | 9-10:30
        # Fri | 10:30-12 | 3-4:30 | 7:30-9 
        # Sat | 9-10:30 | 1:30-3 | 6-7:30
        # Sun | 4:30-6 | 12-1:30 | 3-4:30
        
        # Indices (1-8 based on 1.5h chunks roughly from 6am)
        # Mon(0): Rahu(2nd, 7:30), Yama(4th, 10:30), Guli(6th, 1:30) -- check indices
        # Let's use simple logic:
        # Rahu: Mon(1), Tue(6), Wed(4), Thu(5), Fri(3), Sat(2), Sun(7) [Using 0-7 index where 0 is 6am-7:30am]
        
        def get_time_slot(idx_start):
            # Start time = Sunrise + idx_start * one_eigth
            # End time = Start + one_eigth
            if not sunrise_dt_utc: return "Unknown"
            
            s_min = idx_start * one_eigth
            e_min = (idx_start + 1) * one_eigth
            
            s_dt = sunrise_dt_utc + timedelta(minutes=s_min)
            e_dt = sunrise_dt_utc + timedelta(minutes=e_min)
            
            return f"{self._to_ist_display(s_dt)}-{self._to_ist_display(e_dt)}"

        rahukaal = get_time_slot(rahu_indices.get(weekday, 0))
        yamaganda = get_time_slot(yama_indices.get(weekday, 0))
        gulika = get_time_slot(guli_indices.get(weekday, 0))

        # Dictionary for simple festival/vrat lookups based on Tithi/Paksha
        festival_name = None
        vrat_name = None
        
        # Simple Logic for common Tithis
        if tithi_name == "Ekadashi":
            vrat_name = "Ekadashi"
        elif tithi_name == "Purnima":
            festival_name = "Purnima"
            vrat_name = "Purnima Vrat"
        elif tithi_name == "Amavasya":
            festival_name = "Amavasya"
            vrat_name = "Amavasya"
        elif tithi_name == "Chaturthi":
            if paksha == "Krishna":
                vrat_name = "Sankashti Chaturthi"
            else:
                vrat_name = "Vinayaka Chaturthi"
        elif tithi_name == "Trayodashi":
             vrat_name = "Pradosh Vrat"
        elif tithi_name == "Ashtami":
             if paksha == "Krishna":
                 # Kalashtami
                 pass
             else:
                 vrat_name = "Durga Ashtami"

        # Festivals list (JSONB)
        festivals_list = []
        if festival_name:
            festivals_list.append(festival_name)
        if vrat_name and vrat_name != festival_name:
             festivals_list.append(vrat_name)

        return {
            "date": date_str,
            "city": city_name,
            "sunrise": self._to_ist_display(props["sunrise_utc"]),
            "sunset": self._to_ist_display(props["sunset_utc"]),
            "moonrise": self._to_ist_display(props["moonrise_utc"]),
            "moonset": self._to_ist_display(props["moonset_utc"]),
            "day_duration": f"{int(props['day_duration_mins'] // 60)}h {int(props['day_duration_mins'] % 60)}m",
            "tithi": tithi_name,
            "tithi_hindi": TITHI_NAMES_HI[tithi_idx % 30],
            "tithi_index": tithi_idx % 30, # Useful for filtering logic
            "paksha": paksha,
            "nakshatra": nakshatra_name,
            "nakshatra_hindi": NAKSHATRA_NAMES_HI[nak_idx % 27],
            "yoga": yoga_name,
            "yoga_hindi": YOGA_NAMES_HI[yoga_idx % 27],
            "karan": karan_name,
            "karan_hindi": karan_name_hi,
            "rahukaal": rahukaal,
            "yamaganda": yamaganda,
            "gulika": gulika,
            "festival": festival_name,
            "vrat": vrat_name,
            "festivals": festivals_list, # For JSONB column
            "status": "complete",
            "hindi_description": None, # Placeholder for now
            "english_description": None, # Placeholder for now
            "spiritual_message": None # Placeholder for now
        }

    def calculate_muhurats(self, date_str, city_name):
        """
        Calculate auspicious daily muhurats.
        Abhijit, Brahma, Godhuli, Amrit Kaal.
        """
        city_data = CITIES_DB.get(city_name, CITIES_DB["Delhi"])
        lat = city_data["lat"]
        lon = city_data["lon"]
        
        props = self._get_day_properties(date_str, lat, lon)
        sunrise_utc = props["sunrise_utc"]
        sunset_utc = props["sunset_utc"]
        day_mins = props["day_duration_mins"]
        
        if not sunrise_utc or not sunset_utc:
            return []
            
        muhurats = []
        
        # 1. Abhijit Muhurat
        # Ideally 8th Muhurat of the day (out of 15).
        # Midday.
        # Exact calculation: divide day into 15 parts. Take 8th part.
        # Check weekday. Skip on Wednesday? No, strict definition usually says avoid on Wednesday, but it exists.
        # We will list it and handle avoidance in business logic if needed.
        
        part_duration = day_mins / 15.0
        abhijit_start_mins = 7 * part_duration # Start of 8th part (index 7)
        abhijit_end_mins = 8 * part_duration
        
        abh_start = sunrise_utc + timedelta(minutes=abhijit_start_mins)
        abh_end = sunrise_utc + timedelta(minutes=abhijit_end_mins)
        
        # Skip Abhijit on Wednesday (Weekday = 2) for "Auspiciousness"? 
        # Usually it is considered bad on Wednesday. Let's mark it.
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        week_d = dt.weekday()
        
        score_abh = 4.5
        reason_abh = "Excellent for most auspicious activities. Midday power."
        if week_d == 2: # Wednesday
             score_abh = 2.0
             reason_abh = "Abhijit is generally avoided on Wednesdays."
             
        muhurats.append({
            "type": "Abhijit",
            "start_time": self._to_ist_display(abh_start),
            "end_time": self._to_ist_display(abh_end),
            "score": score_abh,
            "reasoning": reason_abh,
             "date": date_str,
             "city": city_name
        })
        
        # 2. Brahma Muhurat
        # 2 Muhurats (48x2 = 96 mins) before Sunrise.
        # Strictly speaking, it starts 2 muhurats before sunrise and ends 1 muhurat before.
        # Usually 4:24 AM to 5:12 AM roughly.
        # Let's calculate: 96 mins before Sunrise to 48 mins before Sunrise.
        brahma_start = sunrise_utc - timedelta(minutes=96)
        brahma_end = sunrise_utc - timedelta(minutes=48)
        
        muhurats.append({
            "type": "Brahma",
            "start_time": self._to_ist_display(brahma_start),
            "end_time": self._to_ist_display(brahma_end),
            "score": 5.0,
            "reasoning": "Best for meditation, learning, and spiritual practices.",
             "date": date_str,
             "city": city_name
        })
        
        # 3. Godhuli Muhurat
        # 12 mins before and after Sunset. Or 1 Muhurat centered on Sunset.
        # Let's take 12 mins before and 12 mins after Sunset.
        godhuli_start = sunset_utc - timedelta(minutes=12)
        godhuli_end = sunset_utc + timedelta(minutes=12)
        
        muhurats.append({
            "type": "Godhuli",
            "start_time": self._to_ist_display(godhuli_start),
            "end_time": self._to_ist_display(godhuli_end),
            "score": 4.0,
            "reasoning": "Auspicious for cattle, weddings, and evening prayers.",
             "date": date_str,
             "city": city_name
        })
        
        return muhurats
