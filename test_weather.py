import unittest
import sys
from weather import format_temperature, format_wind, AppSettings, CityNotFoundError, ErrorType

class TestWeatherApp(unittest.TestCase):
    
    def test_temperature_conversion(self):
        self.assertEqual(format_temperature(0, 'F'), '32°F')
        self.assertEqual(format_temperature(100, 'F'), '212°F')
        self.assertEqual(format_temperature(25, 'C'), '25°C')
    
    def test_settings_validation(self):
        settings = AppSettings(units='C')
        settings.validate()
        settings = AppSettings(units='F')
        settings.validate()
        with self.assertRaises(ValueError):
            AppSettings(units='K').validate()
    
    def test_wind_format(self):
        self.assertEqual(format_wind(5.0), '5.0 м/с')
        self.assertEqual(format_wind(3.333), '3.3 м/с')
    
    def test_error_types(self):
        err = CityNotFoundError('Moscow')
        self.assertEqual(err.error_type, ErrorType.NOT_FOUND)
        self.assertIn('Moscow', str(err))

if __name__ == '__main__':
    unittest.main()
