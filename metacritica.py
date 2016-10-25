import requests
from bs4 import BeautifulSoup
import pandas as pd
import numpy as np
from datetime import datetime

def get_album_metascore(album, artist):
    return get_metascore('music', album, artist)

def get_movie_metascore(title):
    return get_metascore('movie', title)

def get_tv_metascore(title, season):
    return get_metascore('tv', title, 'season-'+str(season))

def get_game_metascore(title, system):
    return get_metascore('game', system, title)


def get_album_table(album, artist, inc_scorediff=False, inc_timeafter=False):
    return get_review_table('music', album, artist, inc_scorediff, inc_timeafter)

def get_movie_table(title, inc_scorediff=False, inc_timeafter=False):
    return get_review_table('movie', title, '', inc_scorediff, inc_timeafter)

def get_tv_table(title, season, inc_scorediff=False, inc_timeafter=False):
    return get_review_table('tv', title, 'season-'+str(season), inc_scorediff, inc_timeafter)

def get_game_table(title, system, inc_scorediff=False, inc_timeafter=False):
    return get_review_table('game', system, title, inc_scorediff, inc_timeafter)


def get_metascore(category, primary, secondary):
    meta_url = "http://www.metacritic.com/"+category+"/"+adj_name(primary)+"/"+adj_name(secondary)
    return get_metascore_url(meta_url, category)

def get_review_table(category, primary, secondary, inc_scorediff=False, inc_timeafter=False):
    meta_url = "http://www.metacritic.com/"+category+"/"+adj_name(primary)+"/"+adj_name(secondary)+"/critic-reviews"
    return get_review_table_url(meta_url, inc_scorediff, inc_timeafter)

def get_metascore_url(meta_url, category):
    r  = requests.get(meta_url, headers={'User-agent': 'Mozilla/5.0'})
    contents = BeautifulSoup(r.text, 'lxml')
    if contents.find(text="404 Page Not Found - Metacritic - Metacritic"):
        raise ValueError('['+primary + '] [' + secondary + '] not found on metacritic.com')

    rev = contents.find("div", class_="metascore_w")
    metascore = rev.find('span', {'itemprop': 'ratingValue'}).contents[0]

    rev = contents.find("div", class_="user")
    userscore = rev.contents[0]

    release_summary = contents.find("li", class_="summary_detail release")
    if release_summary is None:
        release_summary = contents.find("li", class_="summary_detail release_data")
    rel_date = release_summary.find('span', {'class', 'data'}).contents[0].replace('\n','').strip()

    if category is 'music':
        label_detail = contents.find("li", class_="product_company")
        label = label_detail.find('span', {'class', 'data'}).contents[0]

    if category is 'music':
        comp_type = 'record label'
    if category is 'game':
        comp_type = 'developer'

    return {'metascore': metascore, 'userscore': userscore, 'release date': rel_date}

def get_review_table_url(meta_url, inc_scorediff, inc_timeafter):
    r  = requests.get(meta_url, headers={'User-agent': 'Mozilla/5.0'})
    contents = BeautifulSoup(r.text, 'lxml')
    #print(contents)
    if contents.find(text="404 Page Not Found - Metacritic - Metacritic"):
        raise ValueError(meta_url + ' not found')

    if inc_scorediff:
        score = contents.find("div", class_="metascore_w")
        metascore = int(score.find('span', {'itemprop': 'ratingValue'}).contents[0])
    if inc_timeafter:
        release_summary = contents.find("li", class_="summary_detail release")
        if release_summary is None:
            release_summary = contents.find("li", class_="summary_detail release_data")
        rel_date = release_summary.find('span', {'class', 'data'}).contents[0].replace('\n','').strip()

    data = []
    reviews = contents.find_all("div", class_="review_content")

    for rev in reviews:
        row = []

        if 'user' not in rev.find("div", class_="metascore_w")["class"] and rev.find("div", class_="noscore") is None:
            pub = rev.find("a", class_="external")
            if pub is not None:
                row.append(pub.contents[0])
            else:
                row.append(rev.find("div", class_="source").contents[0])

            rev_date = rev.find("div", class_="date")

            if rev_date is not None:
                rev_date = rev_date.contents[0].rstrip()
                row.append(rev_date)
                date_found = True
            else:
                row.append(np.nan)
                date_found = False

            rev_score = int(rev.find("div", class_="metascore_w").contents[0])
            row.append(rev_score)

            row.append(rev.find("div", class_="review_body").contents[0])

            if inc_scorediff:
                row.append(rev_score - metascore)

            if inc_timeafter:
                if date_found:
                    row.append((datetime.strptime(rev_date, '%b %d, %Y') - datetime.strptime(rel_date, '%b %d, %Y')).days)
                else:
                    row.append(np.nan)

            data.append(row)

    col_names = ['Publication','Date','Score','Text']
    if inc_scorediff:
        col_names.append('Metascore Diff')
    if inc_timeafter:
        col_names.append('Days After Release')
    timeseries = pd.DataFrame(data=data, columns=col_names)
    return timeseries


def adj_name(name):
    return str.lower(name).replace(' ', '-').replace(':', '')

