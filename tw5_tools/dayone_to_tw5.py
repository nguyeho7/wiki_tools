"""Summary

Attributes:
"""
import json
import re
import spacy
from datetime import datetime
import argparse


def multireplace(string, replacements, ignore_case=False):
    """
    https://gist.github.com/bgusach/a967e0587d6e01e889fd1d776c5f3729
    Given a string and a replacement map, it returns the replaced string.
    
    :param str string: string to execute replacements on
    :param dict replacements: replacement dictionary {value to find: value to replace}
    :param bool ignore_case: whether the match should be case insensitive
    :rtype: str
    
    Args:
        string (TYPE): Description
        replacements (TYPE): Description
        ignore_case (bool, optional): Description
    
    Returns:
        TYPE: Description
    
    """
    # If case insensitive, we need to normalize the old string so that later a replacement
    # can be found. For instance with {"HEY": "lol"} we should match and find a replacement for "hey",
    # "HEY", "hEy", etc.
    if ignore_case:

        def normalize_old(s):
            """Summary
            
            Args:
                s (TYPE): Description
            
            Returns:
                TYPE: Description
            """
            return s.lower()

        re_mode = re.IGNORECASE
    else:

        def normalize_old(s):
            """Summary
            
            Args:
                s (TYPE): Description
            
            Returns:
                TYPE: Description
            """
            return s

        re_mode = 0

    replacements = {normalize_old(key): val for key, val in replacements.items()}
    # Place longer ones first to keep shorter substrings from matching where the longer ones should take place
    # For instance given the replacements {'ab': 'AB', 'abc': 'ABC'} against the string 'hey abc', it should produce
    # 'hey ABC' and not 'hey ABc'
    rep_sorted = sorted(replacements, key=len, reverse=True)
    rep_escaped = map(re.escape, rep_sorted)

    # Create a big OR regex that matches any of the substrings to replace
    pattern = re.compile("|".join(rep_escaped), re_mode)
    # For each match, look up the new string in the replacements, being the key the normalized old string
    return pattern.sub(
        lambda match: replacements[normalize_old(match.group(0))], string
    )


def create_title(entry_creationDate):
    """Summary
        Parse date to create a suitable TW5 entry title
    Args:
        entry_creationDate (str): Description
    
    Returns:
        str: Journal title
    """
    date = datetime.strptime(entry_creationDate, "%Y-%m-%dT%H:%M:%SZ")
    title = date.strftime("%Y-%m-%d")
    return title


def clean_text(entry_text):
    """Summary
    
    dayOne adds images and other objects with the following annotation:
        ![](dayone-moment.objectName)
        We add images in separate step, so we just remove them all
    
    Args:
        entry_text (TYPE): Description
    
    Returns:
        str: clean journal entry
    """
    entry_text = re.sub("!\[\]\(dayone-moment.*\)", "", entry_text)
    entry_text = entry_text.replace("\n", "")
    return entry_text.replace("\\", "")


def wrap_entities(entry_text, name_expand_map, nlp):
    """Summary
    Takes entities in a journal entry and wraps them in [[]]
    to create a Tiddler link. 
    
    uses spacy to extract additional links using a statistical tagger
    might have many false positives, and works only for english
    
    Args:
        entry_text (str): Journal text entry
        name_expand_map (dict): Mapping {'name': 'full_name'} 
        nlp (nlp): Spacy model object
    
    Returns:
        str: original text with names replacedd
    """
    doc = nlp(entry_text)
    names = [x.text for x in doc.ents if x.label_ == "PERSON"]
    tmp_name_expand_map = {}
    for name in set(names):
        if name in name_expand_map:
            continue
        tmp_name_expand_map[name] = "[[{}]]".format(name)
    if len(tmp_name_expand_map) > 0:
        entry_text = multireplace(entry_text, tmp_name_expand_map)

    entry_text = multireplace(entry_text, name_expand_map, ignore_case=True)
    return entry_text


def get_location_fields(entry):
    """Summary
    
    Args:
        entry (dict): DayOne entry dict
    
    Returns:
        TYPE: Description
    """
    result = {}
    if "location" in entry:
        result["country"] = entry["location"]["country"].replace(" ", "_")
        if "localityName" in entry["location"]:
            result["locality"] = entry["location"]["localityName"].replace(" ", "_")
        if "placeName" in entry["location"]:
            result["place"] = entry["location"]["placeName"].replace(" ", "_")
        if "latitude" in entry["location"]:
            result["latitude"] = str(entry["location"]["latitude"])
        if "longitude" in entry["location"]:
            result["longitude"] = str(entry["location"]["longitude"])
    return result


def link_photos(entry_text, entry):
    """Summary
    
    Args:
        entry_text (str): Journal text entry
        entry (dict): DayOne entry dict
    
    Returns:
        TYPE: journal text entry with inserted image links
    """
    if "photos" not in entry:
        return entry_text
    photo_list = []
    for photo in entry["photos"]:
        photo_list.append(
            "{{" + "photos/{}.{}".format(photo["md5"], photo["type"]) + "}}"
        )
    return entry_text + "\n\n" + "\n".join(photo_list)


def process_dayone(filename, name_expand_map_filename, output, nlp):
    """Summary
    
    Args:
        filename (TYPE): Description
        name_expand_map_filename (TYPE): Description
        output (TYPE): Description
        nlp (nlp): Spacy model object
    """
    result_list = []
    with open(filename) as f:
        json_dict = json.load(f)
    with open(name_expand_map_filename) as g:
        name_expand_map = json.load(g)
    for name in name_expand_map.keys():
        name_expand_map[name] = "[[{}|{}]]".format(name, name_expand_map[name])
    counter = 0
    for entry in json_dict["entries"]:
        if counter % 100 == 0:
            print(counter)
        counter += 1
        text = clean_text(entry["text"])
        text = wrap_entities(text, name_expand_map, nlp)
        text = link_photos(text, entry)
        title = create_title(entry["creationDate"])
        fields = get_location_fields(entry)
        tw5_dict = {
            "title": title,
            "tags": "journal",
            "text": text,
            "created": title,
        }
        tw5_dict.update(fields)
        result_list.append(tw5_dict)
    with open(output, "w") as f:
        json.dump(result_list, f)


def main():
    nlp = spacy.load("en_core_web_md")
    parser = argparse.ArgumentParser()
    parser.add_argument("input_filename", help="DayOne json file")
    parser.add_argument("name_expand", help="Name expansion name dictionary")
    parser.add_argument("output_filename", help="TW5 tid output name")
    args = parser.parse_args()
    process_dayone(args.input_filename, args.name_expand, args.output_filename, nlp)


if __name__ == "__main__":
    main()
