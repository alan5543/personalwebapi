# Use an official Python runtime as the base image
FROM python:3.9

# Create a non-root user
RUN useradd -m -u 1000 user
USER user
ENV PATH="/home/user/.local/bin:$PATH"

# Set working directory
WORKDIR /app

# Copy and install dependencies
COPY --chown=user requirements.txt .
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application
COPY --chown=user . /app

# Expose the required port
EXPOSE 7860

# Run the application
CMD ["python", "app.py"]