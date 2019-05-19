import pandas as pd
import numpy as np
import math
from bs4 import BeautifulSoup #For web scraping
import requests #For scraping
import random

############################################
# FUNCTIONS FOR GETING AND CLEANING SCRIPTS
def get_season_urls(url_head, season_path):
    '''
    This tool scrapes a 'season' page for the URLs of all the 
    scripts for the episodes of that season. At time of writing,
    there are 3 seasons.
    This tool is used by the later web scraping functions to 
    find each page from which to scrape a script.
    Parameters:
    url_head (str.) The main URL for all pages.
    season_path (str.) The end of the URL for this page.

    Returns:
    season_urls (Pandas df.) Columns for url, season, episode, and title 
    of each episode in this season.
    '''

    #Complete URL for the page with the links to the scripts for the season
    season_page = url_head + season_path
    
    page = requests.get(season_page)
    soup = BeautifulSoup(page.content, 'html.parser')
    urls_raw = soup.findAll('a', class_ = 'season-episode-title')
    
    #Build a list of tuples.
    eps = [(                              #Each has:
            (url.get('href'),             #Path   
             int(url.get('href')[-5:-3]), #Season number
             int(url.get('href')[-2:]),   #Episode number
             url.get_text())              #Episode title
           ) for url in urls_raw]
    
    #Build a DataFrame from the list of tuples
    season_urls = pd.DataFrame(eps, columns = ['url', 
                                               'season', 
                                               'episode', 
                                               'title'])
    
    return season_urls

#Scrape a web page for a script.
#Return it as a string.
def get_script(url_head, script_path):
    '''
    This tool gets one script. It uses the URLs found by 
    get_season_urls. It is called repeatedly to build a document
    of all the scripts.
    Parameters:
    url_head (str.) The main URL for all pages.
    script_path (str) The end of the URL for this page.

    Returns:
    raw_script (str) Raw text of the script. Needs cleaning.
    '''
   
    #Complete URL for the page with the script
    script_page = url_head + script_path
    page = requests.get(script_page)
    soup = BeautifulSoup(page.content, 'html.parser')
    raw_script = soup.find('div', class_ = 'scrolling-script-container')
    
    return str(raw_script)

def clean(raw_script):
    '''
    This tool cleans the text of one script by splitting the string
    into lines and calling its helper functions.

    Parameters:
    raw_script (str.) The script to clean.

    Returns:
    tupled_script (dict) Season/episode tuples as key, lists of 
    dialoge strings as tuples.
    '''
    #Call remove_linebreak and remove_whitespace recursively until 
    #all line breaks and whitespaces are removed.
    cleaned_script = remove_linebreak(raw_script)
    #Split the script into a list of lines of dialogue.
    split_script = cleaned_script.split('<br/>')
    #Turn the lines into tuples to record the numbering.
    tupled_script = [(i, line.lstrip()) for i, line in enumerate(split_script)]
    return tupled_script

#Helper function for clean()
#Called recursively with remove_whitespace
def remove_linebreak(script):
    script = script.replace('\r', ' ')
    if '  ' in script:
        script = remove_whitespace(script)
    return script

#Helper function for clean()
#Called recursively with remove_linebreak
def remove_whitespace(script): 
    while '  ' in script:
        script = script.replace('  ', ' ')
    if '\r' in script:
        remove_linebreak(script)
    else:
        return script


###################################
# FUNCTIONS TO READ AND PRINT SCRIPTS
#Returns dict with all all topical lines from the given scripts
def find_lines(topics, scripts, numerals = False):
    '''
    #Builds a dictionary with season/episode keys and lists of line strings
    for lines that contained any of the given topics. Has the same structure as the 
    scripts dictionary so that find_lines can be run iteratively on a topical_scripts
    dictionary if you want.
    Step 1: Iterate over each script in the dict. Add the key for a given script to 
    the new dict with an empty list as its value.
    Step 2: For each script, iterate over each line.
    Step 3: Look for topical words by calling is_topical() on the line.
    Step 4: Add the tuple of the line to the list for that script in the new dict of scripts.
    Parameters:
    topics (list) Topics as strings to look for. Must be individual words.

    scripts (dict) Dictionary with season/episode tuples as keys and lists of number/string tuples
    as lines of dialogue.

    numerals (bool) Usually False. If True, gets passed into is_topical to look for digits.

    '''               
    topical_scripts = {key: [line for line in val if is_topical(topics, line[1], numerals)] \
                       for key, val in scripts.items()}
    
    return topical_scripts

#h
#Find and return only topical lines
def is_topical(topics, line, numerals):
    '''Helper function for find_lines. Compares a given line
    of dialogue to the list of topics and returns True upon finding
    any of them.
    Also, if 'numerals' was set to True, this function return True
    upon finding a digit in the line.
    (Allows you to look for spelled-out number words and/or digits.)
    Parameters:
    topics (list) List of words to look for in this line of dialogue.
    line (str) The line of dialogue to search.
    numerals (bool) If True, this function searches for digits.

    Returns:
    True (bool) If topic or numeral is found.

    '''
    #Look for topical words
    if any(topic in line for topic in topics):
            return True
    
    #If 'numerals' was set to True in find_lines:
    elif numerals:
        #Find and return lines of dialogue with digits in them
        #Captures numerals with commas like "125,000."
        #Split the line into individual characters 
        #and return True if a numeral is found.
        for letter in list(line):
            if letter.isdigit():
                return True
        
#Print all the the lines from a given set of scripts
def print_lines(titles, lines):
    '''
    Prints all the lines in which given topics were found. Groups
    lines by episode and shows episode title for reference.
    Parameters:
    titles (dict) Season/episode tuples as keys, title strings as values.
    lines (dict) Dictionary of season/episode tuples as keys and lists of dialogue
    strings as  values.
    '''
    for key, val in lines.items():
        if val:
            print(key)
            print(titles[key])
            [print(line) for line in val]
            print('\n')