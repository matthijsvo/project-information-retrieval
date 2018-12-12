import os
import csv
import lucene
from java.io import File
from org.apache.lucene.index import IndexWriterConfig, IndexWriter, FieldInfo, IndexOptions
from org.apache.lucene.document import Document, Field, FieldType, TextField, StringField, StoredField
from org.apache.lucene.store import SimpleFSDirectory
from org.apache.lucene.util import Version
from org.apache.lucene.analysis.standard import StandardAnalyzer


def create_index_from_folder(folder, index_file):
    """Lets Lucene create an index of all database files within a specified folder

    :param folder: absolute or relative path to database files
    :param index_file: absolute or relative output location for index

    Notes:
    - Does not go through database folder recursively, i.e. all files have to be at the root of the folder
    - Only CSV files are supported
    - Column headers are hardcoded and should follow:
        ID, text, Reddit ID, subreddit, meta, time, author, ups, downs, authorlinkkarma, authorkarma, authorisgold
    """
    # Set up Lucene
    print()
    print("Starting Lucene ...")
    lucene.initVM()
    index_store = SimpleFSDirectory.open(File(index_file).toPath())
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(index_store, config)

    print()
    # Go through files, add rows of each as Documents to writer
    for file in os.listdir(folder):
        if file.endswith(".csv"):
            print("Indexing {} ...".format(file), end=" ", flush=True)
            with open(os.path.join(folder, file), newline='') as db:
                reader = csv.reader(db)

                # The Reddit database seems to carry a lot of duplicate posts, so we try to skip those
                post_ids = set()
                duplicate_counter = 0


                # To store term vectors (used for query expansion) we have to use a custom fieldtype
                customfield = FieldType()
                customfield.setIndexOptions(IndexOptions.DOCS_AND_FREQS)
                customfield.setStored(True)
                customfield.setTokenized(True)
                customfield.setStoreTermVectors(True)


                # CSV files have a useless first row...
                skipfirst = True
                # ... and a useless first column. Skip both.
                for _,text,rid,subreddit,meta,time,author,ups,downs,authorlinkkarma,authorkarma,authorisgold in reader:
                    if skipfirst:
                        skipfirst = False
                        continue
                    doc = Document()

                    if rid in post_ids:
                        duplicate_counter += 1
                        continue # skip
                    else:
                        post_ids.add(rid)

                    # Tokenize, index and store
                    doc.add(Field("text", text, customfield))

                    # Index and store
                    doc.add(StringField("id", rid, Field.Store.YES))
                    doc.add(StringField("subreddit", subreddit, Field.Store.YES))
                    doc.add(StringField("meta", meta, Field.Store.YES))
                    doc.add(StringField("time", time, Field.Store.YES))
                    doc.add(StringField("author", author, Field.Store.YES))

                    # Store only
                    doc.add(StoredField("ups", ups))
                    doc.add(StoredField("downs", downs))
                    doc.add(StoredField("authorlinkkarma", authorlinkkarma))
                    doc.add(StoredField("authorkarma", authorkarma))
                    doc.add(StoredField("authorisgold", authorisgold))

                    writer.addDocument(doc)

            print("DONE!\t(Duplicate posts skipped: {})".format(duplicate_counter))

    writer.commit()
    writer.close()

    print()
    print("Finished indexing!")

