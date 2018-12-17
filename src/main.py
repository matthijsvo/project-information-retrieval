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
    print("QE enabled:\t\t{}".format(args.queryexpansion))
    if not os.path.exists(args.indexfile):
        raise OSError("No such file!")
    print("Query:\t\t\t'{}'".format(args.query))
    print("\n")

    search.search_index(args.indexfile, args.query,
                        top=args.top,
                        default_field=args.defaultfield,
                        display_fields=args.resultfields,
                        qe=args.queryexpansion)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="A small command line utility to search Linan Qiu's reddit-dataset.\n"
                                                 "This utility consists of two parts: \n"
                                                 "\t'index', which creates an index from a dataset, and\n"
                                                 "\t'search', which searches a previously created index using a query.\n"
                                                 "Be sure to read the included help functions (--help) for all available functionality.",
                                     epilog="the searchable fields are:\n\t'text', 'id', 'subreddit', 'meta',' time' and 'author'\n\n"
                                            "the displayable fields (for results) are:\n"
                                            "\t'text', 'id', 'subreddit', 'meta',' time', 'author', 'ups', 'downs', 'authorlinkkarma', 'authorkarma', 'authorisgold'",
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.set_defaults(func=lambda x: parser.print_help())

    subparsers = parser.add_subparsers(help="Use --help on the following sub-commands for more details:")

    indexparser = subparsers.add_parser("index", help="Create a new index")
    indexparser.add_argument("folder", action="store", help="Folder containing all database files")
    indexparser.add_argument("indexfile", action="store", help="Path of index file to be created")
    indexparser.set_defaults(func=option_index)

    searchparser = subparsers.add_parser("search", help="Run a search query")
    searchparser.add_argument("indexfile", action="store", help="Location of Lucene-generated index file")
    searchparser.add_argument("query", action="store", help="Your search query")
    searchparser.add_argument("-t", "--top", action="store", type=int, default=10,
                              help="(optional) Maximum amount of results to display")
    searchparser.add_argument("-df", "--defaultfield", action="store", default="text",
                              help="(optional) Default field for query, others can still be searched using one or multiple <field>:\"query\"")
    searchparser.add_argument("-rf", "--resultfields", nargs="+", action="store", default=["subreddit", "author", "text"],
                              help="(optional) List of fields to display in search results")
    searchparser.add_argument("-qe", "--queryexpansion", action='store_true', help="(optional) Enable query expansion")
    searchparser.set_defaults(func=option_search)

    args = parser.parse_args()
    args.func(args)
