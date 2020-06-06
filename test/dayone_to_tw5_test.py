import unittest


class TestDayoneFunctions(unittest.TestCase):
    def setUp(self):
        # create valid dayone wiki
        pass

    def test_multireplace(self):
        from tw5_tools.dayone_to_tw5 import multireplace

        replace_dict = {"me": "replaced", "that": "gone"}
        test_string = "please replace me and Me, also that and That"
        expected_case_sensitive = "please replace replaced and Me, also gone and That"
        expected_case_insensitive = (
            "please replace replaced and replaced, also gone and gone"
        )
        output_case_sensitive = multireplace(
            test_string, replace_dict, ignore_case=False
        )
        output_case_insensitive = multireplace(
            test_string, replace_dict, ignore_case=True
        )
        self.assertEqual(output_case_sensitive, expected_case_sensitive)
        self.assertEqual(output_case_insensitive, expected_case_insensitive)

    def test_create_title(self):
        from tw5_tools.dayone_to_tw5 import create_title

        entry_date = "2018-07-08T22:46:53Z"
        expected = "2018-07-08"
        output = create_title(entry_date)
        self.assertEqual(output, expected)

    def clean_text(self):
        from tw5_tools.dayone_to_tw5 import clean_text

        text_1_object = ("View from AP\n\n![](dayone-moment:\/\/3453513123123213424)",)
        text_2_objects = (
            "![](dayone-moment:\/\/456241234124134123)\n\n![](dayone-moment:\/\/635245123123)\n\n![](dayone-moment:\/\/12345645778)",
        )
        expected_1 = "View from AP!"
        expected_2 = ""
        output_1 = clean_text(text_1_object)
        output_2 = clean_text(text_2_objects)
        self.assertEqual(output_1, expected_1)
        self.assertEqual(output_2, expected_2)

    def test_location_fields(self):
        from tw5_tools.dayone_to_tw5 import get_location_fields

        entry_location = {
            "location": {
                "region": {
                    "center": {"longitude": 40.0333332, "latitude": -76.626497494},
                    "radius": 75,
                },
                "localityName": "Hell",
                "country": "Norway",
                "longitude": 40.0333332,
                "administrativeArea": "Hell city",
                "placeName": "who_knows",
                "latitude": -76.626497494,
            }
        }
        output = get_location_fields(entry_location)
        self.assertEqual(output["locality"], "Hell")
        self.assertEqual(output["place"], "who_knows")
        self.assertEqual(output["country"], "Norway")
        self.assertEqual(output["longitude"], "40.0333332")
        self.assertEqual(output["latitude"], "-76.626497494")
        entry_location_missing = {
            "location": {
                "country": "Norway",
                "longitude": 40.0333332,
                "latitude": -76.626497494,
            }
        }
        output_missing = get_location_fields(entry_location_missing)
        self.assertEqual(len(output_missing), 3)

    def test_wrap_entities(self):
        from tw5_tools.dayone_to_tw5 import wrap_entities
        import spacy
        nlp = spacy.load("en_core_web_sm")
        entry_text = "Testing PersonB"
        name_expand_map = {"PersonB": "PersonB_firstname Person_B_lastname"}
        for name in name_expand_map.keys():
            name_expand_map[name] = "[[{}|{}]]".format(name, name_expand_map[name])
        expected = "Testing [[PersonB|PersonB_firstname Person_B_lastname]]"
        output = wrap_entities(entry_text, name_expand_map, nlp)
        self.assertEqual(output, expected)

    def test_link_photos(self):
        from tw5_tools.dayone_to_tw5 import link_photos

        entry_text = "This is journal entry text"
        mock_entry_no_photo = {"text": "no photo here"}
        mock_entry_1_photo = {
            "photos": [
                {
                    "cameraMake": "Apple",
                    "type": "jpeg",
                    "location": {
                        "region": {
                            "center": {
                                "longitude": 40.0333332,
                                "latitude": -76.626497494
                            },
                            "radius": 75
                        },
                        "localityName": "Hell",
                        "country": "Norway",
                        "longitude": 40.0333332,
                        "administrativeArea": "Hell city",
                        "placeName": "who_knows",
                        "latitude": -76.626497494
                    },
                    "height": 3200,
                    "md5": "4234241231313",
                    "focalLength": "4.25",
                }
            ]
        }
        mock_entry_2_photo = {
            "photos": [
                {"type": "jpeg", "height": 3200, "md5": "4234241231313",},
                {"type": "jpeg", "height": 3200, "md5": "1231245",},
            ]
        }
        expected_1_photo = """This is journal entry text

{{photos/4234241231313.jpeg}}"""
        expected_2_photo = """This is journal entry text

{{photos/4234241231313.jpeg}}
{{photos/1231245.jpeg}}"""
        output_no_photo = link_photos(entry_text, mock_entry_no_photo)
        output_1_photo = link_photos(entry_text, mock_entry_1_photo)
        output_2_photo = link_photos(entry_text, mock_entry_2_photo)
        self.assertEqual(output_no_photo, entry_text)
        self.assertEqual(output_1_photo, expected_1_photo)
        self.assertEqual(output_2_photo, expected_2_photo)

    def test_process_dayone(self):
        from tw5_tools.dayone_to_tw5 import process_dayone
        import spacy
        import json
        import os
        nlp = spacy.load("en_core_web_sm")
        process_dayone("test/day_one_mock.json", "test/test_name_expand.json", "test/tw5_generated.json", nlp)
        with open("test/tw5_expected.json") as f:
            expected = json.load(f)
        with open("test/tw5_generated.json") as g:
            outcome = json.load(g)
        self.assertEqual(outcome, expected)
        os.remove("test/tw5_generated.json")

if __name__ == "__main__":
    unittest.main()
