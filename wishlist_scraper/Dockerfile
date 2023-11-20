FROM public.ecr.aws/lambda/python:3.10

# Required for lxml
RUN yum install -y gcc libpq-dev libxml2-devel libxslt-devel python3-dev 
COPY . ${LAMBDA_TASK_ROOT}
RUN pip3 install -r requirements.txt
CMD [ "lambda_function.handler" ]