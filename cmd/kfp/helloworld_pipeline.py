from kfp import dsl, compiler
from kfp import kubernetes
import sys
from pydantic import BaseModel

class TestStruct(BaseModel):
    a: int
    b: str
    c: list
    d: dict

def my_func(t: TestStruct):
    print(t)
    return t.a

@dsl.component(
    packages_to_install=['pydantic']
)
def hello_world(name: str, arr: list, dct: dict, x: dict) -> str:
    from pydantic import BaseModel
    class TestStruct(BaseModel):
        a: int
        b: str
        c: list
        d: dict

    def my_func(t: TestStruct):
        print(t)
        return t.a
    xx = TestStruct(a=0, b="", c=[], d={})
    try:
        xx = TestStruct.model_validate(x)
    except Exception as e:
        print("ERROR: TestStruct.model_validate failed")
        print(e)
        # x = TestStruct(a=0, b="", c=[], d={})
    my_func(xx)
    import os
    print(f"test secret: {os.environ['TESTOO']}")
    print(f'Hello {name}!')
    print(f'len: {len(arr)} , arr: {arr}')
    print(f'len: {len(dct)} , dct: {dct}')
    return f'Hello {name}!'

@dsl.pipeline(
    name='Hello world pipeline',
    description='A hello world pipeline.'
)
def hello_world_pipeline(name: str, arr: list, dct: dict, x: dict) -> str:
    xx = TestStruct(a=0, b="", c=[], d={})
    try:
        xx = TestStruct.model_validate(x)
    except:
        print("ERROR: TestStruct.model_validate failed")
        # x = TestStruct(a=0, b="", c=[], d={})
    hello_world_task = hello_world(name=name, arr=arr, dct=dct, x=x)
    my_func(xx)
    kubernetes.use_secret_as_env(hello_world_task, 
                                 secret_name='kfp-secret',
                                 secret_key_to_env={"test": "TESTOO"})
    return hello_world_task.output

def compile_pipeline(path: str):
    compiler.Compiler().compile(hello_world_pipeline, path)


if __name__ == '__main__':
    path = sys.argv[1] if len(sys.argv) > 1 else 'gen/kfp/helloworld_pipeline.yaml'
    compile_pipeline(path)

    