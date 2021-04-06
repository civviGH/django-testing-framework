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
        name = desc.get('name')
        endpoint = desc['endpoint']
        endpoint_args = desc.get('kwargs', {})
        method = desc['method']
        data = desc.get('data')

        example_endpoint = endpoint
        for (arg_name, arg_value) in endpoint_args.items():
            example_endpoint = example_endpoint.replace(":" + arg_name, arg_value)

        if name is not None:
            basename += "-" + name

        with open(os.path.join(output_dir, basename + "-desc.txt"), 'w') as file:
            file.write(f"{method} {endpoint}")

        with open(os.path.join(output_dir, basename + "-curl.sh"), 'w') as file:
            file.write(f'curl -X {method} \\\n')
            if data is not None:
                data_lines = json.dumps(data, indent=4).splitlines()
                for i in range(1, len(data_lines)):
                    data_lines[i] = '         ' + data_lines[i]
                data_str = "\n".join(data_lines)
                file.write(f'  --header "Content-Type: application/json" \\\n')
                file.write(f'  --data \'{data_str}\' \\\n')
            file.write(f'  http://dtf.example.com/api{example_endpoint}')

        url = f"http://127.0.0.1:8000/api{example_endpoint}"
        response = requests.request(method, url, json=data)

        if not response.ok:
            print(f"FAILED: {method} {url}")
            print(f"  data = {data}")
            print(f"Response: {response.reason}")
            print(f"  {response.text}")
        elif response.text:
            result_data = json.loads(response.text.replace("127.0.0.1:8000", "dtf.example.com"))
            with open(os.path.join(output_dir, basename + "-response.json"), 'w') as file:
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

    endpoint_files = list(pathlib.Path(endpoints_path).rglob('*.json'))

    endpoint_files = sorted(endpoint_files, key=endpoint_key)

    for endpoint_file in endpoint_files:
        basename = os.path.splitext(os.path.basename(endpoint_file))[0]
        sub_path = os.path.relpath(os.path.dirname(endpoint_file), endpoints_path)

        output_dir = os.path.join(generated_path, sub_path)
        os.makedirs(output_dir, exist_ok=True)

        with open(endpoint_file) as file:
            endpoint_descriptions = json.load(file)

        for endpoint_description in endpoint_descriptions:
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
