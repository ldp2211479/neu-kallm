import json
import argparse

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--input_dir",
        help="Location of dataset, which contains json",
    )
    args = parser.parse_args()


    # load data
    with open(args.input_dir, "r") as f:
        data = json.load(f)

if __name__=="__main__":
    main()
