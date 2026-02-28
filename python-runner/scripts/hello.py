import argparse
import json


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", type=str, default="world", help="인사할 이름")
    args = parser.parse_args()

    result = {"message": f"Hello, {args.name}!"}
    print(json.dumps(result))


if __name__ == "__main__":
    main()
