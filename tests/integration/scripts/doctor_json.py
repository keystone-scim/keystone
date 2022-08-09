#!/usr/bin/env python3

import argparse
import json
import re


def merge_parameters(template_file_path, param_file_path):
    with open(param_file_path, "r") as file:
        # The parameter file needs to be parsed in its entirety,
        # so we aren't streaming it:
        param_file = json.loads(file.read())
    existing_params = param_file.get("parameters", {})
    merged_params = {**existing_params}
    pattern = re.compile(r"parameters\('(\w+)'\)")
    with open(template_file_path, "r") as file:
        # Since the ADF pipeline's template file can be quite big,
        # it's better to avoid loading all of it into memory. Instead,
        # trading for a slightly worse big-O:
        for buff in file:
            for param_name in pattern.findall(buff):
                merged_params[param_name] = existing_params.get(param_name, {"value": "-"})
    return {
        **param_file,
        "parameters": merged_params
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Add parameters to ARM template")
    parser.add_argument("-t", "--template-file", type=str,
                        help="Path to input ARM template file")
    parser.add_argument("-p", "--param-file", type=str,
                        help="Path to input ARM parameters file")
    parser.add_argument("-o", "--output-file", type=str,
                        help="Path to source ARM template file. If empty, write to stdout", default=None)
    args = parser.parse_args()
    res = merge_parameters(
        template_file_path=args.template_file,
        param_file_path=args.param_file
    )
    if args.output_file:
        output_file = open(args.output_file, "w")
        for line in json.dumps(res, indent="\t").split("\n"):
            output_file.write(f"{line}\n")
        output_file.close()
    else:
        print(json.dumps(res, indent=4))
