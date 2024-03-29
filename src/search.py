import os
import lucene
from java.io import File
from java.nio.file import Paths
from org.apache.lucene.store import Directory
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.document import Document
from org.apache.lucene.index import IndexReader
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.search import IndexSearcher
from org.apache.lucene.search import Query
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.queryparser.classic import QueryParser

import queryexpansion


def search_index(indexfile, querytext, top=10, qe=False, default_field="text", display_fields=["subreddit", "author", "text"]):
    lucene.initVM()

    lindex = SimpleFSDirectory(Paths.get(indexfile))
    ireader = DirectoryReader.open(lindex)
    isearcher = IndexSearcher(ireader)

    analyser = StandardAnalyzer()

    parser = QueryParser(default_field, analyser)
    query = parser.parse(querytext)

    hits = isearcher.search(query, top).scoreDocs
    docIDs = [hit.doc for hit in hits]
    print_results(isearcher, hits, display_fields)
    if len(hits) == 0:
        print("No hits!")
    elif qe:
        print("\n")
        print("Which documents were relevant to your search need? (Enter spaced list of result numbers [1-{}], e.g. 2 4 5)".format(top))
        relevantids = [docIDs[i-1] for i in [int(x) for x in input().split()]]
        nonrelevantids = [id for id in docIDs if id not in relevantids]

        print("\n\n")

        qequerytext = queryexpansion.rocchio(ireader, querytext, relevantids, nonrelevantids)
        print("Expanded search query: '{}'\n".format(qequerytext))
        qequery = parser.parse(qequerytext)
        qehits = isearcher.search(qequery, top).scoreDocs
        print_results(isearcher, qehits, display_fields)

    ireader.close()
    lindex.close()


def print_results(isearcher, hits, display_fields):
    for i in range(len(hits)):
        document = isearcher.doc(hits[i].doc)
        fieldoutput = " | ".join([str(document.get(field)) for field in display_fields])
        print("#{})\t".format(i+1) + fieldoutput + "\n")


if __name__ == '__main__':
    lucene.initVM()
    indexdir = "/home/keerthana/Downloads/project-information-retrieval-master/src/lucene.index"

    lindex = SimpleFSDirectory(Paths.get(indexdir))
    ireader = DirectoryReader.open(lindex)
    isearcher = IndexSearcher(ireader)

    analyser = StandardAnalyzer()


    parser = QueryParser(input("Enter your field :"), analyser)
    query = parser.parse(input("Enter Your SearchQuery : "))

    hits = isearcher.search(query, 10).scoreDocs
    print(hits)
    for i in range(len(hits)):
        print(i, hits[i])
        hitDoc = isearcher.doc(hits[i].doc)
        print("{} || {} || {}".format(hitDoc.get("subreddit"), hitDoc.get("id"), hitDoc.get("text")))
    if len(hits) == 0:
        print("No hits!")

    ireader.close()
    lindex.close()
