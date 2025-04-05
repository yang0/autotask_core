try:
    from autotask.nodes import Node, register_node
    from autotask.api_keys import get_api_key
except ImportError:
    from stub import Node, register_node, get_api_key

from typing import Dict, Any
import datetime
import time
import pytz


@register_node
class TimeNode(Node):
    """Node for getting current time in different formats and timezones"""
    NAME = "Current Time"
    DESCRIPTION = "Get the current time with formatting options and timezone support"

    INPUTS = {
        "format_string": {
            "label": "Format String",
            "description": "Python datetime format string (e.g. '%Y-%m-%d %H:%M:%S')",
            "type": "STRING",
            "default": "%Y-%m-%d %H:%M:%S",
            "required": False,
        },
        "timezone": {
            "label": "Timezone",
            "description": "Timezone name (e.g. 'UTC', 'America/New_York', 'Asia/Shanghai')",
            "type": "STRING",
            "default": "UTC",
            "required": False,
        }
    }

    OUTPUTS = {
        "current_time": {
            "label": "Formatted Time",
            "description": "Current time formatted according to the specified format",
            "type": "STRING",
        },
        "timestamp": {
            "label": "Unix Timestamp",
            "description": "Current time as Unix timestamp (seconds since epoch)",
            "type": "FLOAT",
        },
        "iso_format": {
            "label": "ISO Format",
            "description": "Current time in ISO 8601 format",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        """
        Get current time in the specified format and timezone
        
        Args:
            node_inputs: Dictionary containing input parameters
            workflow_logger: Logger instance for workflow execution
            
        Returns:
            Dictionary with current time in different formats
        """
        try:
            workflow_logger.info("Getting current time")
            
            # Get input parameters with defaults
            format_string = node_inputs.get("format_string", "%Y-%m-%d %H:%M:%S")
            timezone_name = node_inputs.get("timezone", "UTC")
            
            # Get current UTC time
            utc_now = datetime.datetime.now(datetime.timezone.utc)
            timestamp = utc_now.timestamp()
            
            # Convert to specified timezone if provided
            try:
                timezone = pytz.timezone(timezone_name)
                current_time = utc_now.astimezone(timezone)
                workflow_logger.debug(f"Converted time to timezone: {timezone_name}")
            except pytz.exceptions.UnknownTimeZoneError:
                workflow_logger.warning(f"Unknown timezone: {timezone_name}, using UTC")
                current_time = utc_now
                timezone_name = "UTC"
            
            # Format the time according to the format string
            try:
                formatted_time = current_time.strftime(format_string)
                workflow_logger.debug(f"Formatted time with pattern: {format_string}")
            except ValueError as e:
                workflow_logger.warning(f"Invalid format string: {format_string}, using default")
                formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")
            
            # Get ISO format
            iso_format = current_time.isoformat()
            
            workflow_logger.info(f"Current time in {timezone_name}: {formatted_time}")
            
            return {
                "success": True,
                "current_time": formatted_time,
                "timestamp": timestamp,
                "iso_format": iso_format,
                "timezone": timezone_name
            }
            
        except Exception as e:
            error_msg = f"Error getting current time: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }


@register_node
class TimeDifferenceNode(Node):
    """Node for calculating the difference between two times"""
    NAME = "Time Difference"
    DESCRIPTION = "Calculate the difference between two times or dates"

    INPUTS = {
        "start_time": {
            "label": "Start Time",
            "description": "Start time in ISO format or timestamp",
            "type": "STRING",
            "required": True,
        },
        "end_time": {
            "label": "End Time",
            "description": "End time in ISO format or timestamp (defaults to current time if not provided)",
            "type": "STRING",
            "required": False,
        },
        "unit": {
            "label": "Result Unit",
            "description": "Unit for the result (seconds, minutes, hours, days)",
            "type": "STRING",
            "default": "seconds",
            "required": False,
        }
    }

    OUTPUTS = {
        "difference": {
            "label": "Time Difference",
            "description": "Difference between the two times in the specified unit",
            "type": "FLOAT",
        },
        "formatted_difference": {
            "label": "Formatted Difference",
            "description": "Human-readable time difference",
            "type": "STRING",
        }
    }

    async def execute(self, node_inputs: Dict[str, Any], workflow_logger) -> Dict[str, Any]:
        """
        Calculate time difference between two timestamps
        
        Args:
            node_inputs: Dictionary containing input parameters
            workflow_logger: Logger instance for workflow execution
            
        Returns:
            Dictionary with time difference in different formats
        """
        try:
            workflow_logger.info("Calculating time difference")
            
            # Get input parameters
            start_time_str = node_inputs.get("start_time")
            end_time_str = node_inputs.get("end_time")
            unit = node_inputs.get("unit", "seconds").lower()
            
            # Parse start time
            start_datetime = self._parse_time_input(start_time_str, workflow_logger)
            if not start_datetime:
                return {
                    "success": False,
                    "error_message": f"Invalid start time format: {start_time_str}"
                }
            
            # Parse end time (default to current time if not provided)
            if end_time_str:
                end_datetime = self._parse_time_input(end_time_str, workflow_logger)
                if not end_datetime:
                    return {
                        "success": False,
                        "error_message": f"Invalid end time format: {end_time_str}"
                    }
            else:
                end_datetime = datetime.datetime.now(datetime.timezone.utc)
            
            # Calculate difference in seconds
            difference_seconds = (end_datetime - start_datetime).total_seconds()
            
            # Convert to requested unit
            formatted_difference = ""
            if unit == "seconds":
                difference = difference_seconds
                formatted_difference = f"{difference:.2f} seconds"
            elif unit == "minutes":
                difference = difference_seconds / 60
                formatted_difference = f"{difference:.2f} minutes"
            elif unit == "hours":
                difference = difference_seconds / 3600
                formatted_difference = f"{difference:.2f} hours"
            elif unit == "days":
                difference = difference_seconds / 86400
                formatted_difference = f"{difference:.2f} days"
            else:
                # Default to seconds if unit not recognized
                workflow_logger.warning(f"Unrecognized unit: {unit}, using seconds")
                unit = "seconds"
                difference = difference_seconds
                formatted_difference = f"{difference:.2f} seconds"
            
            workflow_logger.info(f"Time difference: {formatted_difference}")
            
            return {
                "success": True,
                "difference": difference,
                "formatted_difference": formatted_difference,
                "unit": unit
            }
            
        except Exception as e:
            error_msg = f"Error calculating time difference: {str(e)}"
            workflow_logger.error(error_msg)
            return {
                "success": False,
                "error_message": error_msg
            }
    
    def _parse_time_input(self, time_input: str, logger) -> datetime.datetime:
        """
        Parse a time input string into a datetime object
        
        Args:
            time_input: Time string in various formats
            logger: Logger instance
            
        Returns:
            datetime object or None if parsing fails
        """
        try:
            # Try parsing as timestamp (float)
            try:
                timestamp = float(time_input)
                return datetime.datetime.fromtimestamp(timestamp, tz=datetime.timezone.utc)
            except ValueError:
                # Not a timestamp, continue to other formats
                pass
            
            # Try parsing as ISO format
            try:
                return datetime.datetime.fromisoformat(time_input.replace('Z', '+00:00'))
            except ValueError:
                # Not ISO format, try other common formats
                pass
            
            # Try common formats
            for fmt in ["%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%m/%d/%Y %H:%M:%S", "%m/%d/%Y"]:
                try:
                    dt = datetime.datetime.strptime(time_input, fmt)
                    # Add UTC timezone if not present
                    if dt.tzinfo is None:
                        dt = dt.replace(tzinfo=datetime.timezone.utc)
                    return dt
                except ValueError:
                    continue
            
            # If all parsing attempts fail
            logger.error(f"Failed to parse time input: {time_input}")
            return None
            
        except Exception as e:
            logger.error(f"Error parsing time input: {str(e)}")
            return None


if __name__ == "__main__":
    # Setup basic logging
    import logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    # Test TimeNode
    print("\n1. Testing TimeNode:")
    node1 = TimeNode()
    result1 = node1.execute({}, logger)
    print(f"Current Time Result: {result1}")
    
    # Test with custom format and timezone
    print("\n2. Testing TimeNode with custom format and timezone:")
    result2 = node1.execute({
        "format_string": "%Y-%m-%d %H:%M:%S %Z",
        "timezone": "America/New_York"
    }, logger)
    print(f"Formatted Time Result: {result2}")
    
    # Test TimeDifferenceNode
    print("\n3. Testing TimeDifferenceNode:")
    node2 = TimeDifferenceNode()
    # Calculate difference between a timestamp from an hour ago and now
    one_hour_ago = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=1)
    result3 = node2.execute({
        "start_time": one_hour_ago.isoformat(),
        "unit": "minutes"
    }, logger)
    print(f"Time Difference Result: {result3}")
