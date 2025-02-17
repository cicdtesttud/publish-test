import argparse
import json
import sys

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Generate outcome for the generation step')
  parser.add_argument('--git-sha', help="Git SHA", required=True, type=str, dest='git_sha')
  args = parser.parse_args()
  
  data_in = sys.stdin.read()  
  data = json.loads(data_in)
  success = True
  for job in data["jobs"]:
    job_git_sha = job.get("head_sha", "<unknown>")
    if job_git_sha == args.git_sha:
      name = job.get("name", "<unknown>")
      if name.startswith("run-generation-"):
        for step in job["steps"]: 
          if step["name"] == "Generate tsl":
            if step["conclusion"] != "success":
              success = False
              print(f"{name} failed", file=sys.stderr)
  if success:
    print(0)
  else:
    print(1)