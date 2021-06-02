from orkestra import utils


def test_coalesce():

    dicts = [
        {
            "object": "banner",
            "country": "usa",
            "weather": "rainy",
        },
        {
            "person": "sam",
            "animal": None,
            "country": "brazil",
        },
        {
            "weather": "cloudy",
        },
    ]

    kwargs = {
        "day": "monday",
        "none": None,
        "weather": "windy",
    }

    expected = {
        "object": "banner",
        "person": "sam",
        "day": "monday",
        "country": "brazil",
        "weather": "windy",
    }

    result = utils._coalesce(*dicts, **kwargs)

    assert result == expected

    assert dicts[1] is not result
