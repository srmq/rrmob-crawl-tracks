import app.trackcrawler as tc
import argparse

import datetime

#email = 'srmq@srmq.org'
#date = datetime.datetime.now()
#tc.getTracksPlayedAtDate(email, date)

actions = {
    'create' : tc.action_create,
    'dropall' : tc.action_dropall,
    'crawl' : tc.action_crawl
}


def init_argparse() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        usage="%(prog)s [ACTION] [OPTION]",
        description="Run the spotify crawler"
    )

    parser.add_argument(
        '-d', "--database-url", 
        help="Database URL", 
        action='store', type=str, nargs=1, required=True
    )

    parser.add_argument(
        '-c', "--crawl-args", 
        help="Root password for HTTP service followed by date to crawl in YYYY-MM-DD format", 
        action='store', type=str, nargs=2
    )


    parser.add_argument(
        'action', 
        help="Action to execute. One of: "  + ', '.join(list(actions.keys())), 
        action='store', type=str, nargs=1
    )

    return parser

def main():
    parser = init_argparse()
    args = parser.parse_args()

    if args.action[0] in actions:
        actions[args.action[0]](args)
    else:
        print("Unknown action. Known actions: "  + ', '.join(list(actions.keys())))

if __name__ == "__main__":
    main()