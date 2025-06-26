import pytest
from flowbridge.core.field_extractor import FieldExtractor, FieldExtractionResult


class TestFieldExtractor:
    @pytest.fixture
    def extractor(self):
        return FieldExtractor()
        
    @pytest.fixture
    def sample_payload(self):
        return {
            "objectType": "alert",
            "severity": {
                "level": 5,
                "label": "critical"
            },
            "tags": ["security", "incident"],
            "metadata": {
                "source": {
                    "name": "firewall",
                    "id": None
                }
            }
        }
        
    def test_simple_field_extraction(self, extractor, sample_payload):
        result = extractor.extract_field(sample_payload, "objectType")
        assert result.success
        assert result.value == "alert"
        assert result.error_message is None
        
    def test_nested_field_extraction(self, extractor, sample_payload):
        result = extractor.extract_field(sample_payload, "severity.level")
        assert result.success
        assert result.value == 5
        
    def test_missing_field(self, extractor, sample_payload):
        result = extractor.extract_field(sample_payload, "nonexistent.field")
        assert not result.success
        assert result.value is None
        assert result.error_message is not None
        
    def test_none_value(self, extractor, sample_payload):
        result = extractor.extract_field(sample_payload, "metadata.source.id")
        assert result.success
        assert result.value is None
        
    def test_invalid_path(self, extractor, sample_payload):
        result = extractor.extract_field(sample_payload, "")
        assert not result.success
        assert "Field path must be a non-empty string" in result.error_message

    # New comprehensive tests
    def test_deep_nesting_extraction(self, extractor):
        """Test extraction from deeply nested structures."""
        deep_payload = {
            "level1": {
                "level2": {
                    "level3": {
                        "level4": {
                            "level5": {
                                "level6": "deep_value"
                            }
                        }
                    }
                }
            }
        }
        result = extractor.extract_field(deep_payload, "level1.level2.level3.level4.level5.level6")
        assert result.success
        assert result.value == "deep_value"

    def test_various_data_types(self, extractor):
        """Test extraction of different data types."""
        payload = {
            "string_val": "test_string",
            "int_val": 42,
            "float_val": 3.14,
            "bool_val": True,
            "null_val": None,
            "array_val": [1, 2, 3],
            "nested": {
                "object_val": {"key": "value"}
            }
        }
        
        # String
        result = extractor.extract_field(payload, "string_val")
        assert result.success and result.value == "test_string"
        
        # Integer
        result = extractor.extract_field(payload, "int_val")
        assert result.success and result.value == 42
        
        # Float
        result = extractor.extract_field(payload, "float_val")
        assert result.success and result.value == 3.14
        
        # Boolean
        result = extractor.extract_field(payload, "bool_val")
        assert result.success and result.value is True
        
        # None/null
        result = extractor.extract_field(payload, "null_val")
        assert result.success and result.value is None
        
        # Array
        result = extractor.extract_field(payload, "array_val")
        assert result.success and result.value == [1, 2, 3]
        
        # Nested object
        result = extractor.extract_field(payload, "nested.object_val")
        assert result.success and result.value == {"key": "value"}

    def test_malformed_field_paths(self, extractor, sample_payload):
        """Test various malformed field path scenarios."""
        # Empty path
        result = extractor.extract_field(sample_payload, "")
        assert not result.success
        assert "Field path must be a non-empty string" in result.error_message
        
        # Path with empty components
        result = extractor.extract_field(sample_payload, "severity..level")
        assert not result.success
        assert "Field path contains empty components" in result.error_message
        
        # Path starting with dot
        result = extractor.extract_field(sample_payload, ".severity.level")
        assert not result.success
        assert "Field path contains empty components" in result.error_message
        
        # Path ending with dot
        result = extractor.extract_field(sample_payload, "severity.level.")
        assert not result.success
        assert "Field path contains empty components" in result.error_message

    def test_non_dict_payload(self, extractor):
        """Test handling of non-dictionary payloads."""
        # String payload
        result = extractor.extract_field("not_a_dict", "field")
        assert not result.success
        assert "Payload must be a dictionary" in result.error_message
        
        # List payload
        result = extractor.extract_field([1, 2, 3], "field")
        assert not result.success
        assert "Payload must be a dictionary" in result.error_message
        
        # None payload
        result = extractor.extract_field(None, "field")
        assert not result.success
        assert "Payload must be a dictionary" in result.error_message

    def test_traversal_through_non_dict(self, extractor):
        """Test attempting to traverse through non-dictionary values."""
        payload = {
            "string_field": "some_string",
            "number_field": 42,
            "array_field": [1, 2, 3]
        }
        
        # Try to traverse through string
        result = extractor.extract_field(payload, "string_field.nested")
        assert not result.success
        assert "Cannot traverse through type" in result.error_message
        
        # Try to traverse through number
        result = extractor.extract_field(payload, "number_field.nested")
        assert not result.success
        assert "Cannot traverse through type" in result.error_message
        
        # Try to traverse through array
        result = extractor.extract_field(payload, "array_field.nested")
        assert not result.success
        assert "Cannot traverse through type" in result.error_message

    def test_missing_intermediate_keys(self, extractor):
        """Test extraction when intermediate keys are missing."""
        payload = {
            "level1": {
                "level2": {
                    "existing_key": "value"
                }
            }
        }
        
        # Missing key at level2
        result = extractor.extract_field(payload, "level1.level2.missing_key")
        assert not result.success
        assert "Key 'missing_key' not found" in result.error_message
        
        # Missing key at level1
        result = extractor.extract_field(payload, "level1.missing_level.key")
        assert not result.success
        assert "Key 'missing_level' not found" in result.error_message

    def test_none_intermediate_values(self, extractor):
        """Test extraction when intermediate values are None."""
        payload = {
            "level1": {
                "level2": None
            }
        }
        
        result = extractor.extract_field(payload, "level1.level2.level3")
        assert result.success
        assert result.value is None

    def test_complex_nested_structures(self, extractor):
        """Test extraction from complex real-world-like structures."""
        complex_payload = {
            "alert": {
                "id": "alert_123",
                "severity": {
                    "numeric": 5,
                    "label": "critical"
                },
                "source": {
                    "system": "firewall",
                    "details": {
                        "ip": "192.168.1.1",
                        "port": 443,
                        "protocol": "https"
                    }
                },
                "tags": ["security", "network", "critical"],
                "metadata": {
                    "created_at": "2023-01-01T00:00:00Z",
                    "updated_at": None,
                    "custom_fields": {
                        "analyst": {
                            "name": "John Doe",
                            "id": 12345
                        }
                    }
                }
            }
        }
        
        # Test various extraction paths
        assert extractor.extract_field(complex_payload, "alert.id").value == "alert_123"
        assert extractor.extract_field(complex_payload, "alert.severity.numeric").value == 5
        assert extractor.extract_field(complex_payload, "alert.source.details.ip").value == "192.168.1.1"
        assert extractor.extract_field(complex_payload, "alert.metadata.custom_fields.analyst.name").value == "John Doe"
        assert extractor.extract_field(complex_payload, "alert.metadata.updated_at").value is None

    def test_field_path_parsing_edge_cases(self, extractor):
        """Test field path parsing with various edge cases."""
        payload = {"test": "value"}
        
        # Non-string field path
        with pytest.raises(ValueError, match="Field path must be a non-empty string"):
            extractor.parse_field_path(None)
            
        with pytest.raises(ValueError, match="Field path must be a non-empty string"):
            extractor.parse_field_path(123)
            
        with pytest.raises(ValueError, match="Field path must be a non-empty string"):
            extractor.parse_field_path([])

    def test_extraction_result_properties(self, extractor, sample_payload):
        """Test that FieldExtractionResult contains all expected properties."""
        result = extractor.extract_field(sample_payload, "objectType")
        
        assert hasattr(result, 'success')
        assert hasattr(result, 'value') 
        assert hasattr(result, 'field_path')
        assert hasattr(result, 'error_message')
        
        assert result.field_path == "objectType"
        assert isinstance(result.success, bool)