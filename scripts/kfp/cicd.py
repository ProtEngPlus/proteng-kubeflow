import sys

def lint_pipeline_file(pipelineName :str):
    with open(f"cmd/kfp/{pipelineName}_pipeline.py", "r") as f:
        lines = f.readlines()
        code = ''.join(lines)
        if "use_secret_as_env" not in code:
            print(f"ERROR: use_secret_as_env not found in {pipelineName}_pipeline.py")
            sys.exit(1)