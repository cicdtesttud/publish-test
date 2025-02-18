import argparse
import json
import sys

if __name__ == "__main__":
  parser = argparse.ArgumentParser(description='Generate outcome for the generation step')
  parser.add_argument('--git-sha', help="Git SHA", required=True, type=str, dest='git_sha')
  parser.add_argument('step', choices=['generation', 'testing-x86', 'testing-aarch64'])
  args = parser.parse_args()
  
  if args.step == "generation":
    job_name_prefix = "run-generation-"
    step_name = "Generate tsl"
  elif args.step == "testing-x86":
    job_name_prefix = "run-compile-and-test-x86"
    step_name = "Run Tests"
  elif args.step == "testing-aarch64":
    job_name_prefix = "run-compile-and-test-aarch64"
    step_name = "Run Tests"
  data_in = sys.stdin.read()  
  data = json.loads(data_in)
  success = True
  for job in data["jobs"]:
    job_git_sha = job.get("head_sha", "<unknown>")
    if job_git_sha == args.git_sha:
      name = job.get("name", "<unknown>")
      if name.startswith(job_name_prefix):
        for step in job["steps"]: 
          if step["name"] == step_name:
            if step["conclusion"] != "success":
              success = False
            print(f"{name}: {step['conclusion']}", file=sys.stderr)
          
  if success:
    exit(0)
  else:
    exit(1)