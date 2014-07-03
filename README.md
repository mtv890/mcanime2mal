mcanime2mal
===========

MCAnime to Myanimelist Exporter. It create a myanimelist xml export file that
you can import from the web interface.

It needs user input to resolve differences between names in mcanime and
myanimelist. Sometimes the OVAs or Specials are splitted in myanimelist so you
will have to add them manually later.

I have a lot of anime in my lists so it was too tedious to do it in one stand.
So i made it so you can do it little by little and when you stop the work is
saved and you can continue later.

For help run "./mcanime2mal.py --help":
>usage: mcanime2mal.py [-h] -n PROFILE_NUMBER -u USERNAME -p PASSWORD [-c] [-r]
>                      [-f FILENAME] [-o FILENAME] [-a TYPE|TITLE]
>
> Get mcanime anime list from a specified profile. The mcanime anime list is
> public so mcanime username and password are not required, only the profile
> number. To use myanimelist API to search your user and password are required.
> 
> optional arguments:
>  -h, --help            show this help message and exit
>  -n PROFILE_NUMBER, --number PROFILE_NUMBER
>                        get anime list from mcanime profile PROFILE_NUMBER
>  -u USERNAME, --user USERNAME
>                        myanimelist username
>  -p PASSWORD, --password PASSWORD
>                        myanimelist password
>  -c, --cache           restart from cache
>  -r, --redopassed      reescan skipped animes
>  -f FILENAME, --cachefile FILENAME
>                        cache file name. Default to mcanimelist.json on
>                        current directory
>  -o FILENAME, --outputfile FILENAME
>                        myanimelist export xml output name. default to
>                        myanimelist.xml on current directory
>  -a TYPE|TITLE, --animekey TYPE|TITLE
>                        Change a particular anime from cache.

Requirements
============

python >= 2.7 < 3 
BeatifulSoup4

