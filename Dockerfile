# Use the AWS Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Install required system dependencies
RUN yum -y install gcc git

# Create working directory
WORKDIR /var/task

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy source code
COPY lambda_function.py ./
COPY firebase_utils/ ./firebase_utils/

# Set the entry point for Lambda
CMD ["lambda_function.lambda_handler"]
