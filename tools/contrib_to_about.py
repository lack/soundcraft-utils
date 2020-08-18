#!/bin/env python3

import hashlib
import os
import re

# import subprocess

author_format = re.compile(
    r"^- \[(?P<name>[^]]+)]\(mailto:(?P<email>[^)]+)\)(?P<description>.*)"
)
link_format = re.compile(r"\[(?P<name>[^]]+)]\((?P<url>[^)]+)\)")


def parseMarkdown(line):
    author_match = author_format.match(line)
    if author_match is not None:
        author = author_match.groupdict()
        return f"{author['name']} <{author['email']}>{author['description']}"
    link_match = link_format.search(line)
    if link_match is not None:
        link = link_match.groupdict()
        return f"{link['name']} {link['url']}"
    return line.lstrip("- ")


contributors = {}
section = None
with open("CONTRIBUTORS.md") as contrib:
    for line in contrib:
        line = line.rstrip("\n")
        if line.startswith("- "):
            contributors[section].append(parseMarkdown(line))
        elif line.startswith("--") or len(line) == 0:
            next
        else:
            section = line
            contributors[section] = []

print(f"authors={contributors['Contributors']}")
print(f"artists={contributors['Artwork']}")


def write_people(dst, people_group, people_list):
    if len(people_list) == 0:
        dst.write(f"            {people_group}=[],\n")
    elif len(people_list) == 1:
        person = people_list[0]
        dst.write(f'            {people_group}=["{person}"],\n')
    else:
        dst.write(f"            {people_group}=[\n")
        for person in people_list:
            dst.write(f'                "{person}",\n')
        dst.write(f"            ],\n")


gui = "soundcraft/gui.py"
edited = f"{gui}.edited"
print(f"Editing {gui}")
with open(gui) as src, open(edited, "w") as dst:
    mode = ""
    for line in src:
        if "authors=[" in line:
            mode = "authors"
        elif "artists=[" in line:
            mode = "artists"
        if mode == "authors":
            if "]," in line:
                write_people(dst, "authors", contributors["Contributors"])
                mode = ""
        elif mode == "artists":
            if "]," in line:
                write_people(dst, "artists", contributors["Artwork"])
                mode = ""
        else:
            dst.write(line)


def file_hash(filename):
    with open(filename, "rb") as file:
        m = hashlib.sha256()
        m.update(file.read())
        d = m.digest()
        return d


hash_edited = file_hash(edited)
hash_gui = file_hash(gui)

if hash_edited == hash_gui:
    print(f"Not updating {gui} from {edited} (no changes detected)")
    os.unlink(edited)
else:
    print(f"Update {gui} from {edited} (changes detected)")
    # subprocess.run(["diff", "-u", gui, edited])
    os.rename(edited, gui)
    os.system(f"black {gui}")
