import os
import argparse
import indexer
import search

def option_index(args):
    """Handles command line option 'index'."""
    print("= MAKE INDEX =")
    print()
    print("Database folder:\t{}".format(args.folder))
    if not os.path.isdir(args.folder):
        raise OSError("No such directory!")
    print("Index file:\t\t{}".format(args.indexfile))

    indexer.create_index_from_folder(args.folder, args.indexfile)


def option_search(args):
    """Handles command line option 'search'."""
    print("= SEARCH =")
    print()
    print("Index file:\t\t{}".format(args.indexfile))
    if not os.path.exists(args.indexfile):
        raise OSError("No such file!")
    print("Query:\t\t\t'{}'".format(args.query))

    raise NotImplementedError


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A small command line utility to search Linan Qiu's reddit-dataset.")
    parser.set_defaults(func=lambda x: parser.print_help())

    subparsers = parser.add_subparsers(help="Use --help on the following sub-commands for more details:")

    indexparser = subparsers.add_parser("index", help="Create a new index")
    indexparser.add_argument("folder", action="store", help="Folder containing all database files")
    indexparser.add_argument("indexfile", action="store", help="Path of index file to be created")
    indexparser.set_defaults(func=option_index)

    searchparser = subparsers.add_parser("search", help="Run a search query")
    searchparser.add_argument("indexfile", action="store", help="Location of Lucene-generated index file")
    searchparser.add_argument("query", action="store", help="Your search query")
    searchparser.set_defaults(func=option_search)

    args = parser.parse_args()
    args.func(args)
