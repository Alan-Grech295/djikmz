from pydantic import Field, model_serializer
from enum import Enum
import xmltodict
from .utils import WpmlModel

class StrEnum(str, Enum):
    """Base class for string enums."""
    def __str__(self):
        return self.value
    
class CoordinateModeEnum(StrEnum):
    WGS84 = "WGS84"
    
class HeightModeEnum(StrEnum):
    # EGM96 = "EGM96"
    WGS84 = "WGS84"
    RELATIVE = "relativeToStartPoint"
    AGL = "aboveGroundLevel"
    REAL_TIME_FOLLOW_SURFACE = "realTimeFollowSurface" # only supported by M3x

class PositionTypeEnum(StrEnum):
    GPS = "GPS"
    RTK = "RTKBaseStation"
    QIANXUN = "QianXun"
    CUSTOM = "Custom"


class CoordinateSystemParam(WpmlModel):
    "Coordinate system parameters for the waypoints"
    coordinate_system: CoordinateModeEnum = Field(
        default=CoordinateModeEnum.WGS84,
        serialization_alias="coordinateMode",
        description="Coordinate system used for the mission. Default is WGS84 (and the only support).")
    height_mode: HeightModeEnum = Field(
        default=HeightModeEnum.RELATIVE,
        serialization_alias="heightMode",
        description="Height mode used for the mission.")
    position_type: PositionTypeEnum = Field(
        default=PositionTypeEnum.GPS,
        serialization_alias="positioningType")
    # TODO: the following attributes are for mapping missions. Since we are focusing on
    # waypoint missions right now, they are not supported yet.
    # globalShootHeight         float           m used to calc photo spacing and GSD
    # surfaceFollowModeEnable   bool            enable surface follow mode 0 disabled, 1 enabled
    # surfaceRelativeHeight     float           m relative height to the surface

    def to_dict(self) -> dict:
        return self.to_wpml_dict()

    @classmethod
    def from_dict(cls, data: dict) -> 'CoordinateSystemParam':
        return cls(**cls._from_wpml_dict(data))
    
    def to_xml(self) -> str:
        """Convert the CoordinateSystemParam to XML format."""
        xml_dict = self.to_dict()
        return xmltodict.unparse(xml_dict, pretty=True, full_document=False)
    
    @classmethod
    def from_xml(cls, xml_data: str) -> 'CoordinateSystemParam':
        """Create a CoordinateSystemParam instance from XML data."""
        try:
            data = xmltodict.parse(xml_data)
            coord_data = data.get("wpml:coordinateSystemParam", data)
        except:
            raise ValueError("Invalid XML format for coordinate system parameter")
        
        return cls.from_dict(coord_data)
    
    @model_serializer
    def serialize(self) -> dict:
        """Serialize the CoordinateSystemParam to a dictionary."""
        return self.to_dict()



