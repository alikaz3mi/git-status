import unittest
from unittest.mock import patch
import os
import tempfile
import json

from utils.pydantic_advanced_settings import CustomizedSettings


class TestSettings(CustomizedSettings):
    example_setting: str = 'default_value'
    another_setting: int = 42


# Unit tests for TestSettings
class TestCustomizedSettings(unittest.TestCase):

    def test_default_settings(self):
        settings = TestSettings()
        self.assertEqual(settings.example_setting, 'default_value')
        self.assertEqual(settings.another_setting, 42)

    @patch('sys.argv', ['script_name', '--example_setting', 'cli_value'])
    def test_command_line_arguments(self):
        settings = TestSettings()
        self.assertEqual(settings.example_setting, 'cli_value')

    # ... Additional tests

    def test_incomplete_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            json.dump({'another_setting': 100}, tmp_file)
            tmp_file.close()
            with patch('settings_module.JsonConfigSettingsSource.__call__', return_value={'another_setting': 100}):
                settings = TestSettings()
                self.assertEqual(settings.example_setting, 'default_value')
                self.assertEqual(settings.another_setting, 100)
            os.remove(tmp_file.name)

    def test_environment_variable_override(self):
        with patch.dict(os.environ, {'EXAMPLE_SETTING': 'env_value'}):
            settings = TestSettings()
            self.assertEqual(settings.example_setting, 'env_value')

    def test_json_and_env_variable_combination(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            json.dump({'example_setting': 'json_value'}, tmp_file)
            tmp_file.close()
            with patch.dict(os.environ, {'ANOTHER_SETTING': '50'}):
                with patch('settings_module.JsonConfigSettingsSource.__call__',
                           return_value={'example_setting': 'json_value'}):
                    settings = TestSettings()
                    self.assertEqual(settings.example_setting, 'json_value')
                    self.assertEqual(settings.another_setting, 50)
            os.remove(tmp_file.name)

    def test_command_line_overrides_env_variable(self):
        with patch.dict(os.environ, {'EXAMPLE_SETTING': 'env_value'}):
            with patch('sys.argv', ['script_name', '--example_setting', 'cli_value']):
                settings = TestSettings()
                self.assertEqual(settings.example_setting, 'cli_value')

    def test_missing_setting_in_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            json.dump({'some_other_setting': 'value'}, tmp_file)
            tmp_file.close()
            with patch('settings_module.JsonConfigSettingsSource.__call__',
                       return_value={'some_other_setting': 'value'}):
                settings = TestSettings()
                self.assertEqual(settings.example_setting, 'default_value')
            os.remove(tmp_file.name)

    def test_invalid_type_in_json_file(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            json.dump({'another_setting': 'not_a_number'}, tmp_file)
            tmp_file.close()
            with self.assertRaises(ValueError):
                with patch('settings_module.JsonConfigSettingsSource.__call__',
                           return_value={'another_setting': 'not_a_number'}):
                    settings = TestSettings()
            os.remove(tmp_file.name)

    def test_invalid_type_in_command_line_arguments(self):
        with patch('sys.argv', ['script_name', '--another_setting', 'not_a_number']):
            with self.assertRaises(ValueError):
                settings = TestSettings()

    def test_combination_of_all_sources(self):
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as tmp_file:
            json.dump({'example_setting': 'json_value'}, tmp_file)
            tmp_file.close()
            with patch.dict(os.environ, {'ANOTHER_SETTING': '50'}):
                with patch('sys.argv', ['script_name', '--example_setting', 'cli_value']):
                    with patch('settings_module.JsonConfigSettingsSource.__call__',
                               return_value={'example_setting': 'json_value'}):
                        settings = TestSettings()
                        self.assertEqual(settings.example_setting, 'cli_value')
                        self.assertEqual(settings.another_setting, 50)
            os.remove(tmp_file.name)

    def test_no_sources_provide_value(self):
        settings = TestSettings()
        self.assertEqual(settings.example_setting, 'default_value')
        self.assertEqual(settings.another_setting, 42)

    def test_command_line_invalid_argument(self):
        with patch('sys.argv', ['script_name', '--invalid_setting', 'value']):
            with self.assertRaises(SystemExit):
                settings = TestSettings()

    def test_json_file_not_found(self):
        with patch('pathlib.Path.exists', return_value=False):
            settings = TestSettings()
            self.assertEqual(settings.example_setting, 'default_value')
            self.assertEqual(settings.another_setting, 42)

    # ... Remaining tests


if __name__ == '__main__':
    unittest.main()
