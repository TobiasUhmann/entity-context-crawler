import argparse

from os import remove
from os.path import isfile


def main():
    #
    # Parse args
    #

    parser = argparse.ArgumentParser(
        description='Crop and store context for each entity match',
        formatter_class=lambda prog: argparse.MetavarTypeHelpFormatter(prog, max_help_position=50, width=120))

    parser.add_argument('matches_db', metavar='matches-db', type=str,
                        help='path to matches DB')

    parser.add_argument('contexts_db', metavar='contexts-db', type=str,
                        help='path to contexts DB')

    default_context_size = 1
    parser.add_argument('--context-size', dest='context_size', default=default_context_size, type=int,
                        help='render sentence containing match +/- ... previous/next sentences as context'
                             ' (default: {})'.format(default_context_size))

    parser.add_argument('--crop-tokens', dest='crop_tokens', action='store_true',
                        help='crop tokens instead of sentences')

    parser.add_argument('--overwrite', dest='overwrite', action='store_true',
                        help='overwrite contexts DB if it already exists')

    args = parser.parse_args()

    #
    # Print applied config
    #

    print('Applied config:')
    print('    {:20} {}'.format('Matches DB', args.matches_db))
    print('    {:20} {}'.format('Contexts DB', args.contexts_db))
    print()
    print('    {:20} {}'.format('Context size', args.context_size))
    print('    {:20} {}'.format('Crop tokens', args.crop_tokens))
    print('    {:20} {}'.format('Overwrite', args.overwrite))
    print()

    #
    # Check for input/output files
    #

    if not isfile(args.matches_db):
        print('Matches DB not found')
        exit()

    if isfile(args.contexts_db):
        if args.overwrite:
            remove(args.contexts_db)
        else:
            print('Contexts DB already exists. Use --overwrite to overwrite it')
            exit()

    #
    # Run program
    #

    crop_contexts(args.matches_db, args.contexts_db, args.context_size, args.crop_tokens)


#
# CROP CONTEXTS
#

def crop_contexts(matches_db, contexts_db, context_size, crop_tokens):
    print('hi')


#
#
#

if __name__ == '__main__':
    main()
