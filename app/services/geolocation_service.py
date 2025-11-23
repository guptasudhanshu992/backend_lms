import logging
from typing import Optional, Dict
import httpx
from functools import lru_cache

logger = logging.getLogger(__name__)


class GeolocationService:
    """Service for IP geolocation lookups"""
    
    def __init__(self):
        # Using ipapi.co as it provides a free tier without API key
        # For production, consider using MaxMind GeoIP2 or ipgeolocation.io
        self.api_url = "https://ipapi.co/{ip}/json/"
        self.timeout = 2.0  # Quick timeout to not slow down requests
        
    @lru_cache(maxsize=1000)
    async def get_location(self, ip_address: str) -> Optional[Dict]:
        """
        Get geolocation data for an IP address
        
        Returns dict with: city, region, country, country_code, latitude, longitude
        """
        # Skip private/local IPs
        if self._is_private_ip(ip_address):
            return {
                "city": "Local",
                "region": "Local",
                "country": "Local",
                "country_code": "LC",
                "latitude": 0.0,
                "longitude": 0.0,
            }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(self.api_url.format(ip=ip_address))
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Check for API error
                    if "error" in data:
                        logger.warning(f"Geolocation API error for {ip_address}: {data.get('reason')}")
                        return None
                    
                    return {
                        "city": data.get("city"),
                        "region": data.get("region"),
                        "country": data.get("country_name"),
                        "country_code": data.get("country_code"),
                        "latitude": data.get("latitude"),
                        "longitude": data.get("longitude"),
                    }
                else:
                    logger.debug(f"Geolocation lookup failed for {ip_address}: {response.status_code}")
                    return None
                    
        except httpx.TimeoutException:
            logger.debug(f"Geolocation lookup timeout for {ip_address}")
            return None
        except Exception as e:
            logger.debug(f"Geolocation lookup error for {ip_address}: {e}")
            return None
    
    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP is private/local"""
        private_ranges = [
            "127.",
            "10.",
            "192.168.",
            "172.16.",
            "172.17.",
            "172.18.",
            "172.19.",
            "172.20.",
            "172.21.",
            "172.22.",
            "172.23.",
            "172.24.",
            "172.25.",
            "172.26.",
            "172.27.",
            "172.28.",
            "172.29.",
            "172.30.",
            "172.31.",
            "localhost",
            "::1",
            "fe80:",
        ]
        return any(ip.startswith(prefix) for prefix in private_ranges)


# Alternative implementation using MaxMind GeoIP2 (requires database file)
class MaxMindGeolocationService:
    """
    Alternative geolocation service using MaxMind GeoIP2 database
    Requires: pip install geoip2
    Download database from: https://dev.maxmind.com/geoip/geolite2-free-geolocation-data
    """
    
    def __init__(self, database_path: str = "GeoLite2-City.mmdb"):
        try:
            import geoip2.database
            self.reader = geoip2.database.Reader(database_path)
        except Exception as e:
            logger.warning(f"Failed to initialize MaxMind database: {e}")
            self.reader = None
    
    async def get_location(self, ip_address: str) -> Optional[Dict]:
        """Get geolocation using MaxMind database"""
        if not self.reader:
            return None
            
        try:
            response = self.reader.city(ip_address)
            
            return {
                "city": response.city.name,
                "region": response.subdivisions.most_specific.name if response.subdivisions else None,
                "country": response.country.name,
                "country_code": response.country.iso_code,
                "latitude": response.location.latitude,
                "longitude": response.location.longitude,
            }
        except Exception as e:
            logger.debug(f"MaxMind lookup error for {ip_address}: {e}")
            return None
    
    def close(self):
        """Close the database reader"""
        if self.reader:
            self.reader.close()
