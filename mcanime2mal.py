#!/bin/python2
import requests
import json
import re
from bs4 import BeautifulSoup
from urlparse import urljoin
from urllib import quote
from os.path import isfile
import argparse
import unicodedata
import sys

parser = argparse.ArgumentParser(description='Get mcanime anime list from a specified profile.\
                                              The mcanime anime list is public so mcanime username\
                                              and password are not required, only the profile number.\
                                              To use myanimelist API to search your user and\
                                              password are required.')
parser.add_argument("-n", "--number", dest="profile_number", required=True,
                  help="get anime list from mcanime profile PROFILE_NUMBER", metavar="PROFILE_NUMBER")
parser.add_argument("-u", "--user", dest="user", required=True,
                  help="myanimelist username", metavar="USERNAME")
parser.add_argument("-p", "--password", dest="password", required=True,
                  help="myanimelist password", metavar="PASSWORD")
parser.add_argument("-c", "--cache", dest="cache", action='store_true',
                  help="restart from cache")
parser.add_argument("-r", "--redopassed", dest="redo_passed", action='store_true',
                  help="reescan skipped animes")
parser.add_argument("-f", "--cachefile", dest="cache_file", metavar="FILENAME", default="mcanimelist.json",
                  help="cache file name. Default to mcanimelist.json on current directory")
parser.add_argument("-o", "--outputfile", dest="output_file", metavar="FILENAME", default="myanimelist.xml",
                  help="myanimelist export xml output name. default to myanimelist.xml on current directory")
parser.add_argument("-a", "--animekey", dest="animekey", metavar="TYPE|TITLE",
                  help="Change a particular anime from cache.")

args = parser.parse_args()

# Globals

URL = 'http://www.mcanime.net/perfil/' + args.profile_number + '/lista/anime'
anime_status = {"Watching":'W',
                "Completed":'C',
                "On-Hold":'H',
                "Plan to Watch":'D',
                "Dropped":'A'}

xml_init_string = """<?xml version="1.0" encoding="UTF-8" ?>
<myanimelist>

"""
xml_end_string = """

</myanimelist>
"""

correct_type = { 'Serie': 'TV', 'OVA': 'OVA', 'Pelicula': 'Movie',
                 'Especial': 'Special', 'Web': 'Web' }

def whitespace_replace(string):
    while '  ' in string:
        string = string.replace('  ', ' ')

    return string

def find_getch():
    try:
        import termios
    except ImportError:
        # Non-POSIX. Return msvcrt's (Windows') getch.
        import msvcrt
        return msvcrt.getch

    # POSIX system. Create and return a getch that manipulates the tty.
    import sys, tty
    def _getch():
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            ch = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return ch

    return _getch

getch = find_getch()

def get_mcanime_list(animelist):
    response = requests.get(URL)
    soup = BeautifulSoup(response.content, "html.parser")
    titles = [ i.get_text(strip=True) for i in soup.select("form > .dd_row.anime_list > li.dd_title > h5 > a") ]
    faved = [ True if i.find(class_="favorite") is not None else False for i in soup.select("form > .dd_row.anime_list") ]
    punt = [ i.get_text(strip=True) for i in soup.select("form > .dd_row.anime_list > li.rating ul.unit_rating  li.current_rating") ]
    tipo = [ i.get_text(strip=True) for i in soup.select("form > .dd_row.anime_list > li.dd_title > h5 > i") ]
    current_status = []
    this_status = ''
    for i in soup.select("#content form"):
        for j in i:
            if 'La abandone' in str(j):
                this_status = 'A'
            elif 'La quiero ver' in str(j):
                this_status = 'D'
            elif 'La deje de ver temporalmente' in str(j):
                this_status = 'H'
            elif 'La estoy viendo' in str(j):
                this_status = 'W'
            elif 'La vi completa' in str(j):
                this_status = 'C'
            
            if "dd_row anime_list" in str(j):
                current_status += [this_status]
    
    # MCAnime v1.0 do not Show "watched/total" data, so i need to make request to all anime pages to bring
    # total number of chapters and i overrrided (inveted) watched number... sry about that :(
    totals = []
    print 'Bringing total episode numbers... it takes a LOT of time...'
    for i in soup.select("form > .dd_row.anime_list"):
        animeURL = 'http://www.mcanime.net' + i.find('a').get('href')
        req = requests.get(animeURL)
        anime_soup = str(BeautifulSoup(req.content, "html.parser").select("#content"))
        page = re.search(re.compile('(<b>Episodios:<\/b> )[0-9]+'), anime_soup)
        if page is not None:
            page = page.group(0).replace('<b>Episodios:</b> ','')
        else: # probabliy redirect to naruho.do
            page = re.search(re.compile('(<strong>Cantidad de Episodios:<\/strong> )[0-9]+'), anime_soup)
            if page is None: # ok, is not naruho.do, just don't tell. Overrided to 1
                page = '1'
            else:
               page = page.group(0).replace('<strong>Cantidad de Episodios:<\/strong> ','') 
        totals += [page]
        print '.'
    print "Finish bringing total episode numbers..."        

    for idx,title in enumerate(titles):
        punt[idx] = punt[idx].split('/')[0].replace('Rating: ','')
        tipo[idx] = tipo[idx].replace('(','').replace(')','')
        total = totals[idx] 
        watched = totals[idx] 

        # Completed = total
        # Dropped = Watching, Dropped or Hold On = 1
        # Not Started = 0 
        if current_status[idx] == 'C': 
            watched = total
        elif current_status[idx] == 'A':
            watched = '1'
        elif current_status[idx] == 'D':
            watched = '0'
        elif current_status[idx] == 'H':
            watched = '1'
        elif current_status[idx] == 'W':
            watched = '1'

        tipo[idx] = correct_type[tipo[idx]]
        punt = [ "" if p == "-" else p for p in punt ]
        animekey = title+'|'+tipo[idx]

        if animekey not in animelist:
            animelist[animekey]={}
        animelist[animekey]['title']= title
        animelist[animekey]['watched']= watched
        animelist[animekey]['total']= total
        animelist[animekey]['type']= tipo[idx]
        animelist[animekey]['score']= punt[idx]
        animelist[animekey]['favorite']= faved[idx]
        animelist[animekey]['status']= current_status[idx]

    cache_file = open(args.cache_file, 'w')
    cache_file.truncate()
    cache_file.write(json.dumps(animelist, sort_keys=True, indent=4, separators=(',', ': ')))

    return animelist

def get_animes(animelist):
    for animekey in sorted(animelist):
        if (("mal_anime_entry" not in animelist[animekey] and "passed" not in animelist[animekey])
            or (args.redo_passed and "passed" in animelist[animekey])):
            print (animelist[animekey]["title"] + "  favorite:" + str(animelist[animekey]["favorite"])
                    + "  score:" + animelist[animekey]["score"]
                    + "  type:" + animelist[animekey]["type"]
                    + "  progress:" + animelist[animekey]["watched"]
                    + "/" + animelist[animekey]["total"]
                    + "  status:" + animelist[animekey]["status"] + "\n")
            animelist[animekey] = get_mal_info(animelist[animekey]["title"], animelist[animekey])
            cache_file = open(args.cache_file, 'w')
            cache_file.truncate()
            cache_file.write(json.dumps(animelist, sort_keys=True, indent=4, separators=(',', ': ')))

    return animelist

def get_mal_info(title, anime_info, force_selection=False):
    title_normalized = title.encode('ascii', 'ignore')
    title_quoted = quote(title_normalized)
    response = requests.get('http://myanimelist.net/api/anime/search.xml?q='+title_quoted, auth=(args.user, args.password))
    soup = BeautifulSoup(response.content, "html.parser")
    if anime_info["type"] == 'Web':
        types = ['TV','ONA']
    else:
        types = [anime_info["type"]]
    animes = soup('entry')
    filtered_animes = [ anime for anime in animes if
                        (title_normalized.lower() == anime.title.get_text().lower()
                         and anime.type.get_text() in types)]

    if len(filtered_animes) == 1 and not force_selection:
        print "found: " + title
        if filtered_animes[0].episodes.get_text() != anime_info["total"]:
            print "warning: number of episodes not equal (" + filtered_animes[0].episodes.get_text() + " != " + anime_info["total"] + ")"
        anime_info["mal_anime_entry"] = {
                "id": filtered_animes[0].id.get_text(),
                "title": filtered_animes[0].title.get_text(),
                "type": filtered_animes[0].type.get_text()}
    else:
        selected = get_selection(animes)
        if selected == "search":
            search_title = raw_input("search for: ").decode(sys.stdin.encoding)
            anime_info = get_mal_info(search_title, anime_info, True)
            if "passed" in anime_info:
                del anime_info["passed"]
        elif selected == "pass":
            anime_info["passed"] = True
            return anime_info
        else:
            anime_info["mal_anime_entry"] = selected
            if "passed" in anime_info:
                del anime_info["passed"]
    print "----------------------------------"
    return anime_info

def get_selection(animes, start_idx=0):
    for idx in range(start_idx, min(start_idx+10,len(animes))):
        print chr(ord('0')+idx-start_idx) + ') ' + animes[idx].title.get_text() + " - " + animes[idx].episodes.get_text() + " - " + animes[idx].type.get_text()
    if start_idx > 0:
        print "b) back"
    if len(animes)-start_idx-10 > 0:
        print "n) next 10 found animes"
    print "s) write new search"
    print "p) pass"
    print "q) quit"
    ch = getch()
    sel = ord(ch)-ord('0')+start_idx
    max_sel = len(animes)%10 if start_idx+10 > len(animes) else 10
    if 0 <= sel-start_idx < max_sel: # because letters have a high ord number
        print "selected: " + ch
        return {"id": animes[sel].id.get_text(),
                "title": animes[sel].title.get_text(),
                "type": animes[sel].type.get_text()}
    elif ch == 'b':
        if start_idx > 0:
            return get_selection(animes, start_idx-10)
        else:
            print "this are the first results"
            return get_selection(animes, start_idx)
    elif ch == 'n':
        if start_idx+10 < len(animes):
            return get_selection(animes, start_idx+10)
        else:
            print "there are no more anime results"
            return get_selection(animes, start_idx)
    elif ch == 's':
        return "search"
    elif ch == 'p':
        return "pass"
    elif ch == 'q':
        print "quitting"
        quit()
    else:
        print "wrong selection"
        return get_selection(animes)

def generate_xml(animelist):
    xml_string = xml_init_string
    xml_string += """<myinfo>
		<user_name>""" + args.user + """</user_name>
		<user_export_type>1</user_export_type>
</myinfo>"""
    for animekey in animelist:
        anime_info = animelist[animekey]
        if "passed" not in anime_info and "mal_anime_entry" in anime_info:
            xml_string += """
            <anime>
              <series_animedb_id>""" + anime_info["mal_anime_entry"]["id"] + """</series_animedb_id>
              <series_title><![CDATA[""" + anime_info["mal_anime_entry"]["title"] + """]]></series_title>
              <series_type>""" + anime_info["mal_anime_entry"]["type"] + """</series_type>
              <my_watched_episodes>""" + anime_info["watched"] + """</my_watched_episodes>
              <my_start_date>0000-00-00</my_start_date>
              <my_finish_date>0000-00-00</my_finish_date>
              <my_fansub_group><![CDATA[0]]></my_fansub_group>
              <my_rated></my_rated>
              <my_score>""" + anime_info["score"] + """</my_score>
              <my_dvd></my_dvd>
              <my_storage></my_storage>
              <my_status>""" + anime_info["status"] + """</my_status>
              <my_comments><![CDATA[]]></my_comments>
              <my_times_watched>0</my_times_watched>
              <my_rewatch_value></my_rewatch_value>
              <my_downloaded_eps>0</my_downloaded_eps>
              <my_tags><![CDATA[""" + ("favorite" if anime_info["favorite"] else "") + """]]></my_tags>
              <my_rewatching>0</my_rewatching>
              <my_rewatching_ep>0</my_rewatching_ep>
              <update_on_import>1</update_on_import>
            </anime>
            """
    xml_string += xml_end_string
    xml_file = open(args.output_file, 'w')
    xml_file.truncate()
    xml_file.write(xml_string.encode("UTF-8"))

if isfile(args.cache_file):
    cache_file = open(args.cache_file, 'r')
    animelist = json.loads(cache_file.read())
else:
    animelist = {}

if not args.cache:
    animelist = get_mcanime_list(animelist)

if args.animekey != None:
    animelist[args.animekey] = get_mal_info(animelist[args.animekey]["title"], animelist[args.animekey])

animelist = get_animes(animelist)
generate_xml(animelist)
