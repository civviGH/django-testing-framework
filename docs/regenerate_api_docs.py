import os
import sys
import subprocess
import signal
import pathlib
import json
import argparse
import time
import requests
import psutil
import re
import urllib

parser = argparse.ArgumentParser()
parser.add_argument('--force', action='store_true',
                    help='Do not ask for permission to delete an existing database. Just delete it.')
parser.add_argument('--no-setup', action='store_true',
                    help='Do not setup the demo DB. Assuming it has been setup already.')
parser.add_argument('--no-server', action='store_true',
                    help='Do not start a server. Assuming it is running already.')
args = parser.parse_args()

docs_path = os.path.dirname(os.path.realpath(__file__))
root_path = os.path.dirname(docs_path)

manage_script_path = os.path.join(root_path, "manage.py")

def regenerate_docs():
    # Execute commands
    endpoints_path = os.path.join(docs_path, "modules", "api", "endpoints")
    generated_path = os.path.join(docs_path, "modules", "api", "generated")

    def process_endpoint_description(desc, output_dir, basename):
        endpoint = desc['endpoint']
        method = desc['method']
        attributes = desc.get('attributes', {})

        with open(os.path.join(output_dir, basename + "-desc.txt"), 'w') as file:
            file.write(f"{method} {endpoint}")

        if len(attributes) > 0:
            with open(os.path.join(output_dir, basename + "-attributes.csv"), 'w') as file:
                file.write("Attribute|Type|Required|Description\n")
                for (attr_name, data) in attributes.items():
                    attr_type = data['type']
                    attr_required = 'yes' if data['required'] else 'no'
                    attr_description = data['description']
                    attr_default = data.get('default')
                    if attr_default is not None:
                        if isinstance(attr_default, str) and 'string' in attr_type:
                            attr_default = f'"{attr_default}"'
                        if isinstance(attr_default, bool):
                            attr_default = str(attr_default).lower()
                        attr_required += f' (default: ``{attr_default}``)'
                    if isinstance(attr_description, list):
                        attr_description = " ".join(attr_description)
                    file.write(f"``{attr_name}``|{attr_type}|{attr_required}|{attr_description}\n")

        examples = desc.get("examples", [])
        for example in examples:

            arguments = example.get('arguments', {})
            query_params = example.get('query_params', {})
            name = example.get('name')
            data = example.get('data')

            example_endpoint = endpoint
            for (arg_name, arg_value) in arguments.items():
                example_endpoint = example_endpoint.replace(":" + arg_name, str(arg_value))

            example_name = basename
            if name is not None:
                example_name += "-" + name

            example_server_name = "dtf.example.com"
            localhost_server_name = "127.0.0.1:8000"

            example_url = f"http://{example_server_name}/api{example_endpoint}"

            if len(query_params) > 0:
                example_url += "?" + urllib.parse.urlencode(query_params)

            def write_example_command(file_extension, line_continuation_char, force_double_quotes=False):
                with open(os.path.join(output_dir, example_name + f"-curl{file_extension}"), 'w') as file:
                    file.write(f'curl -X {method} {line_continuation_char}\n')
                    if data is not None:
                        data_lines = json.dumps(data, indent=4).splitlines()
                        for i in range(1, len(data_lines)):
                            data_lines[i] = '         ' + data_lines[i]
                            if force_double_quotes:
                                # In the PowerShell we want to replace single quotes by double quotes.
                                data_lines[i] = data_lines[i].replace('"', '""')
                        data_str = "\n".join(data_lines)
                        file.write(f'  --header "Content-Type: application/json" {line_continuation_char}\n')
                        file.write(f'  --data \'{data_str}\' {line_continuation_char}\n')
                    file.write(f'  {example_url}')

            write_example_command(".sh", "\\")
            write_example_command(".ps1", "`", force_double_quotes=True)

            url =  example_url.replace(example_server_name, localhost_server_name)
            response = requests.request(method, url, json=data, auth=('root', 'test1234'))

            if not response.ok:
                print(f"FAILED: {method} {url}")
                print(f"  data = {data}")
                print(f"Response: {response.reason}")
                print(f"  {response.text}")
            elif response.text:
                result_data = json.loads(response.text.replace(localhost_server_name, example_server_name))
                with open(os.path.join(output_dir, example_name + "-response.json"), 'w') as file:
                    file.write(json.dumps(result_data, indent=4))

    # Sort the endpoints: We want to execute the GET requests first, and the DELETE requests last.
    # This tries to make sure we do not delete any datapoint from the DB that we need in another GET request.
    group_order = {
        "GET" : 0,
        "PUT" : 1,
        "POST" : 2,
        "DELETE" : 3
    }
    def endpoint_key(item):
        basename = os.path.splitext(os.path.basename(str(item)))[0]
        m = re.search("(GET|PUT|POST|DELETE)", basename)
        if m:
            group = m.group(1)
            group = group_order[group]
        else:
            group = None
        return (group, -len(basename))

    descriptor_files = list(pathlib.Path(endpoints_path).rglob('*.json'))

    descriptor_files = sorted(descriptor_files, key=endpoint_key)

    for descriptor_file in descriptor_files:
        basename = os.path.splitext(os.path.basename(descriptor_file))[0]
        sub_path = os.path.relpath(os.path.dirname(descriptor_file), endpoints_path)

        output_dir = os.path.join(generated_path, sub_path)
        os.makedirs(output_dir, exist_ok=True)

        with open(descriptor_file) as file:
            endpoint_description = json.load(file)

        process_endpoint_description(endpoint_description, output_dir, basename)


# Initialize demo db
if not args.no_setup:
    setup_db_script_path = os.path.join(root_path, "setup-demo-db.py")

    os.system(f"{sys.executable} {setup_db_script_path}")

# Run demo server in the background
if args.no_server:
    regenerate_docs()
else:
    print("Starting server")
    env = dict(os.environ)
    env['DTF_DEFAULT_DATABASE'] = 'demo'
    with open('server_output.txt', 'w') as server_output:
        with subprocess.Popen(args=[sys.executable, "-u", manage_script_path, "runserver"], stdout=server_output, stderr=subprocess.STDOUT, cwd=root_path, env=env) as server_process:
            print(f"Started server with pid: {server_process.pid}")
            proc = psutil.Process(server_process.pid)
            time.sleep(1)
            try:
                regenerate_docs()
            finally:
                try:
                    children = proc.children(recursive=True)
                    os.kill(server_process.pid, signal.SIGTERM)
                    for child in children:
                        os.kill(child.pid, signal.SIGTERM)
                    server_process.wait(timeout=2)
                except subprocess.TimeoutExpired as err:
                    pass
