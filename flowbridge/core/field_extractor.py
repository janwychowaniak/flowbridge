from dataclasses import dataclass
from typing import Any, List, Optional, Union
from loguru import logger


@dataclass
class FieldExtractionResult:
    """Result of field extraction from a JSON payload."""
    success: bool
    value: Any
    field_path: str
    error_message: Optional[str] = None


class FieldExtractor:
    """Extracts values from nested JSON structures using dot notation."""

    @staticmethod
    def parse_field_path(field_path: str) -> List[str]:
        """Parse a dot-notated field path into components.
        
        Args:
            field_path: Dot-notated path (e.g., "object.title")
            
        Returns:
            List of path components
            
        Raises:
            ValueError: If field path is invalid
        """
        if not field_path or not isinstance(field_path, str):
            raise ValueError("Field path must be a non-empty string")
            
        components = field_path.split('.')
        if not all(components):
            raise ValueError("Field path contains empty components")
            
        return components

    @staticmethod
    def traverse_nested_structure(
        data: Union[dict, list], 
        path_components: List[str]
    ) -> Any:
        """Traverse a nested structure following the path components.
        
        Args:
            data: The nested data structure to traverse
            path_components: List of path components to follow
            
        Returns:
            The value at the specified path
            
        Raises:
            KeyError: If a dictionary key is not found
            IndexError: If a list index is invalid
            TypeError: If traversal is impossible due to data type
        """
        current = data
        
        for component in path_components:
            if current is None:
                return None
                
            if isinstance(current, dict):
                if component not in current:
                    raise KeyError(f"Key '{component}' not found")
                current = current[component]
            else:
                raise TypeError(f"Cannot traverse through type {type(current)}")
                
        return current

    def extract_field(
        self, 
        payload: dict, 
        field_path: str
    ) -> FieldExtractionResult:
        """Extract a field value from a payload using dot notation.
        
        Args:
            payload: The JSON payload to extract from
            field_path: Dot-notated path to the desired field
            
        Returns:
            FieldExtractionResult containing the extraction outcome
        """
        try:
            path_components = self.parse_field_path(field_path)
            
            if not isinstance(payload, dict):
                return FieldExtractionResult(
                    success=False,
                    value=None,
                    field_path=field_path,
                    error_message="Payload must be a dictionary"
                )
                
            value = self.traverse_nested_structure(payload, path_components)
            
            return FieldExtractionResult(
                success=True,
                value=value,
                field_path=field_path
            )
            
        except (ValueError, KeyError, TypeError) as e:
            logger.warning(
                "Field extraction failed",
                field_path=field_path,
                error=str(e),
                error_type=type(e).__name__
            )
            return FieldExtractionResult(
                success=False,
                value=None,
                field_path=field_path,
                error_message=str(e)
            )