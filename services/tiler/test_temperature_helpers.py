import numpy as np

from services.tiler import server as srv


def test_temp_rescale_for_style_kelvin():
    assert srv._temp_rescale_for_style((180.0, 330.0), "default") == (180.0, 330.0)


def test_temp_rescale_for_style_celsius():
    lo, hi = srv._temp_rescale_for_style((180.0, 330.0), "celsius")
    assert round(lo, 2) == round(180.0 - 273.15, 2)
    assert round(hi, 2) == round(330.0 - 273.15, 2)


def test_temp_rescale_for_style_fahrenheit():
    lo, hi = srv._temp_rescale_for_style((180.0, 330.0), "fahrenheit")
    def k_to_f(k):
        return (k - 273.15) * 9 / 5 + 32
    assert round(lo, 2) == round(k_to_f(180.0), 2)
    assert round(hi, 2) == round(k_to_f(330.0), 2)


def test_convert_temperature():
    arr = np.array([180.0, 273.15, 300.0])
    c = srv._convert_temperature(arr, "celsius")
    f = srv._convert_temperature(arr, "fahrenheit")
    assert np.allclose(c, np.array([180.0 - 273.15, 0.0, 26.85]), atol=1e-6)
    assert np.allclose(f, (arr - 273.15) * 9 / 5 + 32, atol=1e-6)
    k = srv._convert_temperature(arr, "default")
    assert np.allclose(k, arr)
