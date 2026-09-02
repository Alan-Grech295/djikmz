from pydantic import Field
from .mission_config import MissionConfig
from .coordinate_system_param import CoordinateSystemParam
from datetime import datetime
from .heading_param import WaypointHeadingParam
from .turn_param import WaypointTurnMode
from .waypoint import Waypoint
from .utils import WpmlModel
from enum import Enum
import xmltodict

WPML_NAMESPACE = "http://www.dji.com/wpmz/1.0.2"

ATTR_NOT_IN_FOLDER = [
    "wpml:author",
    "wpml:createTime",
    "wpml:updateTime",
    "wpml:missionConfig",
    "wpml:waylineId",
    "wpml:autoFlightSpeed",
    "wpml:executeHeightMode",
]

TEMPLATE_ROOT_ATTRS = [
    "wpml:author",
    "wpml:createTime",
    "wpml:updateTime",
    "wpml:missionConfig",
]

TEMPLATE_FOLDER_ATTRS = [
    "wpml:templateType",
    "wpml:templateId",
    "wpml:waylineCoordinateSysParam",
    "wpml:autoFlightSpeed",
    "wpml:gimbalPitchMode",
    "wpml:globalHeight",
    "wpml:globalRTHHeight",
    "wpml:globalWaypointHeadingParam",
    "wpml:globalWaypointTurnMode",
    "wpml:globalUseStraightLine",
]

WAYLINES_FOLDER_ATTRS = [
    "wpml:templateId",
    "wpml:executeHeightMode",
    "wpml:waylineId",
]

class StrEnum(str, Enum):
    """Base class for string enums."""
    def __str__(self):
        return self.value


class GimbalPitchMode(StrEnum):
    """Enumeration of gimbal pitch modes."""
    MANUAL = "manual"
    POINT_SETTING = "usePointSetting"


class ExecuteHeightMode(StrEnum):
    """Height modes accepted by DJI specifically in waylines.wpml."""

    WGS84 = "WGS84"
    RELATIVE = "relativeToStartPoint"
    REAL_TIME_FOLLOW_SURFACE = "realTimeFollowSurface"


class KML(WpmlModel):
    author: str = Field(
        default="Zey",
        description="Author of the KML file."
    )
    create_time: int = Field(
        default=int(datetime.now().timestamp()*1e3),
        serialization_alias="createTime",
        description="Creation time of the KML file in milliseconds since epoch."
    )
    update_time: int = Field(
        default=int(datetime.now().timestamp()*1e3),
        serialization_alias="updateTime",
        description="Last update time of the KML file in milliseconds since epoch."
    )
    mission_config: MissionConfig = Field(
        default_factory=MissionConfig,
        serialization_alias="missionConfig",
        description="Mission configuration parameters."
    )
    # Those field should under Folder in xml, but we put them here for simplicity since they are also configs.
    template_type: str = Field(
        default="waypoint",
        serialization_alias="templateType",
        description="Type of the KML template, must be 'waypoint' for now",
        pattern="^waypoint$"
    )
    template_id: int = Field(
        default=0,
        serialization_alias="templateId",
        description="ID of the KML template, must be 0 for now",
        ge=0, le=0
    )
    wayline_id: int = Field(
        default=0,
        serialization_alias="waylineId",
        description="Waylines ID. Note: The ID is unique within a kmz file. It is recommended to increment it monotonically and continuously from 0.",
        ge=0, le=65535
    )
    auto_flight_speed: float = Field(
        default=0,
        serialization_alias="autoFlightSpeed",
        description="Global waylines flight speed",
        ge=0
    )
    execute_height_mode: ExecuteHeightMode = Field(
        default=ExecuteHeightMode.WGS84,
        serialization_alias="executeHeightMode",
        description="Execute height mode",
    )
    coordinate_system_param: CoordinateSystemParam = Field(
        default_factory=CoordinateSystemParam,
        serialization_alias="waylineCoordinateSysParam",
        description="Coordinate system parameters for the waypoints."
    )
    global_speed: float = Field(
        default=1.0,
        serialization_alias="autoFlightSpeed",
        description="Global flight speed in m/s.",
        gt=0.0)
    global_height: float = Field(
        default=0.0,
        serialization_alias="globalHeight",
        description="Global height of the waypoints in meters.",
        ge=0.0
    )
    global_waypoint_heading_param: WaypointHeadingParam = Field(
        default_factory=WaypointHeadingParam,
        serialization_alias="globalWaypointHeadingParam",
        description="Global heading parameter configuration for the waypoints."
    )
    global_turn_mode: WaypointTurnMode = Field(
        default=WaypointTurnMode.TURN_AT_POINT,
        serialization_alias="globalWaypointTurnMode",
        description="Global turn mode for the waypoints."
    )
    global_use_straight_line: int = Field(
        default=1,
        serialization_alias="globalUseStraightLine",
        description="Use straight line for the waypoints (0: No, 1: Yes)",
        ge=0, le=1
    )
    global_gimbal_pitch_mode: GimbalPitchMode = Field(
        default=GimbalPitchMode.MANUAL,
        serialization_alias="gimbalPitchMode",
        description="Global gimbal pitch mode for the waypoints."
    )
    waypoints: list[Waypoint] = Field(
        default_factory=list,
        serialization_alias="Placemark",
        description="List of waypoints in the KML file."
    )

    def to_dict(self) -> dict:
        """Convert the KML to a dictionary."""
        return self._to_legacy_dict()

    def _to_flat_dict(self) -> dict:
        """Convert the KML model into a flat WPML dictionary before file-specific grouping."""
        data = self.model_dump(by_alias=True, exclude_none=True, exclude=['waypoints'])
        data = {f"wpml:{k}": v for k, v in data.items()}
        data['Placemark'] = [wp.to_dict() for wp in self.waypoints]
        # expand list and items that have to_dict
        for key, value in data.items():
            if isinstance(value, list):
                data[key] = [item.to_dict() if hasattr(item, 'to_dict') else item for item in value]
            elif hasattr(value, 'to_dict'):
                data[key] = value.to_dict()
        return data

    def _to_legacy_dict(self) -> dict:
        data = self._to_flat_dict()
        # move attributes that are not in folder to the root
        root_data = {k: v for k, v in data.items() if k  in ATTR_NOT_IN_FOLDER}
        folder_data = {k: v for k, v in data.items() if k not in ATTR_NOT_IN_FOLDER}
        if "wpml:autoFlightSpeed" in root_data:
            folder_data["wpml:autoFlightSpeed"] = root_data["wpml:autoFlightSpeed"]
        # Add folder data under 'Folder' key
        data = {**root_data, "Folder": folder_data,}
        return data

    def to_template_dict(self) -> dict:
        """Convert the mission to DJI's planning template.kml document body."""
        data = self._to_flat_dict()
        root_data = {
            k: self._ordered_mission_config(data[k])
            if k == "wpml:missionConfig"
            else data[k]
            for k in TEMPLATE_ROOT_ATTRS
            if k in data
        }
        folder_data = {k: data[k] for k in TEMPLATE_FOLDER_ATTRS if k in data}
        folder_data["wpml:globalRTHHeight"] = max(
            self.global_height,
            float(data["wpml:missionConfig"].get("wpml:takeOffSecurityHeight", 0)),
        )
        folder_data["Placemark"] = [
            self._to_template_waypoint(wp) for wp in data.get("Placemark", [])
        ]
        return {**root_data, "Folder": folder_data}

    def to_waylines_dict(self) -> dict:
        """Convert the mission to DJI's executable waylines.wpml document body."""
        data = self._to_flat_dict()
        root_data = {
            "wpml:missionConfig": self._ordered_mission_config(
                data["wpml:missionConfig"], include_global_rth=True
            )
        }
        folder_data = {k: data[k] for k in WAYLINES_FOLDER_ATTRS if k in data}
        folder_data["wpml:autoFlightSpeed"] = data["wpml:autoFlightSpeed"]
        folder_data["Placemark"] = [self._to_executable_waypoint(wp) for wp in data.get("Placemark", [])]
        return {**root_data, "Folder": folder_data}

    def _ordered_mission_config(
        self, mission_config: dict, include_global_rth: bool = False
    ) -> dict:
        """Return required mission fields in DJI's documented element order."""
        source = dict(mission_config)
        config = {}
        for key in (
            "wpml:flyToWaylineMode",
            "wpml:finishAction",
            "wpml:exitOnRCLost",
            "wpml:executeRCLostAction",
        ):
            if key in source:
                config[key] = source[key]

        # DJI's template.kml and waylines.wpml reference samples both include
        # this element when exitOnRCLost is goContinue, despite the element
        # table describing it as conditionally required. Pilot validates the
        # sample-shaped pair, so provide the harmless hover fallback.
        config.setdefault("wpml:executeRCLostAction", "hover")

        for key in (
            "wpml:takeOffSecurityHeight",
            "wpml:refTakeOffPoint",
            "wpml:takeOffRefPointAGLHeight",
        ):
            if key in source:
                config[key] = source[key]

        config["wpml:globalTransitionalSpeed"] = self.global_speed
        if include_global_rth:
            config["wpml:globalRTHHeight"] = max(
                self.global_height,
                float(source.get("wpml:takeOffSecurityHeight", 0)),
            )

        for key in ("wpml:droneInfo", "wpml:payloadInfo"):
            if key in source:
                config[key] = source[key]

        return config

    def _to_template_waypoint(self, waypoint: dict) -> dict:
        """Translate the shared waypoint model to template.kml fields."""
        source = dict(waypoint)
        template = {}

        if "Point" in source:
            template["Point"] = source["Point"]
        template["wpml:index"] = source["wpml:index"]

        height = source.get("wpml:height", self.global_height)
        template["wpml:ellipsoidHeight"] = source.get(
            "wpml:ellipsoidHeight", height
        )
        template["wpml:height"] = height

        for key in (
            "wpml:useGlobalHeight",
            "wpml:useGlobalSpeed",
            "wpml:waypointSpeed",
            "wpml:useGlobalHeadingParam",
            "wpml:waypointHeadingParam",
            "wpml:useGlobalTurnParam",
            "wpml:waypointTurnParam",
            "wpml:gimbalPitchAngle",
            "wpml:actionGroup",
        ):
            if key in source:
                template[key] = source[key]

        turn_param = source.get("wpml:waypointTurnParam")
        turn_mode = (
            turn_param.get("wpml:waypointTurnMode")
            if turn_param
            else str(self.global_turn_mode)
        )
        if turn_mode in (
            "toPointAndStopWithContinuityCurvature",
            "toPointAndPassWithContinuityCurvature",
        ):
            template["wpml:useStraightLine"] = source.get(
                "wpml:useStraightLine", self.global_use_straight_line
            )

        return template

    def _to_executable_waypoint(self, waypoint: dict) -> dict:
        """Fill executable defaults required by waylines.wpml without mutating the template."""
        source = dict(waypoint)
        executable = {}

        if "Point" in source:
            executable["Point"] = source["Point"]

        executable["wpml:index"] = source["wpml:index"]
        executable["wpml:executeHeight"] = source.get("wpml:height", self.global_height)
        executable["wpml:waypointSpeed"] = source.get("wpml:waypointSpeed", self.global_speed)

        executable["wpml:waypointHeadingParam"] = source.get(
            "wpml:waypointHeadingParam",
            self.global_waypoint_heading_param.to_dict(),
        )

        turn_param = source.get("wpml:waypointTurnParam")
        if turn_param is None:
            turn_param = {
                "wpml:waypointTurnMode": str(self.global_turn_mode),
                "wpml:waypointTurnDampingDist": 0,
            }
        executable["wpml:waypointTurnParam"] = turn_param

        for key in (
            "wpml:gimbalPitchAngle",
            "wpml:actionGroup",
        ):
            if key in source:
                executable[key] = source[key]

        turn_mode = turn_param["wpml:waypointTurnMode"]
        if turn_mode in (
            "toPointAndStopWithContinuityCurvature",
            "toPointAndPassWithContinuityCurvature",
        ):
            executable["wpml:useStraightLine"] = source.get(
                "wpml:useStraightLine", self.global_use_straight_line
            )

        return executable

    @classmethod
    def from_dict(cls, data: dict) -> 'KML':
        """Create a KML instance from a dictionary."""
        folder_data = data.pop("Folder", {})
        merged = {**data, **folder_data}

        waypoints_data = merged.pop("Placemark", [])
        waypoints = [Waypoint.from_dict(wp) for wp in waypoints_data]

        clean_data = cls._from_wpml_dict(merged)

        for field_name, field_value in clean_data.items():
            if field_name in cls.model_fields:
                field_class = cls.model_fields[field_name].annotation
                if hasattr(field_class, 'from_dict') and isinstance(field_value, dict):
                    clean_data[field_name] = field_class.from_dict(field_value)

        return cls(**clean_data, waypoints=waypoints)
    
    def to_xml(self, pretty=True) -> str:
        """Convert the KML to an XML string."""
        return self.dict_to_xml(self.to_dict(), pretty=pretty)

    def to_template_xml(self, pretty=True) -> str:
        """Convert the KML model to DJI's template.kml XML."""
        return self.dict_to_xml(self.to_template_dict(), pretty=pretty)

    def to_waylines_xml(self, pretty=True) -> str:
        """Convert the KML model to DJI's waylines.wpml XML."""
        return self.dict_to_xml(self.to_waylines_dict(), pretty=pretty)

    @staticmethod
    def dict_to_xml(dict, pretty=True) -> str:
        xml_dict = {
            'kml': {
                "@xmlns": "http://www.opengis.net/kml/2.2",
                "@xmlns:wpml": WPML_NAMESPACE,
                "Document": dict
            }
        }
        return xmltodict.unparse(xml_dict, pretty=pretty)
    
    @classmethod
    def from_xml(cls, xml_data: str) -> 'KML':
        """Create a KML instance from an XML string."""
        data = xmltodict.parse(xml_data, force_list=('Placemark',))
        data = data.get('kml', {}).get('Document', {})
        # Handle both cases: with and without root element
        return cls.from_dict(data)
    
