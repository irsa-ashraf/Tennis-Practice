'''
Pydantic models for the API endpoints
'''

from pydantic import BaseModel, Field
from typing import List, Optional


class GeocodeReq(BaseModel):
    '''
    Request model for geocoding an address.

    Attributes:
        address (str): The address to be geocoded. 
                       Must be at least 3 characters long.

    Example:
        {
            "address": "123 Main Street, New York, NY"
        }
    '''

    address: str = Field(..., min_length=3)


class GeocodeResp(BaseModel):
    '''
    Response model for geocoding results.

    Attributes:
        lat (float): Latitude of the geocoded address.
        lon (float): Longitude of the geocoded address.
        display_name (str): A human-readable description of the location.

    Example:
        {
            "lat": 40.7128,
            "lon": -74.0060,
            "display_name": "New York, NY, USA"
        }
    '''

    lat: float
    lon: float
    display_name: str


class ReverseReq(BaseModel):
    '''
    Request model for reverse geocoding coordinates.

    Attributes:
        lat (float): Latitude of the location.
        lon (float): Longitude of the location.

    Example:
        {
            "lat": 40.7128,
            "lon": -74.0060
        }
    '''

    lat: float
    lon: float


class Court(BaseModel):
    '''
    Model representing a court's information.

    Attributes:
        court_id (int): Unique identifier for the court.
        name (str): Name of the court.
        borough (Optional[str]): Borough where the court is located. Defaults to an empty string.
        lat (float): Latitude of the court location.
        lon (float): Longitude of the court location.
        distance_km (Optional[float]): Distance from a given point in kilometers. Defaults to None.
        sport (Optional[str]): Sport type (e.g., "handball", "tennis").

    Example:
        {
            "court_id": 101,
            "name": "Tompkins Square Park Court",
            "borough": "Manhattan",
            "lat": 40.7265,
            "lon": -73.9815,
            "distance_km": 2.3,
            "sport": "handball"
        }
    '''

    Court_Id: Optional[str] = None
    Name: Optional[str] = ""
    Borough: Optional[str] = ""
    Lat: Optional[float] = None
    Lon: Optional[float] = None
    Num_Of_Courts: Optional[int] = None
    Location: Optional[str] = ""
    Distance_Km: Optional[float] = None
    Sport: Optional[str] = None


class NearestResp(BaseModel):
    '''
    Response model for the nearest courts search.

    Attributes:
        count (int): Number of courts found in the search.
        results (List[Court]): List of Court objects representing the nearest courts.

    Example:
        {
            "count": 2,
            "results": [
                {
                    "court_id": 101,
                    "name": "Tompkins Square Park Court",
                    "borough": "Manhattan",
                    "lat": 40.7265,
                    "lon": -73.9815,
                    "distance_km": 2.3
                },
                {
                    "court_id": 205,
                    "name": "Hamilton Fish Park Court",
                    "borough": "Manhattan",
                    "lat": 40.7180,
                    "lon": -73.9830,
                    "distance_km": 3.1
                }
            ]
        }
    '''
    
    count: int
    results: List[Court]


class AgentRequest(BaseModel):
    '''
    Request model for AI agent queries.

    Attributes:
        query (str): The user's query for the AI agent.

    Example:
        {
            "query": "Find the best tennis courts in Brooklyn."
        }
    '''

    query: Optional[str] = Field(..., min_length=2)

