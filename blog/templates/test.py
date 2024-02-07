import urllib.request
from urllib.error import HTTPError
import re
import sys
import xml.etree.ElementTree as ET
import subprocess


class BibTexFetcher:
    def __init__(self):
        pass

    def fetch_bibtex_from_doi(self, doi):
        BASE_URL = 'http://dx.doi.org/'
        url = BASE_URL + doi
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/x-bibtex')

        try:
            with urllib.request.urlopen(req) as f:
                return f.read().decode()
        except HTTPError as e:
            if e.code == 404:
                print('DOI not found.')
            else:
                print('Service unavailable.')
            sys.exit(1)

    def fetch_bibtex_from_arxiv(self, arxiv):
        BASE_URL = 'http://export.arxiv.org/api/query?search_query=id:'
        url = BASE_URL + arxiv
        req = urllib.request.Request(url)
        req.add_header('Accept', 'application/x-bibtex')

        try:
            with urllib.request.urlopen(req) as f:
                return f.read().decode()
        except HTTPError as e:
            if e.code == 404:
                print('arXiv not found.')
            else:
                print('Service unavailable.')
            sys.exit(1)

    def getbib(self, doi=None, arxiv=None):
        if not doi and not arxiv:
            print("Please enter a DOI or a valid arXiv number!")
            sys.exit(1)
        if doi:
            bibtex = self.fetch_bibtex_from_doi(doi)
            # Define the fields you want to extract
            fields = ['title', 'url', 'DOI', 'booktitle', 'publisher', 'author', 'year', 'month', 'collection',
                      'abstract']

            # Extracting values using regular expressions
            values = {field: re.search(f'{field}={{(.*?[^\\\\])}}', bibtex).group(1) for field in fields if
                      re.search(f'{field}={{(.*?[^\\\\])}}', bibtex)}

        if arxiv:
            arxiv_xml_response = self.fetch_bibtex_from_arxiv(arxiv)
            values = self.parse_arxiv_response(arxiv_xml_response)

        return values

    def parse_arxiv_response(self, xml_response):
        root = ET.fromstring(xml_response.strip())

        entry = root.find(".//{http://www.w3.org/2005/Atom}entry")
        if entry is not None:
            title = entry.find("./{http://www.w3.org/2005/Atom}title").text.strip() if entry.find("./{http://www.w3.org/2005/Atom}title") is not None else ''
            doi_elem = entry.find(".//{http://arxiv.org/schemas/atom}doi")
            doi = doi_elem.text.strip() if doi_elem is not None else ''
            url_elem = entry.find("./{http://www.w3.org/2005/Atom}link[@title='doi']")
            url = url_elem.attrib['href'].strip() if url_elem is not None else ''
            authors = [author.find("{http://www.w3.org/2005/Atom}name").text.strip() for author in entry.findall(".//{http://www.w3.org/2005/Atom}author")]
            year = entry.find("./{http://www.w3.org/2005/Atom}published").text.split("-")[0] if entry.find("./{http://www.w3.org/2005/Atom}published") is not None else ''
            booktitle_elem = entry.find(".//{http://arxiv.org/schemas/atom}journal_ref")
            booktitle = booktitle_elem.text.strip() if booktitle_elem is not None else ''
            abstract_elem = entry.find("./{http://www.w3.org/2005/Atom}summary")
            abstract = abstract_elem.text.replace('\n', ' ').strip() if abstract_elem is not None else ''

            json_object = {
                'title': title,
                'url': url,
                'DOI': doi,
                'booktitle': booktitle,
                'publisher': 'ISCA',
                'author': ' and '.join(authors),
                'year': year,
                'collection': 'interspeech_' + year,
                'abstract': abstract
            }
            return json_object
        else:
            return None


# Example usage:
#arxiv_xml_response = fetch_bibtex_from_arxiv("2306.04306")

#result_json = parse_arxiv_response(arxiv_xml_response)
#print(result_json)

# Example usage:
#doi = '10.21437/Interspeech.2023-772'
#bibfetch = BibTexFetcher()
#print(bibfetch.getbib(arxiv="2306.04306"))
#result = bibfetch.getbib(doi=doi)
#print(result)

print(subprocess.check_output(['arxiv2bib', '0901.2880']))
