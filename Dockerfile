# Use the official slim Python 3.11.11 image from the Docker Hub
FROM python:3.11.11-slim

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container's /app directory
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container 
EXPOSE 8000 

# Set the environment variable for Flask 
ENV FLASK_APP=app.py 

# Run flask server with your desired signature 
CMD ["flask", "run", "--host=0.0.0.0", "--port=8000"]
