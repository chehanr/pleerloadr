#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
from os.path import basename

import requests
from bs4 import BeautifulSoup, SoupStrainer
from clint.textui import progress
from tabulate import tabulate

CWD = os.getcwd()

IDX = 0
PAGE_IDX = 1
SEARCH = ''
QUALITY = 'best'
SORT = 0

MASTER_LIST = []
MAPPER = [None]


def dir_exist(path):
    """Check path, if not create it."""
    directory = os.path.dirname(path)
    if not os.path.exists(directory):
        os.makedirs(directory)


def get_src(link):
    """Get download source."""
    url = 'http://pleer.com/mobile/files_mobile/%s.mp3' % (link)
    return url


def download_track(title, artist, link):
    """Downloading the track."""
    src = get_src(link)
    path = '%s\\downloads\\' % (CWD)
    dir_exist(path)
    file_name = '%s - %s - %s' % (title, artist, basename(src))
    print('\n%s: ' % (file_name))
    if not os.path.isfile(path + file_name):
        try:
            response = requests.get(src, stream=True)
            total_length = int(
                response.headers.get('content-length', 0))
            with open('%s%s' % (path, file_name), 'wb') as file:
                for chunk in progress.bar(response.iter_content(chunk_size=1024), expected_size=(total_length / 1024) + 1):
                    if chunk:
                        file.write(chunk)
                        file.flush()
            file_on_disk = open('%s%s' % (path, file_name), 'rb')
            size_on_disk = len(file_on_disk.read())
            print('\n[DOWNLOADED] (size on disk: %s)' % (str(size_on_disk)))
        except Exception as err:
            print('\ndownload failed [ERROR: %s]' % (err))
            main()
    else:
        print('[SKIPPED] (already exists)')


def get_track(idx):
    """Handle downloads."""
    input_list = idx.split(',')
    for i in input_list:
        try:
            index = int(i.strip())
            title, artist, link = MAPPER[index]
            try:
                download_track(title, artist, link)
            except KeyboardInterrupt:
                print('\ndownload interrupted')
                continue
        except Exception as err:
            print('\nenter a valid index number [ERROR: %s]' % (err))
            continue


def fetch_results(soup):
    """Fetching elements."""
    row = []
    for li_track in soup.find_all('li', attrs={'source': 'default'}):
        track_duration_val = li_track.attrs['duration']
        # track_file_id = li_track.attrs['file_id']
        track_artist = li_track.attrs['singer']
        track_title = li_track.attrs['song']
        track_link = li_track.attrs['link']
        track_bitrate = li_track.attrs['rate']
        track_size = li_track.attrs['size']

        track_title = track_title.strip()
        track_artist = track_artist.strip()

        track_title_abr = track_title[:50] + (track_title[75:] and '..')
        track_artist_abr = track_artist[:50] + (track_artist[75:] and '..')

        track_duration_min = int(track_duration_val) / 60
        track_duration_sec = int(track_duration_val) % 60
        track_duration = '%s:%s' % (
            int(track_duration_min), str(track_duration_sec).zfill(2))

        global IDX
        IDX += 1

        row = [IDX, track_title_abr, track_artist_abr,
               track_duration, track_size, track_bitrate]

        MASTER_LIST.append(row)

        MAPPER.insert(IDX, (track_title, track_artist, track_link))

    result = tabulate(MASTER_LIST, headers=[
                      'IDX', 'title', 'artist', 'duration', 'size', 'bitrate'], tablefmt='simple')
    return result


def get_results():
    """Initial scrape."""
    base_url = 'http://pleer.net/'
    search_url = '%s%s' % (base_url, 'search')
    query = {'q': SEARCH, 'target': 'tracks', 'page': PAGE_IDX,
             'QUALITY': QUALITY, 'sort_mode': '0', 'sort_by': SORT}
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2228.0 Safari/537.36'}
    response = requests.get(search_url, headers=headers,
                            stream=True, params=query)
    strainer = SoupStrainer('div', attrs={'class': 'playlist'})

    soup = BeautifulSoup(
        response.content, 'lxml', parse_only=strainer)

    output = fetch_results(soup)
    return output


def main():
    """Main prompt."""
    global SEARCH, IDX, PAGE_IDX, SORT, QUALITY
    option = input(
        '\nsearch [s], load more [m], sort by [sb], set quality [q], download [d], exit [e]\npleerloadr > ')
    if option == 's' or option == 'search':
        SEARCH = input('\nenter song title or artist name\nsearch > ')
        if SEARCH:
            IDX = 0
            PAGE_IDX = 0
            del MASTER_LIST[:]
            output = get_results()
            print('\n' + output)
    elif option == 'm' or option == 'more':
        try:
            PAGE_IDX += 1
            output = get_results()
            print('\n' + output)
        except Exception as err:
            print('\nenter search query first [ERROR: %s]' % (err))
    elif option == 'sb' or option == 'SORT':
        input_sort = input(
            '\npopular [p], newest [n], alphabetical [a]\nsort by > ')
        if input_sort == 'p' or input_sort == 'popular':
            SORT = 0
        elif input_sort == 'n' or input_sort == 'new' or input_sort == 'newest':
            SORT = 1
        elif input_sort == 'a' or input_sort == 'alpha' or input_sort == 'alphabetical':
            SORT = 2
        print('\nsorting by: %s' % (SORT))
        del MASTER_LIST[:]
        IDX = 0
    elif option == 'q' or option == 'QUALITY':
        input_quality = input(
            '\nany [a], low [l], average [av], high [h]\nset quality > ')
        if input_quality == 'a' or input_quality == 'any':
            QUALITY = 'all'
        elif input_quality == 'l' or input_quality == 'low':
            QUALITY = 'bad'
        elif input_quality == 'av' or input_quality == 'average':
            QUALITY = 'good'
        elif input_quality == 'h' or input_quality == 'high':
            QUALITY = 'best'
        print('\nset qualty: %s' % (QUALITY))
        del MASTER_LIST[:]
        IDX = 0
    elif option == 'd' or option == 'download':
        input_download = input(
            '\nenter index number(s) seperated by \',\'\ndownload > ')
        get_track(input_download)
    elif option == 'e' or option == 'exit':
        exit()
    else:
        print('\ninput unrecognized')
    main()


if __name__ == '__main__':
    print('\npleerloadr - terminal downloader for pleer.net (by chehanr)')
    main()
