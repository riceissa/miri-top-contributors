#!/usr/bin/env python3
# License: CC0

import sys
import requests
from bs4 import BeautifulSoup


# These are donors we track separately, so ignore them in this script.
IGNORED_DONORS = {
    "Open Philanthropy Project",
    "Gordon Irlam",
    "Loren Merritt",
}


def mysql_quote(x):
    """Quote the string x using MySQL quoting rules. If x is the empty string,
    return "NULL". Probably not safe against maliciously formed strings, but
    whatever; our input is fixed and from a basically trustable source."""
    if not x:
        return "NULL"
    x = x.replace("\\", "\\\\")
    x = x.replace("'", "''")
    x = x.replace("\n", "\\n")
    return "'{}'".format(x)


def sql_tuple(donor, amount, donation_date, donation_url):
    return ("(" + ",".join([
        mysql_quote(donor),  # donor
        mysql_quote("Machine Intelligence Research Institute"),  # donee
        str(amount),  # amount
        mysql_quote(donation_date),  # donation_date
        mysql_quote("year"),  # donation_date_precision
        mysql_quote("donee contributor list"),  # donation_date_basis
        mysql_quote("AI safety"),  # cause_area
        mysql_quote(donation_url),  # url
        mysql_quote(""),  # notes
    ]) + ")")


def top_donors(url):
    print("Downloading", url, file=sys.stderr)
    response = requests.get(url,
                            headers={'User-Agent': 'Mozilla/5.0 '
                                     '(X11; Linux x86_64) AppleWebKit/537.36 '
                                     '(KHTML, like Gecko) '
                                     'Chrome/63.0.3239.132 Safari/537.36'})
    soup = BeautifulSoup(response.content, "lxml")
    donors = {}
    for table in soup.find_all("table"):
        # There might be other tables on the page that aren't the top-donors
        # table, so make sure the second column of the first row has a "$" sign
        # in it.
        first_row_cols = table.find("tr").find_all("td")
        if len(first_row_cols) == 2 and "$" in first_row_cols[1].text.strip():
            for tr in table.find_all("tr"):
                cols = list(map(lambda x: x.text.strip(), tr.find_all("td")))
                donor = donor_normalized(cols[0])
                amount = cols[1].replace("$", "").replace(",", "")

                # Make sure each donor appears only once in the list
                assert donor not in donors

                donors[donor] = float(amount)

    print("Has", len(donors), "donors", file=sys.stderr)
    return donors


def donor_normalized(x):
    if x == "Johan Edstr\u0e23\u0e16m":
        return "Johan Edström"
    if x == "Marius van Voorden (via Bitcoin)":
        return "Marius van Voorden"
    if x == "Adam J. Weissman":
        return "Adam Weissman"
    return x
