# Use the Amazon Linux 2 Lambda Python 3.11 base image
FROM public.ecr.aws/lambda/python:3.11

# Set working directory
WORKDIR /var/task

# Copy application code to the container
COPY lambda_function.py .
COPY generate_devotional.py .
COPY firebase_utils/ firebase_utils/

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt --target .

# Set the CMD to the handler (function name in lambda_function.py)
CMD ["lambda_function.lambda_handler"]
