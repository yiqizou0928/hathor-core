import argparse
import urllib.parse
import requests
import struct
from hathor.transaction import Transaction
from json.decoder import JSONDecodeError


def create_parser():
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', help='URL to access tx storage in case the hash was passed')
    parser.add_argument('--hash', help='Hash of tx to create a twin')
    parser.add_argument('--raw_tx', help='Raw tx to create a twin')
    parser.add_argument('--human', action='store_true', help='Print in human readable (json)')
    parser.add_argument(
        '--parents',
        action='store_true',
        help='Change the parents, so they can have different accumulated weight'
    )
    parser.add_argument('--weight', type=int, help='Weight of twin transaction')
    return parser


def execute(args):
    # Get tx you want to create a twin
    if args.url and args.hash:
        get_tx_url = urllib.parse.urljoin(args.url, '/transaction/')
        response = requests.get(get_tx_url, {b'id': bytes(args.hash, 'utf-8')})

        try:
            data = response.json()
        except JSONDecodeError as e:
            print('Error decoding transaction data')
            print(e)
            return

        tx_bytes = bytes.fromhex(data['tx']['raw'])
    elif args.raw_tx:
        tx_bytes = bytes.fromhex(args.raw_tx)
    else:
        print('The command expects raw_tx or hash and url as parameters')
        return

    try:
        # Create new tx from the twin
        twin = Transaction.create_from_struct(tx_bytes)

        assert len(twin.parents) == 2

        if args.parents:
            # If we want new parents we get the tips and select new ones
            get_tips_url = urllib.parse.urljoin(args.url, '/tips/')

            response = requests.get(get_tips_url)

            try:
                data = response.json()
            except JSONDecodeError as e:
                print('Error decoding tips')
                print(e)
                return

            parents = data[:2]
            if len(parents) == 0:
                print('No available tips to be selected as parents')
                return
            elif len(parents) == 1:
                parents = [parents[0], twin.parents[0].hex()]

            twin.parents = [bytes.fromhex(parents[0]), bytes.fromhex(parents[1])]
        else:
            # Otherwise we just change the parents position, so we can have a different hash
            twin.parents = [twin.parents[1], twin.parents[0]]

        if args.weight:
            twin.weight = args.weight

        twin.resolve()
        if args.human:
            print(twin.to_json())
        else:
            print(twin.get_struct().hex())
    except (struct.error, ValueError):
        print('Error getting transaction from bytes')
        return


def main():
    parser = create_parser()
    args = parser.parse_args()
    execute(args)
