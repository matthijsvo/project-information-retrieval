
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
from org.apache.lucene.analysis.standard import ClassicAnalyzer
from org.apache.lucene.queryparser.classic import QueryParser


if __name__ == '__main__':
    lucene.initVM()
    indexdir = "./lucene.index"

    lindex = SimpleFSDirectory(Paths.get(indexdir))
    ireader = DirectoryReader.open(lindex)
    isearcher = IndexSearcher(ireader)

    analyser = ClassicAnalyzer()
    parser = QueryParser("text", analyser)
    query = parser.parse("hubble")

    hits = isearcher.search(query, 10).scoreDocs
    print(hits)
    for i in range(len(hits)):
        print(i, hits[i])
        hitDoc = isearcher.doc(hits[i].doc)
        print("{} || {} || {}".format(hitDoc.get("subreddit"), hitDoc.get("id"), hitDoc.get("text")))

    ireader.close()
    lindex.close()
