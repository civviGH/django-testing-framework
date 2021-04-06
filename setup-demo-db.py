import os
import sys
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('--force', action='store_true',
                    help='Do not ask for permission to delete an existing database. Just delete it.')
args = parser.parse_args()

root_path = os.path.dirname(os.path.realpath(__file__))

manage_script_path = os.path.join(root_path, "manage.py")

db_path = os.path.join(root_path, "db.sqlite3")

if os.path.exists(db_path):
    print("WARNING: found existing database at:")
    print("  {}".format(db_path))

    if args.force:
        print("Deleting file due to --force being used.")
    else:
        print("Procceding will delete all data in that file.")
        print("Are you sure you want to continue? [Y/n]")
        answer = sys.stdin.read(1)
        if answer != 'Y' and answer != 'y':
            exit(0)

    os.remove(db_path)

os.system(f"{sys.executable} {manage_script_path} migrate")
os.system(f"{sys.executable} {manage_script_path} loaddata demo-user") # Name: root PW: test1234
os.system(f"{sys.executable} {manage_script_path} loaddata demo-project")
os.system(f"{sys.executable} {manage_script_path} loaddata demo-submissions")
os.system(f"{sys.executable} {manage_script_path} loaddata demo-webhook-log")
