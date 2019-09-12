

## Test lambda locally with sam cli

sample file://env.json
```json
{
  "ExternalApiExternalApiHandlerAF86094E": {
    "REDIS_ADDRESS": "192.168.1.205",
    "REDIS_PORT": "6379"
  }
}
```

```shell script
# generate cloudformation template for sam debugging
cdk synth --no-staging > template.yaml
# generate test event (apigateway in this case)
am local generate-event apigateway aws-proxy > apigateway_event.json
# using lambda identifier from template.lamda, run lambda locally
# use a file (env.json below) to specify any required environment variables (e.g. lambda table name)
sam local invoke ExternalApiHandler7E50D66D --event ./apigateway_event.json  --env-vars env.json
```

start a redis server

local in this case - could also run one in a docker container

`$ redis-server --protected-mode no`

# stack operations

## deploy stack

### bootstrap cdk resources (staging bucket, etc) once
`cdk bootstrap`

### list defined stacks in the app - can have stacks defined across multiple accounts, regions, etc 
`cdk ls`

### deploy stack
`cdk deploy` 

## destroy stack

`cdk destroy`

# Test deployed stack

## invoke deployed lambda
```shell script
$ aws lambda invoke \
  --region us-east-1 \
  --function-name api-poc-mfrasier-ExternalApiHandler7E50D66D-LDEJZM1WSHCB \
  --payload file://apigateway_event.json \
  --log Tail \
  lambda.out
```
The log is base64-encoded in case you need to view it.

Output from lambda is in `lambda.out` 

## external api server

```
$ curl https://e3ryyap5mf.execute-api.us-east-1.amazonaws.com/prod/survey/1/interview/1/attachment

{"data": {"data": "something"}, "quota": 5, "status_code": 200, "message": ["Hello, CDK!  You have hit /survey/1/interview/1/attachment\n"]}
```

```bash
$ curl https://e3ryyap5mf.execute-api.us-east-1.amazonaws.com/prod//list_keys

{"keys": [{"name": "survey:interview:attachment:none", "value": "4", "ttl": 57}, {"name": "survey:interview:none", "value": "9", "ttl": 57}, {"name": "survey:none", "value": "19", "ttl": 57}]}
```

## Information generated by cdk init 
# Welcome to your CDK Python project!

This is a blank project for Python development with CDK.

The `cdk.json` file tells the CDK Toolkit how to execute your app.

This project is set up like a standard Python project.  The initialization
process also creates a virtualenv within this project, stored under the .env
directory.  To create the virtualenv it assumes that there is a `python3`
(or `python` for Windows) executable in your path with access to the `venv`
package. If for any reason the automatic creation of the virtualenv fails,
you can create the virtualenv manually.

To manually create a virtualenv on MacOS and Linux:

```
$ python3 -m venv .env
```

After the init process completes and the virtualenv is created, you can use the following
step to activate your virtualenv.

```
$ source .env/bin/activate
```

If you are a Windows platform, you would activate the virtualenv like this:

```
% .env\Scripts\activate.bat
```

Once the virtualenv is activated, you can install the required dependencies.

```
$ pip install -r requirements.txt
```

At this point you can now synthesize the CloudFormation template for this code.

```
$ cdk synth
```

To add additional dependencies, for example other CDK libraries, just add
them to your `setup.py` file and rerun the `pip install -r requirements.txt`
command.

# Useful commands

 * `cdk ls`          list all stacks in the app
 * `cdk synth`       emits the synthesized CloudFormation template
 * `cdk deploy`      deploy this stack to your default AWS account/region
 * `cdk diff`        compare deployed stack with current state
 * `cdk docs`        open CDK documentation

Enjoy!
